from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.app.core.config import get_settings
from backend.app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from backend.app.db.models import PasswordResetTokenRecord, UserRecord
from backend.app.models.user import Perfil, StatusCadastro


def _seed_user(
    db_session,
    *,
    nome_completo: str,
    email: str,
    username: str,
    perfil: Perfil,
    status: StatusCadastro,
    ativo: bool,
    senha: str = "SenhaPadrao@123",
    matricula: str | None = None,
    failed_login_attempts: int = 0,
    blocked_until: datetime | None = None,
) -> UserRecord:
    user = UserRecord(
        id=str(uuid4()),
        nome_completo=nome_completo,
        email=email,
        username=username,
        senha_hash=hash_password(senha),
        perfil=perfil,
        matricula=matricula,
        status=status,
        failed_login_attempts=failed_login_attempts,
        blocked_until=blocked_until,
        ativo=ativo,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _build_bearer_token(*, user_id: str, perfil: Perfil, expires_delta: timedelta) -> str:
    settings = get_settings()
    return create_access_token(
        payload={
            "user_id": user_id,
            "perfil": perfil.value,
        },
        secret_key=settings.jwt_secret,
        expires_delta=expires_delta,
        algorithm=settings.jwt_algorithm,
    )


def _seed_password_reset_token(
    db_session,
    *,
    user_id: str,
    token: str | None = None,
    expires_at: datetime | None = None,
    usado: bool = False,
) -> PasswordResetTokenRecord:
    reset_token = PasswordResetTokenRecord(
        token=token or str(uuid4()),
        user_id=user_id,
        expira_em=(
            expires_at or datetime.now(UTC) + timedelta(hours=get_settings().password_reset_token_ttl_hours)
        ).replace(tzinfo=None),
        usado=usado,
    )
    db_session.add(reset_token)
    db_session.commit()
    db_session.refresh(reset_token)
    return reset_token


@pytest.mark.parametrize(
    ("perfil", "matricula"),
    [
        (Perfil.COORDENADOR, None),
        (Perfil.ALUNO, "2023123456"),
        (Perfil.ORIENTADOR, None),
    ],
)
def test_login_returns_jwt_for_active_user_profiles(client, db_session, caplog, perfil: Perfil, matricula: str | None) -> None:
    user = _seed_user(
        db_session,
        nome_completo=f"Usuario {perfil.value}",
        email=f"{perfil.value.lower()}@icomp.ufam.edu.br",
        username=f"{perfil.value.lower()}.teste",
        perfil=perfil,
        status=StatusCadastro.ATIVO,
        ativo=True,
        senha="SenhaLogin@123",
        matricula=matricula,
    )

    with caplog.at_level(logging.INFO, logger="backend.audit"):
        response = client.post(
            "/auth/login",
            json={
                "email": user.email,
                "senha": "SenhaLogin@123",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["id"] == user.id
    assert body["user"]["perfil"] == perfil.value
    assert body["user"]["nome_completo"] == user.nome_completo

    token_payload = decode_access_token(
        token=body["access_token"],
        secret_key=get_settings().jwt_secret,
        algorithm=get_settings().jwt_algorithm,
    )
    assert token_payload["user_id"] == user.id
    assert token_payload["perfil"] == perfil.value
    assert token_payload["exp"] > int(datetime.now(UTC).timestamp())

    assert "action=LOGIN_SUCCESS" in caplog.text
    assert f"user_id={user.id}" in caplog.text


def test_login_returns_generic_error_and_tracks_attempts_for_invalid_password(client, db_session, caplog) -> None:
    user = _seed_user(
        db_session,
        nome_completo="Aluno Ativo",
        email="aluno.ativo@icomp.ufam.edu.br",
        username="aluno.ativo",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        senha="SenhaCorreta@123",
        matricula="2023123001",
    )

    with caplog.at_level(logging.INFO, logger="backend.audit"):
        response = client.post(
            "/auth/login",
            json={
                "email": user.email,
                "senha": "SenhaErrada@123",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais invalidas."

    db_session.refresh(user)
    assert user.failed_login_attempts == 1
    assert user.blocked_until is None
    assert "action=LOGIN_FAILED" in caplog.text
    assert "attempts=1" in caplog.text


def test_login_blocks_account_after_five_failures_and_sixth_attempt_returns_locked(client, db_session, caplog) -> None:
    user = _seed_user(
        db_session,
        nome_completo="Orientador Ativo",
        email="orientador@icomp.ufam.edu.br",
        username="orientador.ativo",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
        senha="SenhaCerta@123",
    )

    with caplog.at_level(logging.INFO, logger="backend.audit"):
        for _ in range(5):
            response = client.post(
                "/auth/login",
                json={
                    "email": user.email,
                    "senha": "SenhaErrada@123",
                },
            )
            assert response.status_code == 401
            assert response.json()["detail"] == "Credenciais invalidas."

        db_session.refresh(user)
        assert user.failed_login_attempts == 5
        assert user.blocked_until is not None

        locked_response = client.post(
            "/auth/login",
            json={
                "email": user.email,
                "senha": "SenhaCerta@123",
            },
        )

    assert locked_response.status_code == 423
    assert locked_response.json()["detail"] == "Conta temporariamente bloqueada. Tente novamente em 15 minutos."
    assert "action=LOGIN_BLOCKED" in caplog.text


def test_login_allows_access_again_after_block_expiration(client, db_session) -> None:
    user = _seed_user(
        db_session,
        nome_completo="Coordenador Liberado",
        email="coordenador.liberado@icomp.ufam.edu.br",
        username="coordenador.liberado",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
        senha="SenhaCerta@123",
        failed_login_attempts=5,
        blocked_until=(datetime.now(UTC) - timedelta(minutes=16)).replace(tzinfo=None),
    )

    response = client.post(
        "/auth/login",
        json={
            "email": user.email,
            "senha": "SenhaCerta@123",
        },
    )

    assert response.status_code == 200
    db_session.refresh(user)
    assert user.failed_login_attempts == 0
    assert user.blocked_until is None


def test_login_denies_pending_user_with_clear_message(client, db_session, caplog) -> None:
    user = _seed_user(
        db_session,
        nome_completo="Aluno Pendente",
        email="aluno.pendente@icomp.ufam.edu.br",
        username="aluno.pendente",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.PENDENTE,
        ativo=False,
        senha="SenhaAluno@123",
        matricula="2023123999",
    )

    with caplog.at_level(logging.INFO, logger="backend.audit"):
        response = client.post(
            "/auth/login",
            json={
                "email": user.email,
                "senha": "SenhaAluno@123",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Seu cadastro ainda esta em analise. Aguarde aprovacao."
    assert "action=LOGIN_DENIED" in caplog.text
    assert "reason=PENDENTE" in caplog.text


def test_request_password_reset_returns_generic_message_and_stores_token_for_known_email(
    client,
    db_session,
    email_service,
) -> None:
    user = _seed_user(
        db_session,
        nome_completo="Aluno Reset",
        email="reset@icomp.ufam.edu.br",
        username="aluno.reset",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        senha="SenhaAntiga@123",
        matricula="2023123555",
    )

    response = client.post(
        "/auth/solicitar-reset",
        json={"email": user.email},
    )

    assert response.status_code == 200
    assert response.json()["mensagem"] == "Se o e-mail estiver cadastrado, voce recebera as instrucoes."

    stored_token = db_session.query(PasswordResetTokenRecord).filter_by(user_id=user.id).one()
    assert stored_token.usado is False
    assert stored_token.expira_em.replace(tzinfo=UTC) > datetime.now(UTC)

    assert email_service.reset_calls == [
        {
            "to_email": user.email,
            "full_name": user.nome_completo,
            "reset_link": f"{get_settings().frontend_url}/auth/redefinir-senha?token={stored_token.token}",
        }
    ]


def test_request_password_reset_returns_same_generic_message_for_unknown_email(client, db_session, email_service) -> None:
    response = client.post(
        "/auth/solicitar-reset",
        json={"email": "nao.existe@icomp.ufam.edu.br"},
    )

    assert response.status_code == 200
    assert response.json()["mensagem"] == "Se o e-mail estiver cadastrado, voce recebera as instrucoes."
    assert db_session.query(PasswordResetTokenRecord).count() == 0
    assert email_service.reset_calls == []


def test_confirm_password_reset_updates_password_marks_token_used_and_logs_audit(client, db_session, caplog) -> None:
    user = _seed_user(
        db_session,
        nome_completo="Orientador Reset",
        email="orientador.reset@icomp.ufam.edu.br",
        username="orientador.reset",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
        senha="SenhaAntiga@123",
        failed_login_attempts=3,
        blocked_until=(datetime.now(UTC) + timedelta(minutes=10)).replace(tzinfo=None),
    )
    reset_token = _seed_password_reset_token(db_session, user_id=user.id)

    with caplog.at_level(logging.INFO, logger="backend.audit"):
        response = client.post(
            "/auth/confirmar-reset",
            json={
                "token": reset_token.token,
                "nova_senha": "SenhaNova@456",
            },
        )

    assert response.status_code == 200
    assert response.json()["mensagem"] == "Senha redefinida com sucesso."

    db_session.refresh(user)
    db_session.refresh(reset_token)
    assert verify_password("SenhaNova@456", user.senha_hash) is True
    assert verify_password("SenhaAntiga@123", user.senha_hash) is False
    assert user.failed_login_attempts == 0
    assert user.blocked_until is None
    assert reset_token.usado is True
    assert "action=RESET_SENHA" in caplog.text
    assert f"user_id={user.id}" in caplog.text

    old_password_response = client.post(
        "/auth/login",
        json={
            "email": user.email,
            "senha": "SenhaAntiga@123",
        },
    )
    assert old_password_response.status_code == 401
    assert old_password_response.json()["detail"] == "Credenciais invalidas."

    new_password_response = client.post(
        "/auth/login",
        json={
            "email": user.email,
            "senha": "SenhaNova@456",
        },
    )
    assert new_password_response.status_code == 200


def test_confirm_password_reset_rejects_reused_token(client, db_session) -> None:
    user = _seed_user(
        db_session,
        nome_completo="Aluno Reuso",
        email="aluno.reuso@icomp.ufam.edu.br",
        username="aluno.reuso",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        senha="SenhaBase@123",
        matricula="2023999001",
    )
    reset_token = _seed_password_reset_token(db_session, user_id=user.id)

    first_response = client.post(
        "/auth/confirmar-reset",
        json={
            "token": reset_token.token,
            "nova_senha": "SenhaNova@789",
        },
    )
    second_response = client.post(
        "/auth/confirmar-reset",
        json={
            "token": reset_token.token,
            "nova_senha": "OutraSenha@789",
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Token de reset ja foi utilizado."


def test_confirm_password_reset_rejects_expired_token(client, db_session) -> None:
    user = _seed_user(
        db_session,
        nome_completo="Aluno Expirado",
        email="aluno.expirado@icomp.ufam.edu.br",
        username="aluno.expirado",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        senha="SenhaBase@123",
        matricula="2023999002",
    )
    reset_token = _seed_password_reset_token(
        db_session,
        user_id=user.id,
        expires_at=datetime.now(UTC) - timedelta(hours=3),
    )

    response = client.post(
        "/auth/confirmar-reset",
        json={
            "token": reset_token.token,
            "nova_senha": "SenhaNova@123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Token de reset expirado."


def test_confirm_password_reset_rejects_invalid_token(client) -> None:
    response = client.post(
        "/auth/confirmar-reset",
        json={
            "token": "token-adulterado",
            "nova_senha": "SenhaNova@123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Token de reset invalido."


def test_confirm_password_reset_returns_422_for_short_password(client) -> None:
    response = client.post(
        "/auth/confirmar-reset",
        json={
            "token": str(uuid4()),
            "nova_senha": "1234567",
        },
    )

    assert response.status_code == 422
    assert "Senha deve ter no minimo 8 caracteres." in response.body.decode("utf-8")


def test_protected_route_without_token_returns_401(client) -> None:
    response = client.patch(
        f"/usuarios/{uuid4()}/aprovar",
        json={"acao": "APROVAR"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token de acesso nao informado."


def test_protected_route_with_invalid_token_returns_401(client) -> None:
    response = client.patch(
        f"/usuarios/{uuid4()}/aprovar",
        json={"acao": "APROVAR"},
        headers={"Authorization": "Bearer token-invalido"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token invalido."


def test_protected_route_with_expired_token_returns_401(client, db_session) -> None:
    coordinator = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="maria@icomp.ufam.edu.br",
        username="maria.coord",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
        senha="SenhaCoord@123",
    )
    expired_token = _build_bearer_token(
        user_id=coordinator.id,
        perfil=coordinator.perfil,
        expires_delta=timedelta(seconds=-1),
    )

    response = client.patch(
        f"/usuarios/{uuid4()}/aprovar",
        json={"acao": "APROVAR"},
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token expirado."

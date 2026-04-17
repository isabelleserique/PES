from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.app.core.config import get_settings
from backend.app.core.security import create_access_token, decode_access_token, hash_password
from backend.app.db.models import UserRecord
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

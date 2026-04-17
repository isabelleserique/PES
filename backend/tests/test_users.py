from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional
from uuid import uuid4

from backend.app.core.config import get_settings
from backend.app.core.security import create_access_token, hash_password, verify_password
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
    matricula: Optional[str] = None,
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
        failed_login_attempts=0,
        blocked_until=None,
        ativo=ativo,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _build_auth_headers(*, user_id: str, perfil: Perfil) -> dict[str, str]:
    settings = get_settings()
    token = create_access_token(
        payload={
            "user_id": user_id,
            "perfil": perfil.value,
        },
        secret_key=settings.jwt_secret,
        expires_delta=timedelta(hours=settings.session_timeout_hours),
        algorithm=settings.jwt_algorithm,
    )
    return {"Authorization": f"Bearer {token}"}


def test_create_coordenador_returns_201_and_never_exposes_password_hash(client, db_session, email_service, caplog) -> None:
    payload = {
        "nome_completo": "Maria Coordenadora",
        "email": "maria@icomp.ufam.edu.br",
        "username": "maria.coord",
        "senha": "SenhaTemp@123",
    }

    with caplog.at_level(logging.INFO, logger="backend.audit"):
        response = client.post("/usuarios/coordenador", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == {"id", "nome_completo"}
    assert body["nome_completo"] == payload["nome_completo"]

    stored_user = db_session.query(UserRecord).filter_by(email=payload["email"]).one()
    assert stored_user.perfil == Perfil.COORDENADOR
    assert stored_user.status == StatusCadastro.ATIVO
    assert stored_user.ativo is True
    assert stored_user.username == payload["username"]
    assert stored_user.senha_hash != payload["senha"]
    assert verify_password(payload["senha"], stored_user.senha_hash) is True

    assert email_service.calls == [
        {
            "to_email": payload["email"],
            "full_name": payload["nome_completo"],
            "username": payload["username"],
            "temporary_password": payload["senha"],
        }
    ]
    assert "action=CADASTRO_USUARIO" in caplog.text
    assert "perfil=COORDENADOR" in caplog.text
    assert "timestamp=" in caplog.text


def test_create_coordenador_returns_409_when_email_or_username_already_exists(client) -> None:
    first_payload = {
        "nome_completo": "Maria Coordenadora",
        "email": "maria@icomp.ufam.edu.br",
        "username": "maria.coord",
        "senha": "SenhaTemp@123",
    }
    conflict_payload = {
        "nome_completo": "Outra Pessoa",
        "email": "maria@icomp.ufam.edu.br",
        "username": "outra.coord",
        "senha": "OutraSenha@123",
    }

    first_response = client.post("/usuarios/coordenador", json=first_payload)
    conflict_response = client.post("/usuarios/coordenador", json=conflict_payload)

    assert first_response.status_code == 201
    assert conflict_response.status_code == 409
    assert conflict_response.json()["detail"] == "Nao foi possivel concluir o cadastro com os dados informados."


def test_create_coordenador_keeps_flow_alive_when_welcome_email_fails(client, email_service) -> None:
    email_service.should_fail = True
    payload = {
        "nome_completo": "Joao Coordenador",
        "email": "joao@icomp.ufam.edu.br",
        "username": "joao.coord",
        "senha": "SenhaTemp@456",
    }

    response = client.post("/usuarios/coordenador", json=payload)

    assert response.status_code == 201
    assert response.json()["nome_completo"] == payload["nome_completo"]


def test_request_registration_creates_pending_student_and_notifies_active_coordinators(
    client,
    db_session,
    email_service,
    caplog,
) -> None:
    coordinator = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="maria@icomp.ufam.edu.br",
        username="maria.coord",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    payload = {
        "nome_completo": "Aluno Teste",
        "email": "aluno@icomp.ufam.edu.br",
        "username": "aluno.teste",
        "senha": "SenhaAluno@123",
        "perfil": "ALUNO",
        "matricula": "2023123456",
    }

    with caplog.at_level(logging.INFO, logger="backend.audit"):
        response = client.post("/usuarios/solicitar-cadastro", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["nome_completo"] == payload["nome_completo"]
    assert body["status"] == "PENDENTE"
    assert body["mensagem"] == "Seu cadastro esta em analise. Aguarde aprovacao."

    stored_user = db_session.query(UserRecord).filter_by(email=payload["email"]).one()
    assert stored_user.perfil == Perfil.ALUNO
    assert stored_user.status == StatusCadastro.PENDENTE
    assert stored_user.ativo is False
    assert stored_user.matricula == payload["matricula"]
    assert verify_password(payload["senha"], stored_user.senha_hash) is True

    assert email_service.pending_notifications == [
        {
            "to_email": coordinator.email,
            "requester_name": payload["nome_completo"],
            "requester_email": payload["email"],
            "requester_username": payload["username"],
            "requester_profile": "ALUNO",
        }
    ]
    assert email_service.approval_calls == []
    assert "action=SOLICITACAO_CADASTRO" in caplog.text
    assert "status=PENDENTE" in caplog.text


def test_request_registration_allows_orientador_without_matricula(client, db_session) -> None:
    payload = {
        "nome_completo": "Professora Orientadora",
        "email": "orientadora@icomp.ufam.edu.br",
        "username": "orientadora.icomp",
        "senha": "SenhaOrientadora@123",
        "perfil": "ORIENTADOR",
    }

    response = client.post("/usuarios/solicitar-cadastro", json=payload)

    assert response.status_code == 201
    stored_user = db_session.query(UserRecord).filter_by(email=payload["email"]).one()
    assert stored_user.perfil == Perfil.ORIENTADOR
    assert stored_user.status == StatusCadastro.PENDENTE
    assert stored_user.matricula is None


def test_request_registration_returns_422_when_student_has_no_matricula(client) -> None:
    payload = {
        "nome_completo": "Aluno Sem Matricula",
        "email": "sem.matricula@icomp.ufam.edu.br",
        "username": "aluno.sem.matricula",
        "senha": "SenhaAluno@123",
        "perfil": "ALUNO",
    }

    response = client.post("/usuarios/solicitar-cadastro", json=payload)

    assert response.status_code == 422
    assert "Matricula e obrigatoria para perfil ALUNO." in response.body.decode("utf-8")


def test_request_registration_returns_409_when_email_already_exists(client, db_session) -> None:
    _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="maria@icomp.ufam.edu.br",
        username="maria.coord",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    payload = {
        "nome_completo": "Outra Pessoa",
        "email": "maria@icomp.ufam.edu.br",
        "username": "outra.pessoa",
        "senha": "OutraSenha@123",
        "perfil": "ORIENTADOR",
    }

    response = client.post("/usuarios/solicitar-cadastro", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Nao foi possivel concluir o cadastro com os dados informados."


def test_get_authenticated_profile_returns_current_user_data(client, db_session) -> None:
    user = _seed_user(
        db_session,
        nome_completo="Coordenadora Atual",
        email="coordenadora.atual@icomp.ufam.edu.br",
        username="coord.atual",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )

    response = client.request(
        "GET",
        "/usuarios/me",
        headers=_build_auth_headers(user_id=user.id, perfil=user.perfil),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user.id
    assert body["nome_completo"] == user.nome_completo
    assert body["email"] == user.email
    assert body["username"] == user.username
    assert body["perfil"] == "COORDENADOR"
    assert body["status"] == "ATIVO"
    assert body["ativo"] is True


def test_list_pending_registrations_returns_pending_users_for_active_coordinator(client, db_session) -> None:
    coordinator = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="maria@icomp.ufam.edu.br",
        username="maria.coord",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    first_pending = _seed_user(
        db_session,
        nome_completo="Aluno Pendente",
        email="aluno.pendente@icomp.ufam.edu.br",
        username="aluno.pendente",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.PENDENTE,
        ativo=False,
        matricula="2023123888",
    )
    second_pending = _seed_user(
        db_session,
        nome_completo="Orientadora Pendente",
        email="orientadora.pendente@icomp.ufam.edu.br",
        username="orientadora.pendente",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.PENDENTE,
        ativo=False,
    )
    _seed_user(
        db_session,
        nome_completo="Aluno Ativo",
        email="aluno.ativo@icomp.ufam.edu.br",
        username="aluno.ativo",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123999",
    )

    response = client.request(
        "GET",
        "/usuarios/pendentes",
        headers=_build_auth_headers(user_id=coordinator.id, perfil=coordinator.perfil),
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body] == [first_pending.id, second_pending.id]
    assert body[0]["perfil"] == "ALUNO"
    assert body[0]["matricula"] == "2023123888"
    assert body[1]["perfil"] == "ORIENTADOR"
    assert body[1]["matricula"] is None
    assert all(item["status"] == "PENDENTE" for item in body)


def test_list_pending_registrations_requires_active_coordinator(client, db_session) -> None:
    student = _seed_user(
        db_session,
        nome_completo="Aluno Ativo",
        email="aluno.ativo@icomp.ufam.edu.br",
        username="aluno.ativo",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123999",
    )

    response = client.request(
        "GET",
        "/usuarios/pendentes",
        headers=_build_auth_headers(user_id=student.id, perfil=student.perfil),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Perfil sem permissao para acessar este recurso."


def test_review_registration_approves_pending_user_and_logs_audit(client, db_session, email_service, caplog) -> None:
    coordinator = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="maria@icomp.ufam.edu.br",
        username="maria.coord",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    pending_user = _seed_user(
        db_session,
        nome_completo="Aluno Teste",
        email="aluno@icomp.ufam.edu.br",
        username="aluno.teste",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.PENDENTE,
        ativo=False,
        matricula="2023123456",
    )

    with caplog.at_level(logging.INFO, logger="backend.audit"):
        response = client.patch(
            f"/usuarios/{pending_user.id}/aprovar",
            json={"acao": "APROVAR"},
            headers=_build_auth_headers(user_id=coordinator.id, perfil=coordinator.perfil),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == pending_user.id
    assert body["perfil"] == "ALUNO"
    assert body["status"] == "ATIVO"

    db_session.refresh(pending_user)
    assert pending_user.status == StatusCadastro.ATIVO
    assert pending_user.ativo is True

    assert email_service.approval_calls == [
        {
            "to_email": pending_user.email,
            "full_name": pending_user.nome_completo,
            "username": pending_user.username,
        }
    ]
    assert "action=DECISAO_CADASTRO" in caplog.text
    assert "decision=APROVAR" in caplog.text
    assert f"actor_user_id={coordinator.id}" in caplog.text
    assert f"target_user_id={pending_user.id}" in caplog.text
    assert "status=ATIVO" in caplog.text


def test_review_registration_rejects_pending_user_without_sending_welcome_email(client, db_session, email_service) -> None:
    coordinator = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="maria@icomp.ufam.edu.br",
        username="maria.coord",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    pending_user = _seed_user(
        db_session,
        nome_completo="Professor Pendente",
        email="professor@icomp.ufam.edu.br",
        username="professor.icomp",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.PENDENTE,
        ativo=False,
    )

    response = client.patch(
        f"/usuarios/{pending_user.id}/aprovar",
        json={"acao": "REJEITAR"},
        headers=_build_auth_headers(user_id=coordinator.id, perfil=coordinator.perfil),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REJEITADO"

    db_session.refresh(pending_user)
    assert pending_user.status == StatusCadastro.REJEITADO
    assert pending_user.ativo is False
    assert email_service.approval_calls == []


def test_review_registration_requires_active_coordinator(client, db_session) -> None:
    non_coordinator = _seed_user(
        db_session,
        nome_completo="Aluno Ativo",
        email="aluno.ativo@icomp.ufam.edu.br",
        username="aluno.ativo",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123999",
    )
    pending_user = _seed_user(
        db_session,
        nome_completo="Outro Aluno",
        email="outro.aluno@icomp.ufam.edu.br",
        username="outro.aluno",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.PENDENTE,
        ativo=False,
        matricula="2023123000",
    )

    response = client.patch(
        f"/usuarios/{pending_user.id}/aprovar",
        json={"acao": "APROVAR"},
        headers=_build_auth_headers(user_id=non_coordinator.id, perfil=non_coordinator.perfil),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Perfil sem permissao para acessar este recurso."


def test_review_registration_returns_409_when_target_is_not_pending(client, db_session) -> None:
    coordinator = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="maria@icomp.ufam.edu.br",
        username="maria.coord",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    approved_user = _seed_user(
        db_session,
        nome_completo="Aluno Ja Ativo",
        email="ativo@icomp.ufam.edu.br",
        username="aluno.ativo",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123777",
    )

    response = client.patch(
        f"/usuarios/{approved_user.id}/aprovar",
        json={"acao": "REJEITAR"},
        headers=_build_auth_headers(user_id=coordinator.id, perfil=coordinator.perfil),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Solicitacao de cadastro nao esta pendente."

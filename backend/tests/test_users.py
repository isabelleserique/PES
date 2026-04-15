import logging

from backend.app.core.security import verify_password
from backend.app.db.models import UserRecord


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
    assert stored_user.perfil.value == "COORDENADOR"
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

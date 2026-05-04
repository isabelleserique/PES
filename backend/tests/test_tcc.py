from __future__ import annotations

import logging
from datetime import date, timedelta
from uuid import uuid4

from backend.app.core.config import get_settings
from backend.app.core.security import create_access_token, hash_password
from backend.app.db.models import PeriodoLetivoRecord, PrazoEtapaRecord, TCCEditLogRecord, TCCRecord, UserRecord
from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import AcaoEdicaoTCC, StatusTCC
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
    matricula: str | None = None,
    senha: str = "SenhaPadrao@123",
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


def _seed_periodo(
    db_session,
    *,
    nome: str,
    data_inicio: str,
    data_fim: str,
    ativo: bool,
    prazos: list[tuple[str, str, TipoTCC]] | None = None,
) -> PeriodoLetivoRecord:
    periodo = PeriodoLetivoRecord(
        id=str(uuid4()),
        nome=nome,
        data_inicio=date.fromisoformat(data_inicio),
        data_fim=date.fromisoformat(data_fim),
        ativo=ativo,
        prazos=[
            PrazoEtapaRecord(
                id=str(uuid4()),
                nome_etapa=nome_etapa,
                data_limite=date.fromisoformat(data_limite),
                tipo_tcc=tipo_tcc,
            )
            for nome_etapa, data_limite, tipo_tcc in (prazos or [])
        ],
    )
    db_session.add(periodo)
    db_session.commit()
    db_session.refresh(periodo)
    return periodo


def _seed_tcc(
    db_session,
    *,
    periodo_id: str,
    aluno_id: str,
    orientador_id: str,
    titulo: str,
    tipo_tcc: TipoTCC,
    prazo_excedido: bool = False,
    coorientador_id: str | None = None,
    status: StatusTCC = StatusTCC.AGUARDANDO_ACEITE,
) -> TCCRecord:
    tcc = TCCRecord(
        id=str(uuid4()),
        titulo=titulo,
        tipo_tcc=tipo_tcc,
        aluno_id=aluno_id,
        orientador_id=orientador_id,
        coorientador_id=coorientador_id,
        periodo_id=periodo_id,
        status=status,
        prazo_excedido=prazo_excedido,
    )
    db_session.add(tcc)
    db_session.commit()
    db_session.refresh(tcc)
    return tcc


def test_create_my_tcc_returns_201_marks_late_submission_and_notifies_orientador(
    client,
    db_session,
    email_service,
    caplog,
) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno TCC",
        email="aluno.tcc@icomp.ufam.edu.br",
        username="aluno.tcc",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123020",
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. TCC",
        email="prof.tcc@icomp.ufam.edu.br",
        username="prof.tcc",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=20)).isoformat(),
        data_fim=(today + timedelta(days=60)).isoformat(),
        ativo=True,
        prazos=[
            ("Definicao de Tema/Orientador", (today - timedelta(days=1)).isoformat(), TipoTCC.TODOS),
            ("Entrega Parcial", (today + timedelta(days=10)).isoformat(), TipoTCC.ARTIGO),
        ],
    )

    with caplog.at_level(logging.INFO, logger="backend.audit"):
        response = client.post(
            "/tcc/me",
            json={
                "titulo": "Agentes para Ensino",
                "tipo_tcc": "Artigo",
                "orientador_id": orientador.id,
            },
            headers=_build_auth_headers(user_id=aluno.id, perfil=aluno.perfil),
        )

    assert response.status_code == 201
    body = response.json()
    assert body["periodo_nome"] == periodo.nome
    assert body["status"] == "AGUARDANDO_ACEITE"
    assert body["prazo_excedido"] is True
    assert body["alerta_prazo"] is not None

    stored_tcc = db_session.query(TCCRecord).filter_by(aluno_id=aluno.id, periodo_id=periodo.id).one()
    assert stored_tcc.tipo_tcc == TipoTCC.ARTIGO
    assert stored_tcc.orientador_id == orientador.id

    logs = db_session.query(TCCEditLogRecord).filter_by(tcc_id=stored_tcc.id).all()
    assert len(logs) == 1
    assert logs[0].acao == AcaoEdicaoTCC.CRIACAO

    assert email_service.tcc_notifications == [
        {
            "to_email": orientador.email,
            "aluno_nome": aluno.nome_completo,
            "titulo": "Agentes para Ensino",
            "tipo_tcc": "Artigo",
            "periodo_nome": periodo.nome,
            "prazo_excedido": True,
        }
    ]
    assert "action=TCC_SUBMISSION" in caplog.text


def test_create_my_tcc_returns_409_when_student_submits_twice_in_same_period(client, db_session) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Unico",
        email="aluno.unico@icomp.ufam.edu.br",
        username="aluno.unico",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123021",
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Unico",
        email="prof.unico@icomp.ufam.edu.br",
        username="prof.unico",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=10)).isoformat(),
        data_fim=(today + timedelta(days=40)).isoformat(),
        ativo=True,
        prazos=[("Definicao de Tema/Orientador", (today + timedelta(days=7)).isoformat(), TipoTCC.TODOS)],
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Primeiro Registro",
        tipo_tcc=TipoTCC.ARTIGO,
    )

    response = client.post(
        "/tcc/me",
        json={
            "titulo": "Segundo Registro",
            "tipo_tcc": "Artigo",
            "orientador_id": orientador.id,
        },
        headers=_build_auth_headers(user_id=aluno.id, perfil=aluno.perfil),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Aluno ja informou um TCC neste periodo. Use a edicao para atualizar os dados."


def test_update_my_tcc_appends_edit_log_and_resets_status(client, db_session, email_service, caplog) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Edicao",
        email="aluno.edicao@icomp.ufam.edu.br",
        username="aluno.edicao",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123022",
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Antigo",
        email="prof.antigo@icomp.ufam.edu.br",
        username="prof.antigo",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    novo_orientador = _seed_user(
        db_session,
        nome_completo="Prof. Novo",
        email="prof.novo@icomp.ufam.edu.br",
        username="prof.novo",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    coorientador = _seed_user(
        db_session,
        nome_completo="Prof. Co",
        email="prof.co@icomp.ufam.edu.br",
        username="prof.co",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=5)).isoformat(),
        data_fim=(today + timedelta(days=50)).isoformat(),
        ativo=True,
        prazos=[("Definicao de Tema/Orientador", (today + timedelta(days=10)).isoformat(), TipoTCC.TODOS)],
    )
    tcc = _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Tema Inicial",
        tipo_tcc=TipoTCC.ARTIGO,
        status=StatusTCC.EM_ANDAMENTO,
    )

    with caplog.at_level(logging.INFO, logger="backend.audit"):
        response = client.patch(
            "/tcc/me",
            json={
                "titulo": "Tema Ajustado",
                "tipo_tcc": "Relatorio de Estagio",
                "orientador_id": novo_orientador.id,
                "coorientador_id": coorientador.id,
            },
            headers=_build_auth_headers(user_id=aluno.id, perfil=aluno.perfil),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["titulo"] == "Tema Ajustado"
    assert body["tipo_tcc"] == "Relatorio de Estagio"
    assert body["orientador_id"] == novo_orientador.id
    assert body["coorientador_id"] == coorientador.id
    assert body["status"] == "AGUARDANDO_ACEITE"

    db_session.refresh(tcc)
    assert tcc.titulo == "Tema Ajustado"
    assert tcc.tipo_tcc == TipoTCC.RELATORIO_ESTAGIO
    assert tcc.orientador_id == novo_orientador.id
    assert tcc.coorientador_id == coorientador.id
    assert tcc.status == StatusTCC.AGUARDANDO_ACEITE

    logs = db_session.query(TCCEditLogRecord).filter_by(tcc_id=tcc.id).all()
    assert len(logs) == 1
    assert logs[0].acao == AcaoEdicaoTCC.EDICAO
    assert logs[0].dados_anteriores["titulo"] == "Tema Inicial"
    assert logs[0].dados_novos["titulo"] == "Tema Ajustado"

    assert email_service.tcc_notifications == [
        {
            "to_email": novo_orientador.email,
            "aluno_nome": aluno.nome_completo,
            "titulo": "Tema Ajustado",
            "tipo_tcc": "Relatorio de Estagio",
            "periodo_nome": periodo.nome,
            "prazo_excedido": False,
        }
    ]
    assert "action=TCC_UPDATE" in caplog.text


def test_list_active_orientadores_returns_only_active_professors(client, db_session) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Lista",
        email="aluno.lista@icomp.ufam.edu.br",
        username="aluno.lista",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123023",
    )
    ativo = _seed_user(
        db_session,
        nome_completo="Prof. Ativo",
        email="prof.ativo@icomp.ufam.edu.br",
        username="prof.ativo",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    _seed_user(
        db_session,
        nome_completo="Prof. Pendente",
        email="prof.pendente@icomp.ufam.edu.br",
        username="prof.pendente",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.PENDENTE,
        ativo=False,
    )

    response = client.request(
        "GET",
        "/tcc/orientadores",
        headers=_build_auth_headers(user_id=aluno.id, perfil=aluno.perfil),
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": ativo.id,
            "nome_completo": ativo.nome_completo,
            "email": ativo.email,
        }
    ]

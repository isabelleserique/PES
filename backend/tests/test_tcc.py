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


def test_list_pending_orientation_requests_returns_only_current_orientador_requests(client, db_session) -> None:
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Pendencias",
        email="prof.pendencias@icomp.ufam.edu.br",
        username="prof.pendencias",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    outro_orientador = _seed_user(
        db_session,
        nome_completo="Prof. Outro",
        email="prof.outro@icomp.ufam.edu.br",
        username="prof.outro",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    aluno_pendente = _seed_user(
        db_session,
        nome_completo="Aluno Pendente",
        email="aluno.pendente.tcc@icomp.ufam.edu.br",
        username="aluno.pendente.tcc",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123024",
    )
    aluno_outro = _seed_user(
        db_session,
        nome_completo="Aluno Outro",
        email="aluno.outro.tcc@icomp.ufam.edu.br",
        username="aluno.outro.tcc",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123025",
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=10)).isoformat(),
        data_fim=(today + timedelta(days=45)).isoformat(),
        ativo=True,
        prazos=[
            ("Aceite do Orientador", (today - timedelta(days=2)).isoformat(), TipoTCC.ARTIGO),
            ("Aceite do Orientador", (today + timedelta(days=5)).isoformat(), TipoTCC.MONOGRAFIA),
        ],
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno_pendente.id,
        orientador_id=orientador.id,
        titulo="Tema em IA",
        tipo_tcc=TipoTCC.ARTIGO,
        prazo_excedido=True,
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno_outro.id,
        orientador_id=outro_orientador.id,
        titulo="Tema em Dados",
        tipo_tcc=TipoTCC.MONOGRAFIA,
    )

    response = client.request(
        "GET",
        "/tcc/orientacoes/pendentes",
        headers=_build_auth_headers(user_id=orientador.id, perfil=orientador.perfil),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["aluno_id"] == aluno_pendente.id
    assert body[0]["prazo_excedido"] is True
    assert body[0]["acao_fora_do_prazo"] is True
    assert body[0]["alerta_submissao_prazo"] is not None
    assert body[0]["alerta_acao_prazo"] is not None


def test_accept_orientation_updates_status_notifies_student_and_logs_late_action(
    client,
    db_session,
    email_service,
    caplog,
) -> None:
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Aceite",
        email="prof.aceite@icomp.ufam.edu.br",
        username="prof.aceite",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Aceite",
        email="aluno.aceite@icomp.ufam.edu.br",
        username="aluno.aceite",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123026",
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=15)).isoformat(),
        data_fim=(today + timedelta(days=30)).isoformat(),
        ativo=True,
        prazos=[("Aceite do Orientador", (today - timedelta(days=1)).isoformat(), TipoTCC.ARTIGO)],
    )
    tcc = _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Tema Aceito",
        tipo_tcc=TipoTCC.ARTIGO,
        status=StatusTCC.AGUARDANDO_ACEITE,
    )

    with caplog.at_level(logging.INFO, logger="backend.audit"):
        response = client.patch(
            f"/tcc/orientacoes/{tcc.id}/decisao",
            json={
                "acao": "ACEITAR",
                "observacao": "Vamos seguir com o tema.",
            },
            headers=_build_auth_headers(user_id=orientador.id, perfil=orientador.perfil),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "EM_ANDAMENTO"
    assert body["observacao_orientador"] == "Vamos seguir com o tema."
    assert body["acao_fora_do_prazo"] is True
    assert body["alerta_acao_prazo"] is not None

    db_session.refresh(tcc)
    assert tcc.status == StatusTCC.EM_ANDAMENTO
    assert tcc.observacao_orientador == "Vamos seguir com o tema."

    logs = db_session.query(TCCEditLogRecord).filter_by(tcc_id=tcc.id).all()
    assert len(logs) == 1
    assert logs[0].acao == AcaoEdicaoTCC.ACEITE_ORIENTACAO
    assert logs[0].observacao == "Vamos seguir com o tema."

    assert email_service.orientation_decisions == [
        {
            "to_email": aluno.email,
            "aluno_nome": aluno.nome_completo,
            "titulo": tcc.titulo,
            "orientador_nome": orientador.nome_completo,
            "accepted": True,
            "observacao": "Vamos seguir com o tema.",
            "outside_deadline": True,
        }
    ]
    assert "action=ORIENTATION_DECISION" in caplog.text
    assert "decision=ACEITAR" in caplog.text
    assert "outside_deadline=True" in caplog.text


def test_reject_orientation_requires_observation_and_sets_sem_orientador(
    client,
    db_session,
    email_service,
) -> None:
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Recusa",
        email="prof.recusa@icomp.ufam.edu.br",
        username="prof.recusa",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Recusa",
        email="aluno.recusa@icomp.ufam.edu.br",
        username="aluno.recusa",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123027",
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=3)).isoformat(),
        data_fim=(today + timedelta(days=40)).isoformat(),
        ativo=True,
        prazos=[("Aceite do Orientador", (today + timedelta(days=4)).isoformat(), TipoTCC.MONOGRAFIA)],
    )
    tcc = _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Tema Recusado",
        tipo_tcc=TipoTCC.MONOGRAFIA,
        status=StatusTCC.AGUARDANDO_ACEITE,
    )

    invalid_response = client.patch(
        f"/tcc/orientacoes/{tcc.id}/decisao",
        json={"acao": "RECUSAR"},
        headers=_build_auth_headers(user_id=orientador.id, perfil=orientador.perfil),
    )

    assert invalid_response.status_code == 422
    assert "Observacao e obrigatoria ao recusar a orientacao." in invalid_response.body.decode("utf-8")

    response = client.patch(
        f"/tcc/orientacoes/{tcc.id}/decisao",
        json={
            "acao": "RECUSAR",
            "observacao": "Sem vagas para este tema",
        },
        headers=_build_auth_headers(user_id=orientador.id, perfil=orientador.perfil),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SEM_ORIENTADOR"
    assert body["observacao_orientador"] == "Sem vagas para este tema"
    assert body["acao_fora_do_prazo"] is False

    db_session.refresh(tcc)
    assert tcc.status == StatusTCC.SEM_ORIENTADOR
    assert tcc.observacao_orientador == "Sem vagas para este tema"

    assert email_service.orientation_decisions[-1] == {
        "to_email": aluno.email,
        "aluno_nome": aluno.nome_completo,
        "titulo": tcc.titulo,
        "orientador_nome": orientador.nome_completo,
        "accepted": False,
        "observacao": "Sem vagas para este tema",
        "outside_deadline": False,
    }


def test_orientation_decision_denies_other_orientador(client, db_session) -> None:
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Dono",
        email="prof.dono@icomp.ufam.edu.br",
        username="prof.dono",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    outro_orientador = _seed_user(
        db_session,
        nome_completo="Prof. Intruso",
        email="prof.intruso@icomp.ufam.edu.br",
        username="prof.intruso",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Dono",
        email="aluno.dono@icomp.ufam.edu.br",
        username="aluno.dono",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123028",
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=3)).isoformat(),
        data_fim=(today + timedelta(days=20)).isoformat(),
        ativo=True,
        prazos=[("Aceite do Orientador", (today + timedelta(days=4)).isoformat(), TipoTCC.ARTIGO)],
    )
    tcc = _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Tema Protegido",
        tipo_tcc=TipoTCC.ARTIGO,
    )

    response = client.patch(
        f"/tcc/orientacoes/{tcc.id}/decisao",
        json={"acao": "ACEITAR"},
        headers=_build_auth_headers(user_id=outro_orientador.id, perfil=outro_orientador.perfil),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Solicitacao de orientacao nao encontrada."

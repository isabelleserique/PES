from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import uuid4

from backend.app.db.models import DepositoFinalRecord, DocumentoDepositoRecord, NotificacaoPrazoRecord
from backend.app.models.deposito import StatusDeposito, TipoDocumentoDeposito
from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import StatusTCC
from backend.app.models.user import Perfil, StatusCadastro
from backend.app.services.notificacao_service import NotificacaoPrazoService
from backend.tests.test_tcc import _build_auth_headers, _seed_periodo, _seed_tcc, _seed_user


def test_coordenador_dashboard_periodo_ativo_returns_sprint5_summary(client, db_session) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Coord Dashboard",
        email="coord.dashboard@icomp.ufam.edu.br",
        username="coord.dashboard",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    aluno_com_tcc = _seed_user(
        db_session,
        nome_completo="Aluno Com TCC",
        email="aluno.com.tcc@icomp.ufam.edu.br",
        username="aluno.com.tcc",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="202800001",
    )
    aluno_sem_tcc = _seed_user(
        db_session,
        nome_completo="Aluno Sem TCC",
        email="aluno.sem.tcc@icomp.ufam.edu.br",
        username="aluno.sem.tcc",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="202800002",
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Dashboard",
        email="prof.dashboard@icomp.ufam.edu.br",
        username="prof.dashboard",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2028.1",
        data_inicio=(today - timedelta(days=20)).isoformat(),
        data_fim=(today + timedelta(days=90)).isoformat(),
        ativo=True,
        prazos=[("1ª Entrega", (today - timedelta(days=2)).isoformat(), TipoTCC.MONOGRAFIA)],
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno_com_tcc.id,
        orientador_id=orientador.id,
        titulo="Monografia com pendencia",
        tipo_tcc=TipoTCC.MONOGRAFIA,
        status=StatusTCC.EM_ANDAMENTO,
    )

    response = client.request(
        "GET",
        "/periodos/ativo/dashboard",
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["periodo"]["id"] == periodo.id
    assert body["alunos"]["total"] == 2
    assert body["alunos"]["por_tipo"]["monografia"] == 1
    assert body["alunos"]["por_tipo"]["sem_tcc"] == 1
    assert body["alunos"]["sem_orientador_aceito"] == 1
    assert body["alunos"]["com_prazo_vencido_sem_entrega"] == 1
    assert {aluno["aluno_id"] for aluno in body["alunos_detalhados"]} == {aluno_com_tcc.id, aluno_sem_tcc.id}


def test_public_tcc_search_detail_preview_and_download(client, db_session, tmp_path) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Publico",
        email="aluno.publico@icomp.ufam.edu.br",
        username="aluno.publico",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Publico",
        email="prof.publico@icomp.ufam.edu.br",
        username="prof.publico",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2028.2",
        data_inicio=(today - timedelta(days=20)).isoformat(),
        data_fim=(today + timedelta(days=90)).isoformat(),
        ativo=True,
    )
    tcc = _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Visao computacional na floresta",
        tipo_tcc=TipoTCC.ARTIGO,
        status=StatusTCC.EM_ANDAMENTO,
    )
    tcc.resumo = "Resumo publico do trabalho."
    tcc.area_tematica = "Inteligência Artificial"
    tcc.curso = "Ciência da Computação"
    tcc.data_defesa = today
    tcc.banca = ["Prof. Publico", "Prof. Banca"]
    aluno.publicar_tcc_portal_publico = True
    db_session.commit()

    arquivo = tmp_path / "artigo-publico.pdf"
    arquivo.write_bytes(b"%PDF-publico")
    deposito = DepositoFinalRecord(
        id=str(uuid4()),
        tcc_id=tcc.id,
        status=StatusDeposito.DEPOSITADO,
        submetido_em=datetime.combine(today, datetime.min.time()),
    )
    db_session.add(deposito)
    db_session.flush()
    documento = DocumentoDepositoRecord(
        id=str(uuid4()),
        deposito_id=deposito.id,
        tipo_documento=TipoDocumentoDeposito.TCC_FINAL,
        nome_original=arquivo.name,
        caminho_original=str(arquivo),
        mime_type="application/pdf",
        tamanho_bytes=len(b"%PDF-publico"),
        caminho_preview_pdf=str(arquivo),
    )
    db_session.add(documento)
    db_session.commit()

    search_response = client.request("GET", "/public/tcc?titulo=floresta")
    assert search_response.status_code == 200
    search_body = search_response.json()
    assert len(search_body) == 1
    assert search_body[0]["id"] == tcc.id
    assert search_body[0]["area_tematica"] == "Inteligência Artificial"

    detail_response = client.request("GET", f"/public/tcc/{tcc.id}")
    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["resumo"] == "Resumo publico do trabalho."
    assert detail_body["documentos"][0]["id"] == documento.id
    assert detail_body["documentos"][0]["url_preview"].endswith(f"/public/tcc/{tcc.id}/documentos/{documento.id}/arquivo")

    file_response = client.request("GET", f"/public/tcc/{tcc.id}/documentos/{documento.id}/arquivo")
    assert file_response.status_code == 200
    assert file_response.body == b"%PDF-publico"


def test_notificacao_prazo_sends_email_once_for_upcoming_deadline(db_session, email_service) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Notificacao",
        email="aluno.notificacao@icomp.ufam.edu.br",
        username="aluno.notificacao",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Notificacao",
        email="prof.notificacao@icomp.ufam.edu.br",
        username="prof.notificacao",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2029.1",
        data_inicio=(today - timedelta(days=10)).isoformat(),
        data_fim=(today + timedelta(days=100)).isoformat(),
        ativo=True,
        prazos=[("2ª Entrega", (today + timedelta(days=2)).isoformat(), TipoTCC.MONOGRAFIA)],
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Monografia com alerta",
        tipo_tcc=TipoTCC.MONOGRAFIA,
        status=StatusTCC.EM_ANDAMENTO,
    )

    service = NotificacaoPrazoService()
    first_result = service.processar_alertas_prazos(
        session=db_session,
        email_service=email_service,
        reference_date=today,
    )
    second_result = service.processar_alertas_prazos(
        session=db_session,
        email_service=email_service,
        reference_date=today,
    )

    assert first_result.enviadas == 2
    assert second_result.enviadas == 0
    assert second_result.ignoradas == 2
    assert email_service.deadline_notifications == [
        {
            "to_email": aluno.email,
            "aluno_nome": aluno.nome_completo,
            "titulo": "Monografia com alerta",
            "etapa": "2ª Entrega",
            "data_limite": (today + timedelta(days=2)).isoformat(),
            "tipo_alerta": "A_VENCER",
        }
    ]
    assert email_service.advisor_deadline_notifications == [
        {
            "to_email": orientador.email,
            "orientador_nome": orientador.nome_completo,
            "aluno_nome": aluno.nome_completo,
            "titulo": "Monografia com alerta",
            "etapa": "2ª Entrega",
            "data_limite": (today + timedelta(days=2)).isoformat(),
            "tipo_alerta": "A_VENCER",
        }
    ]
    assert db_session.query(NotificacaoPrazoRecord).count() == 2

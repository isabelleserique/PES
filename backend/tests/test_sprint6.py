from __future__ import annotations

import asyncio
from datetime import date, timedelta

from backend.app.core.config import get_settings
from backend.app.models.deposito import StatusDeposito, TipoDocumentoDeposito
from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import StatusTCC
from backend.app.models.user import Perfil, StatusCadastro
from backend.app.services.audit_service import AuditService
from backend.app.services.deposito_service import DepositoService
from backend.tests.test_submissoes import _build_upload
from backend.tests.test_tcc import _build_auth_headers, _seed_periodo, _seed_tcc, _seed_user


def test_orientador_registers_banca_and_notifies_student(client, db_session, email_service) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Banca",
        email="aluno.banca@icomp.ufam.edu.br",
        username="aluno.banca",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Banca",
        email="prof.banca@icomp.ufam.edu.br",
        username="prof.banca",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2030.1",
        data_inicio=(today - timedelta(days=20)).isoformat(),
        data_fim=(today + timedelta(days=90)).isoformat(),
        ativo=True,
    )
    tcc = _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="TCC com banca",
        tipo_tcc=TipoTCC.MONOGRAFIA,
        status=StatusTCC.EM_ANDAMENTO,
    )

    response = client.post(
        "/defesas/banca",
        json={
            "aluno_id": aluno.id,
            "data_defesa": "2030-07-10T14:30:00",
            "local": "Auditório do IComp",
            "membros": [
                {
                    "nome": "Avaliador Interno",
                    "titulacao": "Doutor",
                    "instituicao": "UFAM",
                    "papel": "AVALIADOR_INTERNO",
                },
                {
                    "nome": "Avaliador Externo",
                    "titulacao": "Doutor",
                    "instituicao": "UEA",
                    "papel": "AVALIADOR_EXTERNO",
                },
                {
                    "nome": "Suplente",
                    "titulacao": "Mestre",
                    "instituicao": "UFAM",
                    "papel": "SUPLENTE",
                },
            ],
        },
        headers=_build_auth_headers(user_id=orientador.id, perfil=orientador.perfil),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tcc_id"] == tcc.id
    assert body["aluno_nome"] == aluno.nome_completo
    assert len(body["membros"]) == 3
    assert email_service.banca_notifications[0]["to_email"] == aluno.email

    db_session.refresh(tcc)
    assert tcc.data_defesa == date(2030, 7, 10)
    assert tcc.banca == ["Avaliador Interno", "Avaliador Externo", "Suplente"]

    aluno_response = client.request(
        "GET",
        "/defesas/banca",
        headers=_build_auth_headers(user_id=aluno.id, perfil=aluno.perfil),
    )
    assert aluno_response.status_code == 200
    assert aluno_response.json()["id"] == body["id"]


def test_deposito_final_status_and_public_portal_visibility(client, db_session, tmp_path, email_service) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Coord Deposito",
        email="coord.deposito@icomp.ufam.edu.br",
        username="coord.deposito",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Deposito",
        email="aluno.deposito@icomp.ufam.edu.br",
        username="aluno.deposito",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Deposito",
        email="prof.deposito@icomp.ufam.edu.br",
        username="prof.deposito",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    aluno.publicar_tcc_portal_publico = True
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2030.2",
        data_inicio=(today - timedelta(days=20)).isoformat(),
        data_fim=(today + timedelta(days=90)).isoformat(),
        ativo=True,
    )
    tcc = _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="TCC depositado",
        tipo_tcc=TipoTCC.ARTIGO,
        status=StatusTCC.EM_ANDAMENTO,
    )
    tcc.area_tematica = "Sistemas"
    db_session.commit()

    service = DepositoService(settings=get_settings().model_copy(update={"upload_dir": tmp_path}))
    deposito = asyncio.run(
        service.submeter_deposito(
            session=db_session,
            current_user=aluno,
            documentos={
                TipoDocumentoDeposito.TCC_FINAL: _build_upload("final.pdf", b"%PDF-final"),
                TipoDocumentoDeposito.ATA_DEFESA: _build_upload("ata.pdf", b"%PDF-ata"),
                TipoDocumentoDeposito.FOLHA_APROVACAO: _build_upload("folha.pdf", b"%PDF-folha"),
                TipoDocumentoDeposito.FORMULARIOS: _build_upload("formularios.docx", b"docx-form"),
                TipoDocumentoDeposito.DECLARACOES: _build_upload("declaracoes.pdf", b"%PDF-declaracoes"),
            },
            audit_service=AuditService(),
        )
    )

    assert deposito.status == StatusDeposito.EM_REVISAO
    assert len(deposito.documentos) == 5
    assert client.get("/public/tcc?titulo=depositado").json() == []

    update_response = client.patch(
        f"/biblioteca/deposito/{deposito.id}/status",
        json={"status": "DEPOSITADO", "observacao_revisao": "Arquivos validados."},
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "DEPOSITADO"
    assert email_service.deposito_status_notifications[0]["to_email"] == aluno.email

    search_response = client.get("/public/tcc?titulo=depositado")
    assert search_response.status_code == 200
    assert search_response.json()[0]["id"] == tcc.id

    detail_response = client.get(f"/public/tcc/{tcc.id}")
    assert detail_response.status_code == 200
    documento_publico = detail_response.json()["documentos"][0]
    assert documento_publico["tipo"] == "TCC_FINAL"

    file_response = client.get(f"/public/tcc/{tcc.id}/documentos/{documento_publico['id']}/arquivo")
    assert file_response.status_code == 200
    assert file_response.body == b"%PDF-final"


def test_privacidade_consentimento_roundtrip(client, db_session) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Privacidade",
        email="aluno.privacidade@icomp.ufam.edu.br",
        username="aluno.privacidade",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    headers = _build_auth_headers(user_id=aluno.id, perfil=aluno.perfil)

    initial_response = client.request("GET", "/privacidade/consentimento", headers=headers)
    assert initial_response.status_code == 200
    assert initial_response.json()["publicar_portal_publico"] is False

    update_response = client.request(
        "PUT",
        "/privacidade/consentimento",
        json_body={"publicar_portal_publico": True, "compartilhar_terceiros": False},
        headers=headers,
    )

    assert update_response.status_code == 200
    body = update_response.json()
    assert body["publicar_portal_publico"] is True
    assert body["compartilhar_terceiros"] is False
    assert body["atualizado_em"] is not None

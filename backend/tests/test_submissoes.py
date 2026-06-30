from __future__ import annotations

import asyncio
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from backend.app.core.config import get_settings
from backend.app.db.models import ApresentacaoArtigoRecord, SubmissaoEntregavelRecord
from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import StatusTCC
from backend.app.models.user import Perfil, StatusCadastro
from backend.app.services.submissao_service import (
    COMPROVANTE_REQUIRED_DETAIL,
    PRESENTATION_DATA_REQUIRED_DETAIL,
    SubmissaoService,
)
from backend.tests.test_tcc import _build_auth_headers, _seed_periodo, _seed_tcc, _seed_user


def _build_upload(filename: str, content: bytes, content_type: str = "application/pdf") -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        headers=Headers({"content-type": content_type}),
    )


def _seed_submissao(
    db_session,
    *,
    tcc_id: str,
    aluno_id: str,
    tipo_tcc: TipoTCC,
    etapa: str,
    versao: int,
    nome_arquivo: str,
    caminho_arquivo: str | None = None,
    fora_do_prazo: bool = False,
    foi_aceito: bool = False,
    nome_comprovante: str | None = None,
    nota_automatica: int | None = None,
) -> SubmissaoEntregavelRecord:
    submissao = SubmissaoEntregavelRecord(
        id=str(uuid4()),
        tcc_id=tcc_id,
        aluno_id=aluno_id,
        tipo_tcc=tipo_tcc,
        etapa=etapa,
        versao=versao,
        nome_arquivo=nome_arquivo,
        caminho_arquivo=caminho_arquivo or f"/tmp/{nome_arquivo}",
        tipo_conteudo="application/pdf",
        tamanho_bytes=1024,
        foi_aceito=foi_aceito,
        nome_comprovante=nome_comprovante,
        caminho_comprovante=f"/tmp/{nome_comprovante}" if nome_comprovante else None,
        tipo_conteudo_comprovante="application/pdf" if nome_comprovante else None,
        tamanho_comprovante_bytes=512 if nome_comprovante else None,
        fora_do_prazo=fora_do_prazo,
        nota_automatica=nota_automatica,
    )
    db_session.add(submissao)
    db_session.commit()
    db_session.refresh(submissao)
    return submissao


def test_submeter_artigo_persists_files_and_returns_auto_grade(client, db_session, tmp_path) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Artigo",
        email="aluno.artigo@icomp.ufam.edu.br",
        username="aluno.artigo",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123030",
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Artigo",
        email="prof.artigo@icomp.ufam.edu.br",
        username="prof.artigo",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=30)).isoformat(),
        data_fim=(today + timedelta(days=30)).isoformat(),
        ativo=True,
        prazos=[("Submissao de Artigo", (today - timedelta(days=1)).isoformat(), TipoTCC.ARTIGO)],
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Artigo sobre Sistemas",
        tipo_tcc=TipoTCC.ARTIGO,
        status=StatusTCC.EM_ANDAMENTO,
    )
    settings = get_settings().model_copy(update={"upload_dir": tmp_path})
    service = SubmissaoService(settings=settings)

    response = asyncio.run(
        service.submeter_entregavel(
            session=db_session,
            current_user=aluno,
            etapa="Artigo Final",
            arquivo=_build_upload("artigo.pdf", b"%PDF-1.4"),
            foi_aceito=True,
            comprovante=_build_upload("aceite.pdf", b"%PDF-proof"),
            apresentacao_data=today,
            apresentacao_tipo_veiculo="Conferência",
            apresentacao_veiculo_publicacao="Simpósio de Sistemas",
            apresentacao_local="Manaus",
            apresentacao_observacoes="Trilha principal",
        )
    )

    assert response.versao == 1
    assert response.nota_automatica == 10

    stored = db_session.query(SubmissaoEntregavelRecord).one()
    assert stored.aluno_id == aluno.id
    assert stored.tipo_tcc == TipoTCC.ARTIGO
    assert stored.etapa == "Artigo Final"
    assert stored.nome_arquivo == "artigo.pdf"
    assert stored.nome_comprovante == "aceite.pdf"
    assert stored.foi_aceito is True
    assert stored.fora_do_prazo is True
    assert stored.nota_automatica == 10
    assert tmp_path in Path(stored.caminho_arquivo).parents
    assert stored.caminho_comprovante is not None
    apresentacao = db_session.query(ApresentacaoArtigoRecord).one()
    assert apresentacao.submissao_id == stored.id
    assert apresentacao.data_apresentacao == today
    assert apresentacao.tipo_veiculo == "Conferência"
    assert apresentacao.veiculo_publicacao == "Simpósio de Sistemas"
    assert apresentacao.local_apresentacao == "Manaus"
    assert apresentacao.observacoes == "Trilha principal"

    history = service.listar_entregaveis(session=db_session, current_user=aluno)
    assert len(history) == 1
    assert history[0].id == stored.id

    arquivo_response = client.request(
        "GET",
        f"/submissoes/entregaveis/{stored.id}/arquivo",
        headers=_build_auth_headers(user_id=orientador.id, perfil=orientador.perfil),
    )
    assert arquivo_response.status_code == 200
    assert arquivo_response.body == b"%PDF-1.4"

    comprovante_response = client.request(
        "GET",
        f"/submissoes/entregaveis/{stored.id}/comprovante",
        headers=_build_auth_headers(user_id=aluno.id, perfil=aluno.perfil),
    )
    assert comprovante_response.status_code == 200
    assert comprovante_response.body == b"%PDF-proof"

    outro_orientador = _seed_user(
        db_session,
        nome_completo="Prof. Sem Acesso",
        email="prof.sem.acesso.submissao@icomp.ufam.edu.br",
        username="prof.sem.acesso.submissao",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    forbidden_response = client.request(
        "GET",
        f"/submissoes/entregaveis/{stored.id}/arquivo",
        headers=_build_auth_headers(user_id=outro_orientador.id, perfil=outro_orientador.perfil),
    )
    assert forbidden_response.status_code == 403


def test_submeter_artigo_requires_proof_when_marked_as_accepted(db_session, tmp_path) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Sem Comprovante",
        email="aluno.sem.comprovante@icomp.ufam.edu.br",
        username="aluno.sem.comprovante",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Sem Comprovante",
        email="prof.sem.comprovante@icomp.ufam.edu.br",
        username="prof.sem.comprovante",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=30)).isoformat(),
        data_fim=(today + timedelta(days=30)).isoformat(),
        ativo=True,
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Artigo sem comprovante",
        tipo_tcc=TipoTCC.ARTIGO,
    )
    settings = get_settings().model_copy(update={"upload_dir": tmp_path})
    service = SubmissaoService(settings=settings)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            service.submeter_entregavel(
                session=db_session,
                current_user=aluno,
                etapa="Artigo Final",
                arquivo=_build_upload("artigo.pdf", b"%PDF-1.4"),
                foi_aceito=True,
                comprovante=None,
            )
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == COMPROVANTE_REQUIRED_DETAIL


def test_submeter_artigo_requires_presentation_data_when_marked_as_accepted(db_session, tmp_path) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Sem Apresentacao",
        email="aluno.sem.apresentacao@icomp.ufam.edu.br",
        username="aluno.sem.apresentacao",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Sem Apresentacao",
        email="prof.sem.apresentacao@icomp.ufam.edu.br",
        username="prof.sem.apresentacao",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=30)).isoformat(),
        data_fim=(today + timedelta(days=30)).isoformat(),
        ativo=True,
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Artigo sem apresentação",
        tipo_tcc=TipoTCC.ARTIGO,
    )
    service = SubmissaoService(settings=get_settings().model_copy(update={"upload_dir": tmp_path}))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            service.submeter_entregavel(
                session=db_session,
                current_user=aluno,
                etapa="Artigo Final",
                arquivo=_build_upload("artigo.pdf", b"%PDF-1.4"),
                foi_aceito=True,
                comprovante=_build_upload("aceite.pdf", b"%PDF-proof"),
            )
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == PRESENTATION_DATA_REQUIRED_DETAIL


def test_submeter_artigo_persists_selected_deliverable_step_without_accepted_flag(db_session, tmp_path) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Artigo Parcial",
        email="aluno.artigo.parcial@icomp.ufam.edu.br",
        username="aluno.artigo.parcial",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Artigo Parcial",
        email="prof.artigo.parcial@icomp.ufam.edu.br",
        username="prof.artigo.parcial",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=30)).isoformat(),
        data_fim=(today + timedelta(days=30)).isoformat(),
        ativo=True,
        prazos=[("1ª Entrega", (today + timedelta(days=3)).isoformat(), TipoTCC.ARTIGO)],
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Artigo em Etapas",
        tipo_tcc=TipoTCC.ARTIGO,
    )
    service = SubmissaoService(settings=get_settings().model_copy(update={"upload_dir": tmp_path}))

    response = asyncio.run(
        service.submeter_entregavel(
            session=db_session,
            current_user=aluno,
            etapa="1ª Entrega",
            arquivo=_build_upload("artigo-parcial.pdf", b"%PDF-1.4"),
            foi_aceito=False,
            comprovante=None,
        )
    )

    stored = db_session.query(SubmissaoEntregavelRecord).one()
    assert response.etapa == "1ª Entrega"
    assert response.nota_automatica is None
    assert stored.tipo_tcc == TipoTCC.ARTIGO
    assert stored.etapa == "1ª Entrega"
    assert stored.foi_aceito is False
    assert stored.fora_do_prazo is False


def test_submeter_monografia_persists_selected_deliverable_step(db_session, tmp_path) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Monografia",
        email="aluno.monografia@icomp.ufam.edu.br",
        username="aluno.monografia",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Monografia",
        email="prof.monografia@icomp.ufam.edu.br",
        username="prof.monografia",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=30)).isoformat(),
        data_fim=(today + timedelta(days=30)).isoformat(),
        ativo=True,
        prazos=[("2ª Entrega", (today + timedelta(days=5)).isoformat(), TipoTCC.MONOGRAFIA)],
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Monografia sobre Sistemas",
        tipo_tcc=TipoTCC.MONOGRAFIA,
    )
    service = SubmissaoService(settings=get_settings().model_copy(update={"upload_dir": tmp_path}))

    response = asyncio.run(
        service.submeter_entregavel(
            session=db_session,
            current_user=aluno,
            etapa="2ª Entrega",
            arquivo=_build_upload("monografia.pdf", b"%PDF-1.4"),
            foi_aceito=True,
            comprovante=None,
        )
    )

    stored = db_session.query(SubmissaoEntregavelRecord).one()
    assert response.etapa == "2ª Entrega"
    assert stored.tipo_tcc == TipoTCC.MONOGRAFIA
    assert stored.etapa == "2ª Entrega"
    assert stored.foi_aceito is False
    assert stored.nota_automatica is None
    assert stored.fora_do_prazo is False


def test_submeter_relatorio_estagio_persists_selected_deliverable_step(db_session, tmp_path) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Estagio",
        email="aluno.estagio@icomp.ufam.edu.br",
        username="aluno.estagio",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Estagio",
        email="prof.estagio@icomp.ufam.edu.br",
        username="prof.estagio",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=30)).isoformat(),
        data_fim=(today + timedelta(days=30)).isoformat(),
        ativo=True,
        prazos=[("Relatório Final", (today - timedelta(days=2)).isoformat(), TipoTCC.RELATORIO_ESTAGIO)],
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Relatorio de Estagio",
        tipo_tcc=TipoTCC.RELATORIO_ESTAGIO,
    )
    service = SubmissaoService(settings=get_settings().model_copy(update={"upload_dir": tmp_path}))

    response = asyncio.run(
        service.submeter_entregavel(
            session=db_session,
            current_user=aluno,
            etapa="Relatório Final",
            arquivo=_build_upload("relatorio.pdf", b"%PDF-1.4"),
            foi_aceito=False,
            comprovante=None,
        )
    )

    stored = db_session.query(SubmissaoEntregavelRecord).one()
    assert response.etapa == "Relatório Final"
    assert stored.tipo_tcc == TipoTCC.RELATORIO_ESTAGIO
    assert stored.etapa == "Relatório Final"
    assert stored.fora_do_prazo is True


def test_historico_submissoes_coordenador_and_orientador_include_versions_and_tcc_data(client, db_session) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Coord Histórico",
        email="coord.historico@icomp.ufam.edu.br",
        username="coord.historico",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    aluno_mono = _seed_user(
        db_session,
        nome_completo="Aluno Monografia Histórico",
        email="aluno.mono.historico@icomp.ufam.edu.br",
        username="aluno.mono.historico",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2026123401",
    )
    aluno_artigo = _seed_user(
        db_session,
        nome_completo="Aluno Artigo Histórico",
        email="aluno.artigo.historico@icomp.ufam.edu.br",
        username="aluno.artigo.historico",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2026123402",
    )
    orientador_mono = _seed_user(
        db_session,
        nome_completo="Prof. Mono Histórico",
        email="prof.mono.historico@icomp.ufam.edu.br",
        username="prof.mono.historico",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador_artigo = _seed_user(
        db_session,
        nome_completo="Prof. Artigo Histórico",
        email="prof.artigo.historico@icomp.ufam.edu.br",
        username="prof.artigo.historico",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.2",
        data_inicio=(today - timedelta(days=10)).isoformat(),
        data_fim=(today + timedelta(days=120)).isoformat(),
        ativo=True,
    )
    tcc_mono = _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno_mono.id,
        orientador_id=orientador_mono.id,
        titulo="Monografia com Versões",
        tipo_tcc=TipoTCC.MONOGRAFIA,
        status=StatusTCC.EM_ANDAMENTO,
    )
    tcc_artigo = _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno_artigo.id,
        orientador_id=orientador_artigo.id,
        titulo="Artigo Aceito",
        tipo_tcc=TipoTCC.ARTIGO,
        status=StatusTCC.EM_ANDAMENTO,
    )
    _seed_submissao(
        db_session,
        tcc_id=tcc_mono.id,
        aluno_id=aluno_mono.id,
        tipo_tcc=TipoTCC.MONOGRAFIA,
        etapa="1ª Entrega",
        versao=1,
        nome_arquivo="mono-v1.pdf",
    )
    _seed_submissao(
        db_session,
        tcc_id=tcc_mono.id,
        aluno_id=aluno_mono.id,
        tipo_tcc=TipoTCC.MONOGRAFIA,
        etapa="1ª Entrega",
        versao=2,
        nome_arquivo="mono-v2.pdf",
        fora_do_prazo=True,
    )
    _seed_submissao(
        db_session,
        tcc_id=tcc_artigo.id,
        aluno_id=aluno_artigo.id,
        tipo_tcc=TipoTCC.ARTIGO,
        etapa="Artigo Final",
        versao=1,
        nome_arquivo="artigo.pdf",
        foi_aceito=True,
        nome_comprovante="aceite.pdf",
        nota_automatica=10,
    )

    service = SubmissaoService()
    historico_coordenador = service.listar_historico_coordenador(
        session=db_session,
        current_user=coordenador,
    )
    assert len(historico_coordenador) == 3
    assert {item.titulo_tcc for item in historico_coordenador} == {"Monografia com Versões", "Artigo Aceito"}
    assert {item.versao for item in historico_coordenador if item.tcc_id == tcc_mono.id} == {1, 2}
    assert any(item.fora_do_prazo for item in historico_coordenador if item.tcc_id == tcc_mono.id)
    assert any(item.nota_automatica == 10 for item in historico_coordenador if item.tcc_id == tcc_artigo.id)

    historico_orientador = service.listar_historico_orientador(
        session=db_session,
        current_user=orientador_mono,
    )
    assert len(historico_orientador) == 2
    assert {item.tcc_id for item in historico_orientador} == {tcc_mono.id}

    response = client.request(
        "GET",
        "/submissoes/historico",
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert {"titulo_tcc", "aluno_nome", "matricula", "nota_automatica"}.issubset(body[0])


def test_registrar_apresentacao_artigo_marks_existing_acceptance_and_logs(client, db_session) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Coord Logs Artigo",
        email="coord.logs.artigo@icomp.ufam.edu.br",
        username="coord.logs.artigo",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Apresentacao",
        email="aluno.apresentacao@icomp.ufam.edu.br",
        username="aluno.apresentacao",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Apresentacao",
        email="prof.apresentacao@icomp.ufam.edu.br",
        username="prof.apresentacao",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2027.1",
        data_inicio=(today - timedelta(days=10)).isoformat(),
        data_fim=(today + timedelta(days=120)).isoformat(),
        ativo=True,
    )
    tcc = _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Artigo com apresentacao",
        tipo_tcc=TipoTCC.ARTIGO,
        status=StatusTCC.EM_ANDAMENTO,
    )
    _seed_submissao(
        db_session,
        tcc_id=tcc.id,
        aluno_id=aluno.id,
        tipo_tcc=TipoTCC.ARTIGO,
        etapa="Artigo Final",
        versao=1,
        nome_arquivo="artigo-final.pdf",
        foi_aceito=True,
        nome_comprovante="aceite.pdf",
        nota_automatica=10,
    )

    response = client.post(
        "/submissoes/apresentacao-artigo",
        json={"data_apresentacao": today.isoformat()},
        headers=_build_auth_headers(user_id=aluno.id, perfil=aluno.perfil),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tcc_id"] == tcc.id
    assert body["artigo_ja_aceito"] is True

    list_response = client.request(
        "GET",
        "/submissoes/apresentacao-artigo",
        headers=_build_auth_headers(user_id=aluno.id, perfil=aluno.perfil),
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    coordinator_logs_response = client.request(
        "GET",
        "/logs",
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )
    assert coordinator_logs_response.status_code == 403

    admin = _seed_user(
        db_session,
        nome_completo="Admin Logs",
        email="admin.logs@icomp.ufam.edu.br",
        username="admin.logs",
        perfil=Perfil.ADMIN,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    logs_response = client.request(
        "GET",
        "/logs",
        headers=_build_auth_headers(user_id=admin.id, perfil=admin.perfil),
    )
    assert logs_response.status_code == 200
    assert any(log["acao"] == "REGISTRO_APRESENTACAO_ARTIGO" for log in logs_response.json())


def test_list_submissoes_atrasadas_returns_deadline_delta(client, db_session) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Coord Atrasos",
        email="coord.atrasos@icomp.ufam.edu.br",
        username="coord.atrasos",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Atrasado",
        email="aluno.atrasado@icomp.ufam.edu.br",
        username="aluno.atrasado",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2027000001",
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Atrasos",
        email="prof.atrasos@icomp.ufam.edu.br",
        username="prof.atrasos",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2027.2",
        data_inicio=(today - timedelta(days=30)).isoformat(),
        data_fim=(today + timedelta(days=90)).isoformat(),
        ativo=True,
        prazos=[("1ª Entrega", (today - timedelta(days=4)).isoformat(), TipoTCC.MONOGRAFIA)],
    )
    tcc = _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Monografia atrasada",
        tipo_tcc=TipoTCC.MONOGRAFIA,
        status=StatusTCC.EM_ANDAMENTO,
    )
    submissao = _seed_submissao(
        db_session,
        tcc_id=tcc.id,
        aluno_id=aluno.id,
        tipo_tcc=TipoTCC.MONOGRAFIA,
        etapa="1ª Entrega",
        versao=1,
        nome_arquivo="mono-atrasada.pdf",
        fora_do_prazo=True,
    )

    response = client.request(
        "GET",
        "/submissoes/atrasadas",
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == submissao.id
    assert body[0]["aluno_nome"] == aluno.nome_completo
    assert body[0]["matricula"] == aluno.matricula
    assert body[0]["data_limite"] == (today - timedelta(days=4)).isoformat()
    assert body[0]["dias_atraso"] >= 4

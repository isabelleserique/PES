from __future__ import annotations

import asyncio
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from backend.app.core.config import get_settings
from backend.app.db.models import SubmissaoEntregavelRecord
from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import StatusTCC
from backend.app.models.user import Perfil, StatusCadastro
from backend.app.services.submissao_service import COMPROVANTE_REQUIRED_DETAIL, SubmissaoService
from backend.tests.test_tcc import _seed_periodo, _seed_tcc, _seed_user


def _build_upload(filename: str, content: bytes, content_type: str = "application/pdf") -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        headers=Headers({"content-type": content_type}),
    )


def test_submeter_artigo_persists_files_and_returns_auto_grade(db_session, tmp_path) -> None:
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
            etapa=None,
            arquivo=_build_upload("artigo.pdf", b"%PDF-1.4"),
            foi_aceito=True,
            comprovante=_build_upload("aceite.pdf", b"%PDF-proof"),
        )
    )

    assert response.versao == 1
    assert response.nota_automatica == 10

    stored = db_session.query(SubmissaoEntregavelRecord).one()
    assert stored.aluno_id == aluno.id
    assert stored.tipo_tcc == TipoTCC.ARTIGO
    assert stored.etapa == "Artigo Científico"
    assert stored.nome_arquivo == "artigo.pdf"
    assert stored.nome_comprovante == "aceite.pdf"
    assert stored.foi_aceito is True
    assert stored.fora_do_prazo is True
    assert stored.nota_automatica == 10
    assert tmp_path in Path(stored.caminho_arquivo).parents
    assert stored.caminho_comprovante is not None

    history = service.listar_entregaveis(session=db_session, current_user=aluno)
    assert len(history) == 1
    assert history[0].id == stored.id


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
                etapa=None,
                arquivo=_build_upload("artigo.pdf", b"%PDF-1.4"),
                foi_aceito=True,
                comprovante=None,
            )
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == COMPROVANTE_REQUIRED_DETAIL


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

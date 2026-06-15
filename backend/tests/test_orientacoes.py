from __future__ import annotations

from datetime import date, timedelta

from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import StatusTCC
from backend.app.models.user import Perfil, StatusCadastro
from backend.tests.test_tcc import _build_auth_headers, _seed_periodo, _seed_tcc, _seed_user


def test_orientador_registers_session_and_student_can_view_it(client, db_session) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Sessao",
        email="aluno.sessao@icomp.ufam.edu.br",
        username="aluno.sessao",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Sessao",
        email="prof.sessao@icomp.ufam.edu.br",
        username="prof.sessao",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2028.1",
        data_inicio=(today - timedelta(days=15)).isoformat(),
        data_fim=(today + timedelta(days=90)).isoformat(),
        ativo=True,
    )
    tcc = _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="TCC com sessoes",
        tipo_tcc=TipoTCC.MONOGRAFIA,
        status=StatusTCC.EM_ANDAMENTO,
    )

    response = client.post(
        "/orientacoes/sessoes",
        json={
            "aluno_id": aluno.id,
            "data_sessao": today.isoformat(),
            "resumo": "Revisamos o andamento da fundamentacao teorica.",
            "proximos_passos": "Enviar nova versao com referencias atualizadas.",
        },
        headers=_build_auth_headers(user_id=orientador.id, perfil=orientador.perfil),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tcc_id"] == tcc.id
    assert body["aluno_nome"] == aluno.nome_completo
    assert body["orientador_nome"] == orientador.nome_completo

    orientador_list_response = client.request(
        "GET",
        f"/orientacoes/sessoes?aluno_id={aluno.id}",
        headers=_build_auth_headers(user_id=orientador.id, perfil=orientador.perfil),
    )
    assert orientador_list_response.status_code == 200
    assert orientador_list_response.json()[0]["id"] == body["id"]

    aluno_list_response = client.request(
        "GET",
        "/tcc/me/sessoes",
        headers=_build_auth_headers(user_id=aluno.id, perfil=aluno.perfil),
    )
    assert aluno_list_response.status_code == 200
    assert aluno_list_response.json()[0]["id"] == body["id"]


def test_orientador_cannot_register_session_for_other_professors_student(client, db_session) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Outro Orientador",
        email="aluno.outro.orientador@icomp.ufam.edu.br",
        username="aluno.outro.orientador",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador_correto = _seed_user(
        db_session,
        nome_completo="Prof. Correto",
        email="prof.correto@icomp.ufam.edu.br",
        username="prof.correto",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    orientador_sem_acesso = _seed_user(
        db_session,
        nome_completo="Prof. Sem Sessao",
        email="prof.sem.sessao@icomp.ufam.edu.br",
        username="prof.sem.sessao",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2028.2",
        data_inicio=(today - timedelta(days=15)).isoformat(),
        data_fim=(today + timedelta(days=90)).isoformat(),
        ativo=True,
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador_correto.id,
        titulo="TCC protegido",
        tipo_tcc=TipoTCC.ARTIGO,
        status=StatusTCC.EM_ANDAMENTO,
    )

    response = client.post(
        "/orientacoes/sessoes",
        json={
            "aluno_id": aluno.id,
            "data_sessao": today.isoformat(),
            "resumo": "Tentativa indevida de registro de sessao.",
            "proximos_passos": "Nao deve ser persistido pelo sistema.",
        },
        headers=_build_auth_headers(user_id=orientador_sem_acesso.id, perfil=orientador_sem_acesso.perfil),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Orientando nao encontrado para este orientador."

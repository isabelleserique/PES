from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import pytest

from backend.app.core.config import get_settings
from backend.app.core.security import create_access_token, hash_password
from backend.app.db.models import PeriodoLetivoRecord, PrazoEtapaRecord, TCCRecord, UserRecord
from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import StatusTCC
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


def test_create_periodo_returns_201_with_prazos_and_active_status(client, db_session) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="maria.coord@icomp.ufam.edu.br",
        username="maria.coord",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )

    response = client.post(
        "/periodos",
        json={
            "nome": "2025.1",
            "data_inicio": "2025-03-01",
            "data_fim": "2025-07-30",
            "ativo": True,
            "prazos": [
                {
                    "nome_etapa": "Aceite do Orientador",
                    "data_limite": "2025-03-20",
                    "tipo_tcc": "Todos",
                },
                {
                    "nome_etapa": "Definicao de Tema/Orientador",
                    "data_limite": "2025-03-10",
                    "tipo_tcc": "Artigo",
                },
            ],
        },
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["nome"] == "2025.1"
    assert body["ativo"] is True
    assert body["prazos"][0]["nome_etapa"] == "Definicao de Tema/Orientador"
    assert body["prazos"][1]["nome_etapa"] == "Aceite do Orientador"

    stored_periodo = db_session.query(PeriodoLetivoRecord).filter_by(nome="2025.1").one()
    assert stored_periodo.ativo is True
    assert stored_periodo.data_inicio.isoformat() == "2025-03-01"
    assert stored_periodo.data_fim.isoformat() == "2025-07-30"
    assert len(stored_periodo.prazos) == 2


def test_create_periodo_returns_409_when_dates_overlap_existing_period(client, db_session) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="coordenadora@icomp.ufam.edu.br",
        username="coord.icomp",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    _seed_periodo(
        db_session,
        nome="2025.1",
        data_inicio="2025-03-01",
        data_fim="2025-07-30",
        ativo=True,
    )

    response = client.post(
        "/periodos",
        json={
            "nome": "2025.2",
            "data_inicio": "2025-07-15",
            "data_fim": "2025-11-30",
            "ativo": False,
            "prazos": [],
        },
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Ja existe um periodo letivo configurado para o intervalo informado."


def test_create_periodo_returns_409_when_other_active_period_exists(client, db_session) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="coordenadora2@icomp.ufam.edu.br",
        username="coord2.icomp",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    _seed_periodo(
        db_session,
        nome="2025.1",
        data_inicio="2025-03-01",
        data_fim="2025-07-30",
        ativo=True,
    )

    response = client.post(
        "/periodos",
        json={
            "nome": "2025.2",
            "data_inicio": "2025-08-01",
            "data_fim": "2025-12-20",
            "ativo": True,
            "prazos": [],
        },
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Ja existe um periodo letivo ativo."


def test_create_periodo_returns_422_when_prazo_is_outside_period_range(client, db_session) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="coordenadora3@icomp.ufam.edu.br",
        username="coord3.icomp",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )

    response = client.post(
        "/periodos",
        json={
            "nome": "2025.1",
            "data_inicio": "2025-03-01",
            "data_fim": "2025-07-30",
            "ativo": True,
            "prazos": [
                {
                    "nome_etapa": "Entrega Final",
                    "data_limite": "2025-08-01",
                    "tipo_tcc": "Monografia",
                }
            ],
        },
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )

    assert response.status_code == 422
    assert "Todos os prazos devem estar entre a data de inicio e a data de fim do periodo." in response.body.decode(
        "utf-8"
    )


def test_list_periodos_returns_history_for_coordenador(client, db_session) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="historico@icomp.ufam.edu.br",
        username="historico.coord",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    _seed_periodo(
        db_session,
        nome="2025.1",
        data_inicio="2025-03-01",
        data_fim="2025-07-30",
        ativo=False,
        prazos=[("Entrega Final", "2025-07-20", TipoTCC.TODOS)],
    )
    _seed_periodo(
        db_session,
        nome="2025.2",
        data_inicio="2025-08-01",
        data_fim="2025-12-20",
        ativo=True,
        prazos=[("Aceite do Orientador", "2025-08-15", TipoTCC.ARTIGO)],
    )

    response = client.request(
        "GET",
        "/periodos",
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )

    assert response.status_code == 200
    body = response.json()
    assert [periodo["nome"] for periodo in body] == ["2025.2", "2025.1"]
    assert body[0]["prazos"][0]["tipo_tcc"] == "Artigo"
    assert body[1]["ativo"] is False


def test_get_active_periodo_returns_current_period_for_authenticated_user(client, db_session) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Ativo",
        email="aluno.ativo@icomp.ufam.edu.br",
        username="aluno.ativo",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123001",
    )
    _seed_periodo(
        db_session,
        nome="2025.2",
        data_inicio="2025-08-01",
        data_fim="2025-12-20",
        ativo=True,
        prazos=[
            ("Definicao de Tema/Orientador", "2025-08-10", TipoTCC.TODOS),
            ("Entrega Final", "2025-12-10", TipoTCC.MONOGRAFIA),
        ],
    )

    response = client.request(
        "GET",
        "/periodos/ativo",
        headers=_build_auth_headers(user_id=aluno.id, perfil=aluno.perfil),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["nome"] == "2025.2"
    assert len(body["prazos"]) == 2


def test_update_periodo_allows_changes_while_period_is_active(client, db_session) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="edicao@icomp.ufam.edu.br",
        username="edicao.coord",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    periodo = _seed_periodo(
        db_session,
        nome="2025.2",
        data_inicio="2025-08-01",
        data_fim="2025-12-20",
        ativo=True,
        prazos=[("Aceite do Orientador", "2025-08-15", TipoTCC.TODOS)],
    )

    response = client.patch(
        f"/periodos/{periodo.id}",
        json={
            "nome": "2025.2 - Ajustado",
            "data_fim": "2025-12-22",
            "ativo": False,
            "prazos": [
                {
                    "nome_etapa": "Aceite do Orientador",
                    "data_limite": "2025-08-18",
                    "tipo_tcc": "Todos",
                },
                {
                    "nome_etapa": "Entrega Final",
                    "data_limite": "2025-12-15",
                    "tipo_tcc": "Monografia",
                },
            ],
        },
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["nome"] == "2025.2 - Ajustado"
    assert body["data_fim"] == "2025-12-22"
    assert body["ativo"] is False
    assert [prazo["nome_etapa"] for prazo in body["prazos"]] == ["Aceite do Orientador", "Entrega Final"]

    db_session.refresh(periodo)
    assert periodo.nome == "2025.2 - Ajustado"
    assert periodo.ativo is False
    assert periodo.data_fim.isoformat() == "2025-12-22"
    assert len(periodo.prazos) == 2


def test_update_periodo_returns_409_for_inactive_period(client, db_session) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="inativo@icomp.ufam.edu.br",
        username="inativo.coord",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    periodo = _seed_periodo(
        db_session,
        nome="2024.2",
        data_inicio="2024-08-01",
        data_fim="2024-12-20",
        ativo=False,
    )

    response = client.patch(
        f"/periodos/{periodo.id}",
        json={"nome": "2024.2 - Revisado"},
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Apenas periodos ativos podem ser editados."


def test_periodos_management_requires_coordenador_profile(client, db_session) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Ativo",
        email="aluno.sem.permissao@icomp.ufam.edu.br",
        username="aluno.sem.permissao",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123010",
    )

    response = client.post(
        "/periodos",
        json={
            "nome": "2025.1",
            "data_inicio": "2025-03-01",
            "data_fim": "2025-07-30",
            "ativo": True,
            "prazos": [],
        },
        headers=_build_auth_headers(user_id=aluno.id, perfil=aluno.perfil),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Perfil sem permissao para acessar este recurso."


def test_update_periodo_returns_422_when_request_has_no_changes(client, db_session) -> None:
    coordenador = _seed_user(
        db_session,
        nome_completo="Maria Coordenadora",
        email="sem.alteracao@icomp.ufam.edu.br",
        username="sem.alteracao.coord",
        perfil=Perfil.COORDENADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    periodo = _seed_periodo(
        db_session,
        nome="2025.2",
        data_inicio="2025-08-01",
        data_fim="2025-12-20",
        ativo=True,
    )

    response = client.patch(
        f"/periodos/{periodo.id}",
        json={},
        headers=_build_auth_headers(user_id=coordenador.id, perfil=coordenador.perfil),
    )

    assert response.status_code == 422
    assert "Informe ao menos um campo para atualizacao." in response.body.decode("utf-8")


def test_get_active_cronograma_filters_student_prazos_by_tcc_type_and_computes_status(client, db_session) -> None:
    aluno = _seed_user(
        db_session,
        nome_completo="Aluno Cronograma",
        email="aluno.cronograma@icomp.ufam.edu.br",
        username="aluno.cronograma",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123011",
    )
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Cronograma",
        email="prof.cronograma@icomp.ufam.edu.br",
        username="prof.cronograma",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=30)).isoformat(),
        data_fim=(today + timedelta(days=45)).isoformat(),
        ativo=True,
        prazos=[
            ("Definicao de Tema/Orientador", (today + timedelta(days=12)).isoformat(), TipoTCC.TODOS),
            ("Entrega Parcial", (today + timedelta(days=3)).isoformat(), TipoTCC.ARTIGO),
            ("Entrega Final", (today - timedelta(days=2)).isoformat(), TipoTCC.MONOGRAFIA),
        ],
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno.id,
        orientador_id=orientador.id,
        titulo="Planejamento de IA",
        tipo_tcc=TipoTCC.ARTIGO,
    )

    response = client.request(
        "GET",
        "/periodos/ativo/cronograma",
        headers=_build_auth_headers(user_id=aluno.id, perfil=aluno.perfil),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["perfil"] == "ALUNO"
    assert body["aluno"]["tipo_tcc"] == "Artigo"
    assert [prazo["nome_etapa"] for prazo in body["aluno"]["prazos"]] == [
        "Entrega Parcial",
        "Definicao de Tema/Orientador",
    ]
    assert body["aluno"]["prazos"][0]["status"] == "PROXIMO"
    assert body["aluno"]["prazos"][0]["cor"] == "amarelo"
    assert body["aluno"]["prazos"][1]["status"] == "A_VENCER"
    assert body["aluno"]["alerta_prazo"] is None


def test_get_active_cronograma_returns_orientador_view_grouped_by_orientandos_and_filter(client, db_session) -> None:
    orientador = _seed_user(
        db_session,
        nome_completo="Prof. Orientador",
        email="orientador.cronograma@icomp.ufam.edu.br",
        username="orientador.cronograma",
        perfil=Perfil.ORIENTADOR,
        status=StatusCadastro.ATIVO,
        ativo=True,
    )
    aluno_artigo = _seed_user(
        db_session,
        nome_completo="Aluno Artigo",
        email="aluno.artigo@icomp.ufam.edu.br",
        username="aluno.artigo",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123012",
    )
    aluno_relatorio = _seed_user(
        db_session,
        nome_completo="Aluno Relatorio",
        email="aluno.relatorio@icomp.ufam.edu.br",
        username="aluno.relatorio",
        perfil=Perfil.ALUNO,
        status=StatusCadastro.ATIVO,
        ativo=True,
        matricula="2023123013",
    )
    today = date.today()
    periodo = _seed_periodo(
        db_session,
        nome="2026.1",
        data_inicio=(today - timedelta(days=15)).isoformat(),
        data_fim=(today + timedelta(days=60)).isoformat(),
        ativo=True,
        prazos=[
            ("Definicao de Tema/Orientador", (today - timedelta(days=1)).isoformat(), TipoTCC.TODOS),
            ("Entrega Parcial", (today + timedelta(days=5)).isoformat(), TipoTCC.ARTIGO),
            ("Seminario Final", (today + timedelta(days=8)).isoformat(), TipoTCC.RELATORIO_ESTAGIO),
        ],
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno_artigo.id,
        orientador_id=orientador.id,
        titulo="Agentes para Educacao",
        tipo_tcc=TipoTCC.ARTIGO,
        prazo_excedido=True,
    )
    _seed_tcc(
        db_session,
        periodo_id=periodo.id,
        aluno_id=aluno_relatorio.id,
        orientador_id=orientador.id,
        titulo="Relatorio de Estagio em Dados",
        tipo_tcc=TipoTCC.RELATORIO_ESTAGIO,
    )

    response = client.request(
        "GET",
        f"/periodos/ativo/cronograma?orientando_id={aluno_artigo.id}",
        headers=_build_auth_headers(user_id=orientador.id, perfil=orientador.perfil),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["perfil"] == "ORIENTADOR"
    assert body["filtro_orientando_id"] == aluno_artigo.id
    assert len(body["orientandos"]) == 1
    assert body["orientandos"][0]["aluno_nome"] == aluno_artigo.nome_completo
    assert body["orientandos"][0]["papel_orientacao"] == "ORIENTADOR"
    assert body["orientandos"][0]["alerta_prazo"] is not None
    assert [prazo["nome_etapa"] for prazo in body["orientandos"][0]["prazos"]] == [
        "Definicao de Tema/Orientador",
        "Entrega Parcial",
    ]

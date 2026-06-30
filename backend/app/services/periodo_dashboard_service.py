from __future__ import annotations

import unicodedata
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models import PeriodoLetivoRecord, TCCRecord, UserRecord
from backend.app.models.deposito import StatusDeposito
from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import StatusTCC
from backend.app.models.user import Perfil, StatusCadastro
from backend.app.schemas.dashboard import (
    DashboardAlunoDetalhe,
    DashboardAlunosResumo,
    DashboardDepositoBiblioteca,
    DashboardPeriodoResumo,
    DashboardTipoTccResumo,
    PeriodoDashboardResponse,
)

NO_ACTIVE_PERIODO_FOUND_DETAIL = "Nenhum periodo letivo ativo encontrado."

class PeriodoDashboardService:
    def get_dashboard(self, *, session: Session) -> PeriodoDashboardResponse:
        periodo = self._get_active_periodo(session=session)
        alunos = session.scalars(
            select(UserRecord)
            .where(
                UserRecord.perfil == Perfil.ALUNO,
                UserRecord.status == StatusCadastro.ATIVO,
                UserRecord.ativo.is_(True),
            )
            .order_by(UserRecord.nome_completo.asc())
        ).all()
        tccs = session.scalars(
            select(TCCRecord)
            .options(
                selectinload(TCCRecord.submissoes_entregaveis),
                selectinload(TCCRecord.deposito_final),
            )
            .where(TCCRecord.periodo_id == periodo.id)
        ).all()
        tcc_by_aluno = {tcc.aluno_id: tcc for tcc in tccs}
        orientadores = self._load_orientadores(session=session, tccs=tccs)

        detalhes = [
            self._build_aluno_detalhe(
                aluno=aluno,
                tcc=tcc_by_aluno.get(aluno.id),
                periodo=periodo,
                orientadores=orientadores,
            )
            for aluno in alunos
        ]

        return PeriodoDashboardResponse(
            periodo=DashboardPeriodoResumo(
                id=periodo.id,
                nome=periodo.nome,
                data_inicio=periodo.data_inicio,
                data_fim=periodo.data_fim,
            ),
            alunos=self._build_resumo(alunos=alunos, tccs=tccs, detalhes=detalhes),
            alunos_detalhados=detalhes,
        )

    def _get_active_periodo(self, *, session: Session) -> PeriodoLetivoRecord:
        periodo = session.scalar(
            select(PeriodoLetivoRecord)
            .options(selectinload(PeriodoLetivoRecord.prazos))
            .where(PeriodoLetivoRecord.ativo.is_(True))
            .order_by(PeriodoLetivoRecord.data_inicio.desc())
        )
        if periodo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_ACTIVE_PERIODO_FOUND_DETAIL)
        return periodo

    def _load_orientadores(self, *, session: Session, tccs: list[TCCRecord]) -> dict[str, UserRecord]:
        orientador_ids = {tcc.orientador_id for tcc in tccs if tcc.orientador_id}
        if not orientador_ids:
            return {}
        orientadores = session.scalars(select(UserRecord).where(UserRecord.id.in_(orientador_ids))).all()
        return {orientador.id: orientador for orientador in orientadores}

    def _build_resumo(
        self,
        *,
        alunos: list[UserRecord],
        tccs: list[TCCRecord],
        detalhes: list[DashboardAlunoDetalhe],
    ) -> DashboardAlunosResumo:
        tipo_counts = DashboardTipoTccResumo(
            monografia=sum(1 for tcc in tccs if tcc.tipo_tcc == TipoTCC.MONOGRAFIA),
            artigo=sum(1 for tcc in tccs if tcc.tipo_tcc == TipoTCC.ARTIGO),
            relatorio_estagio=sum(1 for tcc in tccs if tcc.tipo_tcc == TipoTCC.RELATORIO_ESTAGIO),
            sem_tcc=max(len(alunos) - len(tccs), 0),
        )
        depositados = sum(1 for detalhe in detalhes if detalhe.deposito_biblioteca == StatusDeposito.DEPOSITADO.value)
        return DashboardAlunosResumo(
            total=len(alunos),
            por_tipo=tipo_counts,
            sem_orientador_aceito=sum(1 for detalhe in detalhes if detalhe.sem_orientador_aceito),
            com_prazo_vencido_sem_entrega=sum(1 for detalhe in detalhes if detalhe.prazos_vencidos_sem_entrega > 0),
            deposito_biblioteca=DashboardDepositoBiblioteca(
                depositados=depositados,
                pendentes=max(len(tccs) - depositados, 0),
            ),
        )

    def _build_aluno_detalhe(
        self,
        *,
        aluno: UserRecord,
        tcc: TCCRecord | None,
        periodo: PeriodoLetivoRecord,
        orientadores: dict[str, UserRecord],
    ) -> DashboardAlunoDetalhe:
        if tcc is None:
            return DashboardAlunoDetalhe(
                aluno_id=aluno.id,
                nome=aluno.nome_completo,
                matricula=aluno.matricula,
                status_tcc="SEM_TCC",
                sem_orientador_aceito=True,
                prazos_vencidos_sem_entrega=0,
                entregas_pendentes=0,
                deposito_biblioteca="SEM_TCC",
            )

        pendentes, vencidos = self._count_pending_deadlines(tcc=tcc, periodo=periodo)
        orientador = orientadores.get(tcc.orientador_id)
        return DashboardAlunoDetalhe(
            aluno_id=aluno.id,
            nome=aluno.nome_completo,
            matricula=aluno.matricula,
            titulo_tcc=tcc.titulo,
            tipo_tcc=tcc.tipo_tcc.value,
            status_tcc=tcc.status.value,
            orientador_nome=orientador.nome_completo if orientador else None,
            sem_orientador_aceito=tcc.status != StatusTCC.EM_ANDAMENTO and tcc.status != StatusTCC.APROVADO,
            prazos_vencidos_sem_entrega=vencidos,
            entregas_pendentes=pendentes,
            deposito_biblioteca=self._get_deposito_status(tcc),
        )

    def _count_pending_deadlines(self, *, tcc: TCCRecord, periodo: PeriodoLetivoRecord) -> tuple[int, int]:
        pendentes = 0
        vencidos = 0
        hoje = date.today()

        for prazo in periodo.prazos:
            if prazo.tipo_tcc not in {TipoTCC.TODOS, tcc.tipo_tcc}:
                continue
            if self._has_submission_for_deadline(tcc=tcc, etapa=prazo.nome_etapa):
                continue

            pendentes += 1
            if prazo.data_limite < hoje:
                vencidos += 1

        return pendentes, vencidos

    def _has_submission_for_deadline(self, *, tcc: TCCRecord, etapa: str) -> bool:
        etapa_normalizada = self._normalize_text(etapa)
        return any(
            self._deadline_matches_etapa(submissao.etapa, etapa_normalizada)
            for submissao in tcc.submissoes_entregaveis
        )

    def _get_deposito_status(self, tcc: TCCRecord) -> str:
        if tcc.deposito_final is None:
            return StatusDeposito.AGUARDANDO_ENVIO.value
        return tcc.deposito_final.status.value

    def _deadline_matches_etapa(self, nome_etapa: str, etapa_normalizada: str) -> bool:
        nome_normalizado = self._normalize_text(nome_etapa)
        if "artigo" in etapa_normalizada and "artigo" in nome_normalizado:
            return True
        return etapa_normalizada in nome_normalizado or nome_normalizado in etapa_normalizada

    def _normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.strip().casefold())
        without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
        return " ".join(without_accents.split())


async def get_periodo_dashboard_service() -> PeriodoDashboardService:
    return PeriodoDashboardService()

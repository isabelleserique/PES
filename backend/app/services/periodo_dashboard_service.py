from sqlalchemy import select, func, exists
from sqlalchemy.orm import Session

from datetime import date

from backend.app.db.models import (
    TCCRecord,
    UserRecord,
    SubmissaoEntregavelRecord,
    PeriodoLetivoRecord,
    PrazoEtapaRecord,
)
from backend.app.models.tcc import StatusTCC
from backend.app.models.user import Perfil

class PeriodoDashboardService:

    def get_dashboard(self, *, session: Session) -> dict:
        periodo = self._get_active_periodo(session=session)

        total_alunos = self._count_alunos(
            session=session,
            periodo_id=periodo.id
        )
        por_tipo = self._count_by_tipo_tcc(session=session, periodo_id=periodo.id)
        sem_orientador = self._count_sem_orientador(session=session, periodo_id=periodo.id)
        artigos_aceitos = self._count_artigos_aceitos(session=session, periodo_id=periodo.id)

        prazos_vencidos, entregas_pendentes = self._count_pendencias(
            session=session,
            periodo_id=periodo.id
        )

        biblioteca_status = self._get_biblioteca_status_base()

        return {
            "periodo": {
                "id": periodo.id,
                "nome": periodo.nome,
                "data_inicio": periodo.data_inicio,
                "data_fim": periodo.data_fim,
            },
            "alunos": {
                "total": total_alunos,
                "por_tipo_tcc": por_tipo,
                "sem_orientador": sem_orientador,
            },
            "status_tcc": {
                "artigos_aceitos": artigos_aceitos,
            },
            "prazos": {
                "vencidos": prazos_vencidos,
            },
            "entregas": {
                "pendentes": entregas_pendentes,
            },
            "alunos_detalhados": self._build_alunos_detalhados(
                session=session,
                periodo_id=periodo.id,
            ),
        }

    def _get_active_periodo(self, *, session: Session) -> PeriodoLetivoRecord:
        periodo = session.scalar(
            select(PeriodoLetivoRecord).where(
                PeriodoLetivoRecord.ativo.is_(True)
            )
        )
        if not periodo:
            raise Exception("Nenhum periodo ativo encontrado")
        return periodo

    def _count_alunos(self, *, session: Session, periodo_id: str) -> int:
        return session.scalar(
            select(func.count(func.distinct(TCCRecord.aluno_id))).where(
                TCCRecord.periodo_id == periodo_id
            )
        ) or 0

    def _count_by_tipo_tcc(self, *, session: Session, periodo_id: str) -> dict:
        rows = session.execute(
            select(TCCRecord.tipo_tcc, func.count(TCCRecord.id))
            .where(TCCRecord.periodo_id == periodo_id)
            .group_by(TCCRecord.tipo_tcc)
        ).all()

        return {str(tipo): count for tipo, count in rows}

    def _count_sem_orientador(self, *, session: Session, periodo_id: str) -> int:
        return session.scalar(
            select(func.count(TCCRecord.id)).where(
                TCCRecord.periodo_id == periodo_id,
                TCCRecord.orientador_id.is_(None),
            )
        ) or 0

    def _count_artigos_aceitos(self, *, session: Session, periodo_id: str) -> int:
        return session.scalar(
            select(func.count(TCCRecord.id)).where(
                TCCRecord.periodo_id == periodo_id,
                TCCRecord.status == StatusTCC.APROVADO,
            )
        ) or 0

    def _count_pendencias(self, *, session: Session, periodo_id: str) -> tuple[int, int]:
        hoje = date.today()

        tccs = (
            select(
                TCCRecord.id.label("tcc_id"),
                TCCRecord.tipo_tcc.label("tipo_tcc"),
            )
            .where(TCCRecord.periodo_id == periodo_id)
            .subquery()
        )

        etapas = (
            select(
                PrazoEtapaRecord.nome_etapa,
                PrazoEtapaRecord.tipo_tcc,
                PrazoEtapaRecord.data_limite,
            )
            .where(PrazoEtapaRecord.periodo_id == periodo_id)
            .subquery()
        )

        base = (
            select(
                tccs.c.tcc_id,
                etapas.c.nome_etapa,
                etapas.c.data_limite,
            )
            .select_from(
                tccs.join(etapas, etapas.c.tipo_tcc == tccs.c.tipo_tcc)
            )
            .subquery()
        )

        submissoes_ok = (
            select(
                SubmissaoEntregavelRecord.tcc_id,
                SubmissaoEntregavelRecord.etapa,
            )
            .where(SubmissaoEntregavelRecord.foi_aceito.is_(True))
            .distinct()
            .subquery()
        )

        pendencias = (
            select(base.c.tcc_id, base.c.data_limite)
            .where(
                ~exists(
                    select(1).where(
                        submissoes_ok.c.tcc_id == base.c.tcc_id,
                        submissoes_ok.c.etapa == base.c.nome_etapa,
                    )
                )
            )
            .subquery()
        )

        total_pendentes = session.scalar(
            select(func.count(func.distinct(pendencias.c.tcc_id)))
        ) or 0

        vencidos = session.scalar(
            select(func.count(func.distinct(pendencias.c.tcc_id))).where(
                pendencias.c.data_limite.is_not(None)
            ).where(
                pendencias.c.data_limite < hoje
            )
        ) or 0

        return vencidos, total_pendentes

    def _get_biblioteca_status_base(self) -> dict:
        """
        será implementado no futuro
        """
        return {
            "depositados": 0,
            "pendentes": 0,
            "status": "nao_implementado"
        }

    def _build_alunos_detalhados(self, *, session: Session, periodo_id: str) -> list[dict]:
        hoje = date.today()

        tccs = session.execute(
            select(
                TCCRecord.id,
                TCCRecord.aluno_id,
                TCCRecord.tipo_tcc,
                TCCRecord.status,
                TCCRecord.orientador_id,
            ).where(TCCRecord.periodo_id == periodo_id)
        ).all()

        if not tccs:
            return []

        tcc_ids = [t.id for t in tccs]

        alunos = session.execute(
            select(UserRecord.id, UserRecord.nome_completo)
            .where(UserRecord.id.in_([t.aluno_id for t in tccs]))
        ).all()

        alunos_map = {a.id: a.nome_completo for a in alunos}

        submissoes = session.execute(
            select(
                SubmissaoEntregavelRecord.tcc_id,
                SubmissaoEntregavelRecord.etapa,
            ).where(
                SubmissaoEntregavelRecord.tcc_id.in_(tcc_ids),
                SubmissaoEntregavelRecord.foi_aceito.is_(True),
            )
        ).all()

        entregas_ok = {(s.tcc_id, s.etapa) for s in submissoes}

        prazos = session.execute(
            select(
                PrazoEtapaRecord.tipo_tcc,
                PrazoEtapaRecord.nome_etapa,
                PrazoEtapaRecord.data_limite,
            ).where(PrazoEtapaRecord.periodo_id == periodo_id)
        ).all()

        prazos_por_tipo = {}
        for p in prazos:
            prazos_por_tipo.setdefault(p.tipo_tcc, []).append(p)

        resultado = []

        for tcc in tccs:
            prazos_tipo = prazos_por_tipo.get(tcc.tipo_tcc, [])

            vencidos = 0
            pendentes = 0

            for p in prazos_tipo:
                chave = (tcc.id, p.nome_etapa)

                if chave not in entregas_ok:
                    pendentes += 1

                    if p.data_limite and p.data_limite < hoje:
                        vencidos += 1

            resultado.append({
                "aluno_id": tcc.aluno_id,
                "nome": alunos_map.get(tcc.aluno_id, ""),
                "tipo_tcc": tcc.tipo_tcc.value if hasattr(tcc.tipo_tcc, "value") else str(tcc.tipo_tcc),
                "tem_orientador": tcc.orientador_id is not None,
                "status_tcc": tcc.status.value if hasattr(tcc.status, "value") else str(tcc.status),
                "prazos_vencidos": vencidos,
                "entregas_pendentes": pendentes,
            })

        return resultado

    
async def get_periodo_dashboard_service() -> PeriodoDashboardService:
    return PeriodoDashboardService()
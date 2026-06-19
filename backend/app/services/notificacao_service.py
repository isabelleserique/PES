from __future__ import annotations

import asyncio
import unicodedata
from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from backend.app.core.config import get_settings
from backend.app.db.models import NotificacaoPrazoRecord, PeriodoLetivoRecord, TCCRecord, UserRecord
from backend.app.db.session import SessionLocal
from backend.app.models.periodo import TipoTCC
from backend.app.models.user import StatusCadastro
from backend.app.schemas.notificacao import NotificacaoPrazoResultado
from backend.app.services.audit_service import AuditService
from backend.app.services.email_service import EmailService

ALERT_DAYS_BEFORE_DEADLINE = 3


class NotificacaoPrazoService:
    def processar_alertas_prazos(
        self,
        *,
        session: Session,
        email_service: EmailService,
        reference_date: date | None = None,
    ) -> NotificacaoPrazoResultado:
        hoje = reference_date or date.today()
        periodo = session.scalar(
            select(PeriodoLetivoRecord)
            .options(selectinload(PeriodoLetivoRecord.prazos))
            .where(PeriodoLetivoRecord.ativo.is_(True))
            .order_by(PeriodoLetivoRecord.data_inicio.desc())
        )
        if periodo is None:
            return NotificacaoPrazoResultado()

        tccs = session.scalars(
            select(TCCRecord)
            .options(selectinload(TCCRecord.submissoes_entregaveis))
            .where(TCCRecord.periodo_id == periodo.id)
        ).all()
        alunos = self._load_alunos(session=session, tccs=tccs)
        resultado = NotificacaoPrazoResultado()

        for tcc in tccs:
            aluno = alunos.get(tcc.aluno_id)
            if aluno is None:
                continue

            for prazo in periodo.prazos:
                if prazo.tipo_tcc not in {TipoTCC.TODOS, tcc.tipo_tcc}:
                    continue
                if self._has_submission_for_deadline(tcc=tcc, etapa=prazo.nome_etapa):
                    continue

                tipo_alerta = self._resolve_tipo_alerta(data_limite=prazo.data_limite, reference_date=hoje)
                if tipo_alerta is None:
                    continue

                resultado.avaliadas += 1
                if self._notification_already_sent(
                    session=session,
                    tcc_id=tcc.id,
                    prazo_id=prazo.id,
                    tipo_alerta=tipo_alerta,
                ):
                    resultado.ignoradas += 1
                    continue

                sent = email_service.send_deadline_notification(
                    to_email=aluno.email,
                    aluno_nome=aluno.nome_completo,
                    titulo=tcc.titulo,
                    etapa=prazo.nome_etapa,
                    data_limite=prazo.data_limite.isoformat(),
                    tipo_alerta=tipo_alerta,
                )
                if not sent:
                    resultado.ignoradas += 1
                    continue

                if self._record_notification(
                    session=session,
                    tcc_id=tcc.id,
                    aluno_id=aluno.id,
                    prazo_id=prazo.id,
                    tipo_alerta=tipo_alerta,
                ):
                    resultado.enviadas += 1
                    AuditService().log_event(
                        session=session,
                        user_id=aluno.id,
                        action="NOTIFICACAO_PRAZO",
                        entity="PRAZO",
                        description=f"Enviou alerta {tipo_alerta} para {prazo.nome_etapa}.",
                        data={"tcc_id": tcc.id, "prazo_id": prazo.id, "tipo_alerta": tipo_alerta},
                    )
                else:
                    resultado.ignoradas += 1

        return resultado

    def _load_alunos(self, *, session: Session, tccs: list[TCCRecord]) -> dict[str, UserRecord]:
        aluno_ids = {tcc.aluno_id for tcc in tccs}
        if not aluno_ids:
            return {}
        alunos = session.scalars(
            select(UserRecord).where(
                UserRecord.id.in_(aluno_ids),
                UserRecord.status == StatusCadastro.ATIVO,
                UserRecord.ativo.is_(True),
            )
        ).all()
        return {aluno.id: aluno for aluno in alunos}

    def _resolve_tipo_alerta(self, *, data_limite: date, reference_date: date) -> str | None:
        dias_restantes = (data_limite - reference_date).days
        if 0 < dias_restantes <= ALERT_DAYS_BEFORE_DEADLINE:
            return "A_VENCER"
        if dias_restantes == 0:
            return "VENCE_HOJE"
        if dias_restantes < 0:
            return "VENCIDO"
        return None

    def _notification_already_sent(
        self,
        *,
        session: Session,
        tcc_id: str,
        prazo_id: str,
        tipo_alerta: str,
    ) -> bool:
        return session.scalar(
            select(NotificacaoPrazoRecord.id).where(
                NotificacaoPrazoRecord.tcc_id == tcc_id,
                NotificacaoPrazoRecord.prazo_id == prazo_id,
                NotificacaoPrazoRecord.tipo_alerta == tipo_alerta,
            )
        ) is not None

    def _record_notification(
        self,
        *,
        session: Session,
        tcc_id: str,
        aluno_id: str,
        prazo_id: str,
        tipo_alerta: str,
    ) -> bool:
        session.add(
            NotificacaoPrazoRecord(
                id=str(uuid4()),
                tcc_id=tcc_id,
                aluno_id=aluno_id,
                prazo_id=prazo_id,
                tipo_alerta=tipo_alerta,
                canal="EMAIL",
            )
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return False
        return True

    def _has_submission_for_deadline(self, *, tcc: TCCRecord, etapa: str) -> bool:
        etapa_normalizada = self._normalize_text(etapa)
        return any(
            self._deadline_matches_etapa(submissao.etapa, etapa_normalizada)
            for submissao in tcc.submissoes_entregaveis
        )

    def _deadline_matches_etapa(self, nome_etapa: str, etapa_normalizada: str) -> bool:
        nome_normalizado = self._normalize_text(nome_etapa)
        if "artigo" in etapa_normalizada and "artigo" in nome_normalizado:
            return True
        return etapa_normalizada in nome_normalizado or nome_normalizado in etapa_normalizada

    def _normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.strip().casefold())
        without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
        return " ".join(without_accents.split())


async def get_notificacao_prazo_service() -> NotificacaoPrazoService:
    return NotificacaoPrazoService()


async def run_deadline_notification_loop(
    *,
    notificacao_service: NotificacaoPrazoService | None = None,
    notification_time: time = time(hour=11, minute=0),
) -> None:
    service = notificacao_service or NotificacaoPrazoService()
    while True:
        await asyncio.sleep(_seconds_until_next_run(notification_time))
        await asyncio.to_thread(_process_alerts_once, service)


def _process_alerts_once(service: NotificacaoPrazoService) -> None:
    with SessionLocal() as session:
        email_service = EmailService(get_settings())
        service.processar_alertas_prazos(session=session, email_service=email_service)


def _seconds_until_next_run(notification_time: time) -> float:
    now = datetime.now(UTC)
    next_run = now.replace(
        hour=notification_time.hour,
        minute=notification_time.minute,
        second=notification_time.second,
        microsecond=0,
    )
    if next_run <= now:
        next_run += timedelta(days=1)
    return (next_run - now).total_seconds()

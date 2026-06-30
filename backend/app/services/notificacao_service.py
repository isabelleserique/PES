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
        users = self._load_users(session=session, tccs=tccs)
        resultado = NotificacaoPrazoResultado()

        for tcc in tccs:
            aluno = users.get(tcc.aluno_id)
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

                self._process_student_notification(
                    session=session,
                    email_service=email_service,
                    resultado=resultado,
                    tcc=tcc,
                    aluno=aluno,
                    prazo_id=prazo.id,
                    etapa=prazo.nome_etapa,
                    data_limite=prazo.data_limite.isoformat(),
                    tipo_alerta=tipo_alerta,
                )
                for orientador_id in {tcc.orientador_id, tcc.coorientador_id} - {None}:
                    orientador = users.get(orientador_id)
                    if orientador is None or not orientador.email_prazos_orientandos:
                        continue
                    orientador_alerta = self._resolve_tipo_alerta(
                        data_limite=prazo.data_limite,
                        reference_date=hoje,
                        alert_days_before=orientador.notificacao_antecedencia_dias,
                    )
                    if orientador_alerta is None:
                        continue
                    self._process_advisor_notification(
                        session=session,
                        email_service=email_service,
                        resultado=resultado,
                        tcc=tcc,
                        aluno=aluno,
                        orientador=orientador,
                        prazo_id=prazo.id,
                        etapa=prazo.nome_etapa,
                        data_limite=prazo.data_limite.isoformat(),
                        tipo_alerta=orientador_alerta,
                    )

        return resultado

    def _load_users(self, *, session: Session, tccs: list[TCCRecord]) -> dict[str, UserRecord]:
        user_ids = {
            user_id
            for tcc in tccs
            for user_id in (tcc.aluno_id, tcc.orientador_id, tcc.coorientador_id)
            if user_id is not None
        }
        if not user_ids:
            return {}
        users = session.scalars(
            select(UserRecord).where(
                UserRecord.id.in_(user_ids),
                UserRecord.status == StatusCadastro.ATIVO,
                UserRecord.ativo.is_(True),
            )
        ).all()
        return {user.id: user for user in users}

    def _resolve_tipo_alerta(
        self,
        *,
        data_limite: date,
        reference_date: date,
        alert_days_before: int = ALERT_DAYS_BEFORE_DEADLINE,
    ) -> str | None:
        dias_restantes = (data_limite - reference_date).days
        if 0 < dias_restantes <= alert_days_before:
            return "A_VENCER"
        if dias_restantes == 0:
            return "VENCE_HOJE"
        if dias_restantes < 0:
            return "VENCIDO"
        return None

    def _process_student_notification(
        self,
        *,
        session: Session,
        email_service: EmailService,
        resultado: NotificacaoPrazoResultado,
        tcc: TCCRecord,
        aluno: UserRecord,
        prazo_id: str,
        etapa: str,
        data_limite: str,
        tipo_alerta: str,
    ) -> None:
        resultado.avaliadas += 1
        if self._notification_already_sent(
            session=session,
            tcc_id=tcc.id,
            prazo_id=prazo_id,
            tipo_alerta=tipo_alerta,
        ):
            resultado.ignoradas += 1
            return

        sent = email_service.send_deadline_notification(
            to_email=aluno.email,
            aluno_nome=aluno.nome_completo,
            titulo=tcc.titulo,
            etapa=etapa,
            data_limite=data_limite,
            tipo_alerta=tipo_alerta,
        )
        if not sent:
            resultado.ignoradas += 1
            return

        self._finalize_notification(
            session=session,
            resultado=resultado,
            tcc_id=tcc.id,
            user_id=aluno.id,
            prazo_id=prazo_id,
            tipo_alerta=tipo_alerta,
            description=f"Enviou alerta {tipo_alerta} para {etapa}.",
        )

    def _process_advisor_notification(
        self,
        *,
        session: Session,
        email_service: EmailService,
        resultado: NotificacaoPrazoResultado,
        tcc: TCCRecord,
        aluno: UserRecord,
        orientador: UserRecord,
        prazo_id: str,
        etapa: str,
        data_limite: str,
        tipo_alerta: str,
    ) -> None:
        notification_type = f"ORIENTADOR_{tipo_alerta}"
        resultado.avaliadas += 1
        if self._notification_already_sent(
            session=session,
            tcc_id=tcc.id,
            prazo_id=prazo_id,
            tipo_alerta=notification_type,
        ):
            resultado.ignoradas += 1
            return

        sent = email_service.send_advisor_deadline_notification(
            to_email=orientador.email,
            orientador_nome=orientador.nome_completo,
            aluno_nome=aluno.nome_completo,
            titulo=tcc.titulo,
            etapa=etapa,
            data_limite=data_limite,
            tipo_alerta=tipo_alerta,
        )
        if not sent:
            resultado.ignoradas += 1
            return

        self._finalize_notification(
            session=session,
            resultado=resultado,
            tcc_id=tcc.id,
            user_id=orientador.id,
            prazo_id=prazo_id,
            tipo_alerta=notification_type,
            description=f"Enviou alerta {tipo_alerta} de orientando para {etapa}.",
        )

    def _finalize_notification(
        self,
        *,
        session: Session,
        resultado: NotificacaoPrazoResultado,
        tcc_id: str,
        user_id: str,
        prazo_id: str,
        tipo_alerta: str,
        description: str,
    ) -> None:
        if self._record_notification(
            session=session,
            tcc_id=tcc_id,
            aluno_id=user_id,
            prazo_id=prazo_id,
            tipo_alerta=tipo_alerta,
        ):
            resultado.enviadas += 1
            AuditService().log_event(
                session=session,
                user_id=user_id,
                action="NOTIFICACAO_PRAZO",
                entity="PRAZO",
                description=description,
                data={"tcc_id": tcc_id, "prazo_id": prazo_id, "tipo_alerta": tipo_alerta},
            )
        else:
            resultado.ignoradas += 1

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

from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models import PeriodoLetivoRecord, PrazoEtapaRecord
from backend.app.schemas.periodo import (
    CreatePeriodoRequest,
    PeriodoResponse,
    PeriodoWriteRequest,
    PrazoPayload,
    PrazoResponse,
    UpdatePeriodoRequest,
)

ACTIVE_PERIOD_CONFLICT_DETAIL = "Ja existe um periodo letivo ativo."
INACTIVE_PERIOD_EDIT_DETAIL = "Apenas periodos ativos podem ser editados."
OVERLAPPING_PERIOD_CONFLICT_DETAIL = "Ja existe um periodo letivo configurado para o intervalo informado."
PERIODO_NOT_FOUND_DETAIL = "Periodo letivo nao encontrado."
NO_ACTIVE_PERIODO_FOUND_DETAIL = "Nenhum periodo letivo ativo encontrado."
PERIODO_SAVE_CONFLICT_DETAIL = "Nao foi possivel salvar o periodo letivo informado."


class PeriodoService:
    def create_periodo(
        self,
        *,
        session: Session,
        payload: CreatePeriodoRequest,
    ) -> PeriodoResponse:
        self._ensure_no_date_overlap(
            session=session,
            data_inicio=payload.data_inicio,
            data_fim=payload.data_fim,
        )
        if payload.ativo:
            self._ensure_single_active_period(session=session)

        periodo = PeriodoLetivoRecord(
            id=str(uuid4()),
            nome=payload.nome,
            data_inicio=payload.data_inicio,
            data_fim=payload.data_fim,
            ativo=payload.ativo,
            prazos=self._build_prazos(payload.prazos),
        )

        self._persist_periodo(
            session=session,
            periodo=periodo,
            active_requested=payload.ativo,
            data_inicio=payload.data_inicio,
            data_fim=payload.data_fim,
        )
        return self.get_periodo_by_id(session=session, periodo_id=periodo.id)

    def list_periodos(self, *, session: Session) -> list[PeriodoResponse]:
        periodos = session.scalars(
            select(PeriodoLetivoRecord)
            .options(selectinload(PeriodoLetivoRecord.prazos))
            .order_by(PeriodoLetivoRecord.data_inicio.desc(), PeriodoLetivoRecord.nome.asc())
        ).all()
        return [self._build_periodo_response(periodo) for periodo in periodos]

    def get_periodo_by_id(self, *, session: Session, periodo_id: str) -> PeriodoResponse:
        periodo = self._get_periodo_record(session=session, periodo_id=periodo_id)
        return self._build_periodo_response(periodo)

    def get_active_periodo(self, *, session: Session) -> PeriodoResponse:
        periodo = session.scalar(
            select(PeriodoLetivoRecord)
            .options(selectinload(PeriodoLetivoRecord.prazos))
            .where(PeriodoLetivoRecord.ativo.is_(True))
            .order_by(PeriodoLetivoRecord.data_inicio.desc())
        )
        if periodo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NO_ACTIVE_PERIODO_FOUND_DETAIL,
            )
        return self._build_periodo_response(periodo)

    def update_periodo(
        self,
        *,
        session: Session,
        periodo_id: str,
        payload: UpdatePeriodoRequest,
    ) -> PeriodoResponse:
        periodo = self._get_periodo_record(session=session, periodo_id=periodo_id)
        if periodo.ativo is not True:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=INACTIVE_PERIOD_EDIT_DETAIL,
            )

        merged_payload = self._build_merged_payload(periodo=periodo, payload=payload)

        self._ensure_no_date_overlap(
            session=session,
            data_inicio=merged_payload.data_inicio,
            data_fim=merged_payload.data_fim,
            exclude_periodo_id=periodo.id,
        )
        if merged_payload.ativo:
            self._ensure_single_active_period(session=session, exclude_periodo_id=periodo.id)

        periodo.nome = merged_payload.nome
        periodo.data_inicio = merged_payload.data_inicio
        periodo.data_fim = merged_payload.data_fim
        periodo.ativo = merged_payload.ativo

        if payload.prazos is not None:
            periodo.prazos.clear()
            periodo.prazos.extend(self._build_prazos(merged_payload.prazos))

        self._persist_periodo(
            session=session,
            periodo=periodo,
            active_requested=merged_payload.ativo,
            data_inicio=merged_payload.data_inicio,
            data_fim=merged_payload.data_fim,
        )
        return self.get_periodo_by_id(session=session, periodo_id=periodo.id)

    def _get_periodo_record(self, *, session: Session, periodo_id: str) -> PeriodoLetivoRecord:
        periodo = session.scalar(
            select(PeriodoLetivoRecord)
            .options(selectinload(PeriodoLetivoRecord.prazos))
            .where(PeriodoLetivoRecord.id == periodo_id)
        )
        if periodo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=PERIODO_NOT_FOUND_DETAIL,
            )
        return periodo

    def _ensure_single_active_period(
        self,
        *,
        session: Session,
        exclude_periodo_id: str | None = None,
    ) -> None:
        query = select(PeriodoLetivoRecord).where(PeriodoLetivoRecord.ativo.is_(True))
        if exclude_periodo_id is not None:
            query = query.where(PeriodoLetivoRecord.id != exclude_periodo_id)

        existing_periodo = session.scalar(query)
        if existing_periodo is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ACTIVE_PERIOD_CONFLICT_DETAIL,
            )

    def _ensure_no_date_overlap(
        self,
        *,
        session: Session,
        data_inicio,
        data_fim,
        exclude_periodo_id: str | None = None,
    ) -> None:
        query = select(PeriodoLetivoRecord).where(
            PeriodoLetivoRecord.data_inicio <= data_fim,
            PeriodoLetivoRecord.data_fim >= data_inicio,
        )
        if exclude_periodo_id is not None:
            query = query.where(PeriodoLetivoRecord.id != exclude_periodo_id)

        overlapping_periodo = session.scalar(query)
        if overlapping_periodo is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=OVERLAPPING_PERIOD_CONFLICT_DETAIL,
            )

    def _persist_periodo(
        self,
        *,
        session: Session,
        periodo: PeriodoLetivoRecord,
        active_requested: bool,
        data_inicio,
        data_fim,
    ) -> None:
        session.add(periodo)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            if active_requested:
                self._ensure_single_active_period(session=session, exclude_periodo_id=periodo.id)
            self._ensure_no_date_overlap(
                session=session,
                data_inicio=data_inicio,
                data_fim=data_fim,
                exclude_periodo_id=periodo.id,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=PERIODO_SAVE_CONFLICT_DETAIL,
            ) from exc

    def _build_prazos(self, prazos: list[PrazoPayload]) -> list[PrazoEtapaRecord]:
        return [
            PrazoEtapaRecord(
                id=str(uuid4()),
                nome_etapa=prazo.nome_etapa,
                data_limite=prazo.data_limite,
                tipo_tcc=prazo.tipo_tcc,
            )
            for prazo in prazos
        ]

    def _build_merged_payload(
        self,
        *,
        periodo: PeriodoLetivoRecord,
        payload: UpdatePeriodoRequest,
    ) -> PeriodoWriteRequest:
        try:
            return PeriodoWriteRequest(
                nome=payload.nome if payload.nome is not None else periodo.nome,
                data_inicio=payload.data_inicio if payload.data_inicio is not None else periodo.data_inicio,
                data_fim=payload.data_fim if payload.data_fim is not None else periodo.data_fim,
                ativo=payload.ativo if payload.ativo is not None else periodo.ativo,
                prazos=payload.prazos if payload.prazos is not None else self._serialize_existing_prazos(periodo.prazos),
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors()[0]["msg"],
            ) from exc

    def _serialize_existing_prazos(self, prazos: list[PrazoEtapaRecord]) -> list[PrazoPayload]:
        return [
            PrazoPayload(
                nome_etapa=prazo.nome_etapa,
                data_limite=prazo.data_limite,
                tipo_tcc=prazo.tipo_tcc,
            )
            for prazo in prazos
        ]

    def _build_periodo_response(self, periodo: PeriodoLetivoRecord) -> PeriodoResponse:
        ordered_prazos = sorted(
            periodo.prazos,
            key=lambda prazo: (prazo.data_limite, prazo.nome_etapa.casefold(), prazo.id),
        )
        return PeriodoResponse(
            id=periodo.id,
            nome=periodo.nome,
            data_inicio=periodo.data_inicio,
            data_fim=periodo.data_fim,
            ativo=periodo.ativo,
            prazos=[PrazoResponse.model_validate(prazo) for prazo in ordered_prazos],
        )


async def get_periodo_service() -> PeriodoService:
    return PeriodoService()

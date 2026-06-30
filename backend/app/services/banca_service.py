from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models import BancaRecord, MembroBancaRecord, PeriodoLetivoRecord, TCCRecord, UserRecord
from backend.app.models.banca import PapelBanca
from backend.app.models.tcc import StatusTCC
from backend.app.models.user import Perfil
from backend.app.schemas.banca import BancaRequest, BancaResponse, MembroBancaResponse
from backend.app.services.audit_service import AuditService
from backend.app.services.email_service import EmailService

NO_ACTIVE_PERIODO_FOUND_DETAIL = "Nenhum periodo letivo ativo encontrado."
TCC_ORIENTANDO_NOT_FOUND_DETAIL = "Orientando nao encontrado para o periodo ativo."
BANCA_NOT_FOUND_DETAIL = "Banca nao encontrada."
BANCA_ACCESS_FORBIDDEN_DETAIL = "Perfil sem permissao para acessar esta banca."


class BancaService:
    def registrar_banca(
        self,
        *,
        session: Session,
        current_user: UserRecord,
        payload: BancaRequest,
        email_service: EmailService,
        audit_service: AuditService,
    ) -> BancaResponse:
        tcc, aluno = self._get_tcc_orientando(
            session=session,
            orientador=current_user,
            aluno_id=payload.aluno_id,
        )

        banca = session.scalar(
            select(BancaRecord)
            .options(selectinload(BancaRecord.membros))
            .where(BancaRecord.tcc_id == tcc.id)
        )
        if banca is None:
            banca = BancaRecord(
                id=str(uuid4()),
                tcc_id=tcc.id,
                data_defesa=payload.data_defesa,
                local=payload.local,
            )
            session.add(banca)
            session.flush()
        else:
            banca.data_defesa = payload.data_defesa
            banca.local = payload.local
            for membro in list(banca.membros):
                session.delete(membro)
            session.flush()

        for membro in payload.membros:
            session.add(
                MembroBancaRecord(
                    id=str(uuid4()),
                    banca_id=banca.id,
                    user_id=self._resolve_user_id_for_papel(
                        tcc=tcc,
                        papel=membro.papel,
                    ),
                    nome=membro.nome,
                    titulacao=membro.titulacao,
                    instituicao=membro.instituicao,
                    papel=membro.papel,
                )
            )

        tcc.data_defesa = payload.data_defesa.date()
        tcc.banca = [membro.nome for membro in payload.membros]
        session.commit()
        session.refresh(banca)

        membros_texto = [
            f"{membro.nome} ({membro.titulacao}, {membro.instituicao})"
            for membro in payload.membros
        ]
        email_service.send_banca_notification(
            to_email=aluno.email,
            aluno_nome=aluno.nome_completo,
            titulo=tcc.titulo,
            data_defesa=self._format_datetime(payload.data_defesa),
            local=payload.local,
            membros=membros_texto,
        )
        audit_service.log_event(
            session=session,
            user_id=current_user.id,
            action="REGISTRO_BANCA",
            entity="BANCA",
            description=f"Registrou banca de defesa de {aluno.nome_completo}.",
            data={"tcc_id": tcc.id, "banca_id": banca.id, "aluno_id": aluno.id},
        )

        return self._build_response(session=session, banca_id=banca.id)

    def get_banca(
        self,
        *,
        session: Session,
        current_user: UserRecord,
        aluno_id: str | None = None,
    ) -> BancaResponse | None:
        statement = (
            select(BancaRecord)
            .options(selectinload(BancaRecord.membros), selectinload(BancaRecord.tcc))
            .join(TCCRecord, TCCRecord.id == BancaRecord.tcc_id)
        )
        if current_user.perfil == Perfil.ALUNO:
            statement = statement.where(TCCRecord.aluno_id == current_user.id)
        elif current_user.perfil == Perfil.ORIENTADOR:
            if aluno_id:
                statement = statement.where(TCCRecord.aluno_id == aluno_id)
            statement = statement.where(
                (TCCRecord.orientador_id == current_user.id)
                | (TCCRecord.coorientador_id == current_user.id)
            )
        elif current_user.perfil == Perfil.COORDENADOR:
            if aluno_id:
                statement = statement.where(TCCRecord.aluno_id == aluno_id)
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=BANCA_ACCESS_FORBIDDEN_DETAIL)

        banca = session.scalar(statement.order_by(BancaRecord.criado_em.desc()))
        if banca is None:
            return None
        return self._build_response(session=session, banca_id=banca.id)

    def _get_tcc_orientando(
        self,
        *,
        session: Session,
        orientador: UserRecord,
        aluno_id: str | None,
    ) -> tuple[TCCRecord, UserRecord]:
        periodo = self._get_active_periodo(session=session)
        statement = (
            select(TCCRecord, UserRecord)
            .join(UserRecord, UserRecord.id == TCCRecord.aluno_id)
            .where(
                TCCRecord.periodo_id == periodo.id,
                (TCCRecord.orientador_id == orientador.id) | (TCCRecord.coorientador_id == orientador.id),
                TCCRecord.status.in_([StatusTCC.EM_ANDAMENTO, StatusTCC.APROVADO]),
            )
        )
        if aluno_id:
            statement = statement.where(TCCRecord.aluno_id == aluno_id)

        row = session.execute(statement.order_by(UserRecord.nome_completo.asc())).first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TCC_ORIENTANDO_NOT_FOUND_DETAIL)
        return row[0], row[1]

    def _get_active_periodo(self, *, session: Session) -> PeriodoLetivoRecord:
        periodo = session.scalar(
            select(PeriodoLetivoRecord)
            .where(PeriodoLetivoRecord.ativo.is_(True))
            .order_by(PeriodoLetivoRecord.data_inicio.desc())
        )
        if periodo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_ACTIVE_PERIODO_FOUND_DETAIL)
        return periodo

    def _resolve_user_id_for_papel(self, *, tcc: TCCRecord, papel: PapelBanca) -> str | None:
        if papel == PapelBanca.ORIENTADOR:
            return tcc.orientador_id
        if papel == PapelBanca.COORIENTADOR:
            return tcc.coorientador_id
        return None

    def _build_response(self, *, session: Session, banca_id: str) -> BancaResponse:
        row = session.execute(
            select(BancaRecord, TCCRecord, UserRecord)
            .options(selectinload(BancaRecord.membros))
            .join(TCCRecord, TCCRecord.id == BancaRecord.tcc_id)
            .join(UserRecord, UserRecord.id == TCCRecord.aluno_id)
            .where(BancaRecord.id == banca_id)
        ).one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BANCA_NOT_FOUND_DETAIL)

        banca, tcc, aluno = row
        return BancaResponse(
            id=banca.id,
            tcc_id=tcc.id,
            aluno_id=aluno.id,
            aluno_nome=aluno.nome_completo,
            data_defesa=banca.data_defesa,
            local=banca.local,
            membros=[
                MembroBancaResponse(
                    id=membro.id,
                    nome=membro.nome,
                    titulacao=membro.titulacao,
                    instituicao=membro.instituicao,
                    papel=membro.papel,
                )
                for membro in sorted(banca.membros, key=lambda item: item.papel.value)
            ],
            criado_em=banca.criado_em,
            atualizado_em=banca.atualizado_em,
        )

    def _format_datetime(self, value: datetime) -> str:
        return value.strftime("%d/%m/%Y %H:%M")


async def get_banca_service() -> BancaService:
    return BancaService()

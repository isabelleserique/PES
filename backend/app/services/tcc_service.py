from uuid import uuid4
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.db.models import TCCRecord, UserRecord
from backend.app.models.user import Perfil
from backend.app.models.tcc import StatusTCC
from backend.app.schemas.tcc import TCCCreateRequest
from backend.app.services.email_service import EmailService
from backend.app.services.audit_service import AuditService


class TCCService:

    def _get_periodo_atual(self) -> str:
        now = datetime.utcnow()
        semestre = 1 if now.month <= 6 else 2
        return f"{now.year}.{semestre}"

    def _is_prazo_excedido(self) -> bool:
        return False  

    def create_tcc(
        self,
        *,
        session: Session,
        payload: TCCCreateRequest,
        current_user: UserRecord,
        email_service: EmailService,
        audit_service: AuditService,
    ):
        if current_user.perfil != Perfil.ALUNO:
            raise HTTPException(status_code=403, detail="Apenas alunos podem submeter TCC.")

        periodo_atual = self._get_periodo_atual()

        existing = session.scalar(
            select(TCCRecord).where(
                TCCRecord.aluno_id == current_user.id,
                TCCRecord.periodo == periodo_atual,
            )
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Aluno já submeteu TCC neste período.",
            )

        orientador = session.scalar(
            select(UserRecord).where(
                UserRecord.id == payload.orientador_id,
                UserRecord.perfil == Perfil.ORIENTADOR,
            )
        )
        if not orientador:
            raise HTTPException(404, "Orientador inválido.")

        if payload.coorientador_id == payload.orientador_id:
            raise HTTPException(400, "Orientador e coorientador não podem ser iguais.")

        if payload.coorientador_id:
            co = session.scalar(
                select(UserRecord).where(
                    UserRecord.id == payload.coorientador_id,
                    UserRecord.perfil == Perfil.ORIENTADOR,
                )
            )
            if not co:
                raise HTTPException(404, "Coorientador inválido.")
                

        prazo_excedido = self._is_prazo_excedido()

        tcc = TCCRecord(
            id=str(uuid4()),
            titulo=payload.titulo,
            tipo=payload.tipo,
            aluno_id=current_user.id,
            orientador_id=payload.orientador_id,
            coorientador_id=payload.coorientador_id,
            periodo=periodo_atual,
            status=StatusTCC.AGUARDANDO_ACEITE,
            prazo_excedido=self._is_prazo_excedido(),
        )

        session.add(tcc)
        session.commit()
        session.refresh(tcc)

        email_service.send_tcc_submission_notification(
            to_email=orientador.email,
            aluno_nome=current_user.nome_completo,
            titulo=tcc.titulo,
        )

        audit_service.log_tcc_submission(
            aluno_id=current_user.id,
            tcc_id=tcc.id,
        )

        return tcc
    
    def update_tcc(
        self,
        *,
        tcc_id: str,
        payload: TCCCreateRequest,
        session: Session,
        current_user: UserRecord,
        audit_service: AuditService,
    ):
        tcc = session.get(TCCRecord, tcc_id)

        if not tcc:
            raise HTTPException(404, "TCC não encontrado.")

        if tcc.aluno_id != current_user.id:
            raise HTTPException(403, "Sem permissão.")

        tcc.titulo = payload.titulo
        tcc.tipo = payload.tipo
        tcc.orientador_id = payload.orientador_id
        tcc.coorientador_id = payload.coorientador_id
        tcc.atualizado_em = datetime.utcnow()

        session.commit()

        audit_service.log_tcc_update(
            aluno_id=current_user.id,
            tcc_id=tcc.id,
        )

        return tcc
from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import OrientacaoSessaoRecord, TCCRecord, UserRecord
from backend.app.models.tcc import StatusTCC
from backend.app.schemas.orientacao import SessaoOrientacaoPayload, SessaoOrientacaoResponse
from backend.app.services.audit_service import AuditService

ORIENTANDO_NOT_FOUND_DETAIL = "Orientando nao encontrado para este orientador."
TCC_NOT_FOUND_DETAIL = "Aluno nao possui TCC no periodo letivo ativo."


class OrientacaoService:
    def registrar_sessao(
        self,
        *,
        session: Session,
        current_user: UserRecord,
        payload: SessaoOrientacaoPayload,
        audit_service: AuditService,
    ) -> SessaoOrientacaoResponse:
        row = self._get_orientando_row(
            session=session,
            orientador_id=current_user.id,
            aluno_id=payload.aluno_id,
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ORIENTANDO_NOT_FOUND_DETAIL)

        tcc, aluno = row
        sessao = OrientacaoSessaoRecord(
            id=str(uuid4()),
            tcc_id=tcc.id,
            aluno_id=aluno.id,
            orientador_id=current_user.id,
            data_sessao=payload.data_sessao,
            resumo=payload.resumo,
            proximos_passos=payload.proximos_passos,
        )
        session.add(sessao)
        session.commit()
        session.refresh(sessao)

        audit_service.log_event(
            session=session,
            user_id=current_user.id,
            action="REGISTRO_SESSAO_ORIENTACAO",
            entity="ORIENTACAO",
            description=f"Registrou sessao de orientacao para {aluno.nome_completo}.",
            data={"sessao_id": sessao.id, "tcc_id": tcc.id, "aluno_id": aluno.id},
        )

        return self._build_response(sessao=sessao, aluno=aluno, orientador=current_user)

    def listar_sessoes_orientador(
        self,
        *,
        session: Session,
        current_user: UserRecord,
        aluno_id: str,
    ) -> list[SessaoOrientacaoResponse]:
        row = self._get_orientando_row(
            session=session,
            orientador_id=current_user.id,
            aluno_id=aluno_id,
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ORIENTANDO_NOT_FOUND_DETAIL)

        _, aluno = row
        sessoes = session.scalars(
            select(OrientacaoSessaoRecord)
            .where(
                OrientacaoSessaoRecord.aluno_id == aluno.id,
                OrientacaoSessaoRecord.orientador_id == current_user.id,
            )
            .order_by(OrientacaoSessaoRecord.data_sessao.desc(), OrientacaoSessaoRecord.criado_em.desc())
        ).all()

        return [
            self._build_response(sessao=sessao, aluno=aluno, orientador=current_user)
            for sessao in sessoes
        ]

    def listar_minhas_sessoes(
        self,
        *,
        session: Session,
        current_user: UserRecord,
    ) -> list[SessaoOrientacaoResponse]:
        row = session.execute(
            select(TCCRecord, UserRecord)
            .join(UserRecord, UserRecord.id == TCCRecord.orientador_id)
            .where(TCCRecord.aluno_id == current_user.id)
            .order_by(TCCRecord.criado_em.desc())
        ).first()
        if row is None:
            return []

        tcc, orientador = row
        sessoes = session.scalars(
            select(OrientacaoSessaoRecord)
            .where(OrientacaoSessaoRecord.tcc_id == tcc.id)
            .order_by(OrientacaoSessaoRecord.data_sessao.desc(), OrientacaoSessaoRecord.criado_em.desc())
        ).all()
        return [
            self._build_response(sessao=sessao, aluno=current_user, orientador=orientador)
            for sessao in sessoes
        ]

    def _get_orientando_row(
        self,
        *,
        session: Session,
        orientador_id: str,
        aluno_id: str,
    ) -> tuple[TCCRecord, UserRecord] | None:
        return session.execute(
            select(TCCRecord, UserRecord)
            .join(UserRecord, UserRecord.id == TCCRecord.aluno_id)
            .where(
                TCCRecord.aluno_id == aluno_id,
                (TCCRecord.orientador_id == orientador_id) | (TCCRecord.coorientador_id == orientador_id),
                TCCRecord.status.in_(
                    [
                        StatusTCC.AGUARDANDO_ACEITE,
                        StatusTCC.EM_ANDAMENTO,
                        StatusTCC.APROVADO,
                    ]
                ),
            )
            .order_by(TCCRecord.criado_em.desc())
        ).first()

    def _build_response(
        self,
        *,
        sessao: OrientacaoSessaoRecord,
        aluno: UserRecord,
        orientador: UserRecord,
    ) -> SessaoOrientacaoResponse:
        return SessaoOrientacaoResponse(
            id=sessao.id,
            tcc_id=sessao.tcc_id,
            aluno_id=aluno.id,
            aluno_nome=aluno.nome_completo,
            orientador_id=orientador.id,
            orientador_nome=orientador.nome_completo,
            data_sessao=sessao.data_sessao,
            resumo=sessao.resumo,
            proximos_passos=sessao.proximos_passos,
            criado_em=sessao.criado_em,
        )


async def get_orientacao_service() -> OrientacaoService:
    return OrientacaoService()

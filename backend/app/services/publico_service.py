from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session, aliased, selectinload

from backend.app.core.config import Settings, get_settings
from backend.app.db.models import SubmissaoEntregavelRecord, TCCRecord, UserRecord
from backend.app.schemas.publico import (
    DocumentoTccPublicoResponse,
    PublicStoredFile,
    TccPublicoDetalheResponse,
    TccPublicoResponse,
)

TCC_PUBLICO_NOT_FOUND_DETAIL = "TCC publico nao encontrado."
DOCUMENTO_PUBLICO_NOT_FOUND_DETAIL = "Documento publico nao encontrado."


class PublicoService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def buscar_tccs(
        self,
        *,
        session: Session,
        area_tematica: str | None = None,
        curso: str | None = None,
        aluno: str | None = None,
        titulo: str | None = None,
    ) -> list[TccPublicoResponse]:
        aluno_alias = aliased(UserRecord)
        orientador_alias = aliased(UserRecord)
        statement = (
            select(TCCRecord, aluno_alias, orientador_alias)
            .join(aluno_alias, aluno_alias.id == TCCRecord.aluno_id)
            .join(orientador_alias, orientador_alias.id == TCCRecord.orientador_id)
            .where(self._has_public_document_clause())
            .order_by(TCCRecord.atualizado_em.desc(), TCCRecord.titulo.asc())
        )

        statement = self._apply_filters(
            statement=statement,
            aluno_alias=aluno_alias,
            area_tematica=area_tematica,
            curso=curso,
            aluno=aluno,
            titulo=titulo,
        )

        rows = session.execute(statement).all()
        return [
            self._build_public_response(
                session=session,
                tcc=tcc,
                aluno=aluno_record,
                orientador=orientador,
            )
            for tcc, aluno_record, orientador in rows
        ]

    def get_tcc_detalhe(self, *, session: Session, tcc_id: str) -> TccPublicoDetalheResponse:
        aluno_alias = aliased(UserRecord)
        orientador_alias = aliased(UserRecord)
        row = session.execute(
            select(TCCRecord, aluno_alias, orientador_alias)
            .options(selectinload(TCCRecord.submissoes_entregaveis))
            .join(aluno_alias, aluno_alias.id == TCCRecord.aluno_id)
            .join(orientador_alias, orientador_alias.id == TCCRecord.orientador_id)
            .where(
                TCCRecord.id == tcc_id,
                self._has_public_document_clause(),
            )
        ).one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TCC_PUBLICO_NOT_FOUND_DETAIL)

        tcc, aluno, orientador = row
        base = self._build_public_response(session=session, tcc=tcc, aluno=aluno, orientador=orientador)
        return TccPublicoDetalheResponse(
            **base.model_dump(),
            resumo=tcc.resumo,
            documentos=self._build_documentos(tcc),
        )

    def get_documento_publico(
        self,
        *,
        session: Session,
        tcc_id: str,
        submissao_id: str,
    ) -> PublicStoredFile:
        submissao = session.scalar(
            select(SubmissaoEntregavelRecord)
            .join(TCCRecord, TCCRecord.id == SubmissaoEntregavelRecord.tcc_id)
            .where(
                TCCRecord.id == tcc_id,
                SubmissaoEntregavelRecord.id == submissao_id,
            )
        )
        if submissao is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=DOCUMENTO_PUBLICO_NOT_FOUND_DETAIL)

        path = Path(submissao.caminho_arquivo)
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=DOCUMENTO_PUBLICO_NOT_FOUND_DETAIL)

        return PublicStoredFile(
            path=str(path),
            filename=submissao.nome_arquivo,
            media_type=submissao.tipo_conteudo or "application/octet-stream",
        )

    def _apply_filters(
        self,
        *,
        statement,
        aluno_alias,
        area_tematica: str | None,
        curso: str | None,
        aluno: str | None,
        titulo: str | None,
    ):
        if area_tematica:
            statement = statement.where(TCCRecord.area_tematica.ilike(f"%{area_tematica.strip()}%"))
        if curso:
            statement = statement.where(TCCRecord.curso.ilike(f"%{curso.strip()}%"))
        if aluno:
            statement = statement.where(aluno_alias.nome_completo.ilike(f"%{aluno.strip()}%"))
        if titulo:
            statement = statement.where(TCCRecord.titulo.ilike(f"%{titulo.strip()}%"))
        return statement

    def _has_public_document_clause(self):
        return exists(
            select(SubmissaoEntregavelRecord.id).where(SubmissaoEntregavelRecord.tcc_id == TCCRecord.id)
        )

    def _build_public_response(
        self,
        *,
        session: Session,
        tcc: TCCRecord,
        aluno: UserRecord,
        orientador: UserRecord,
    ) -> TccPublicoResponse:
        return TccPublicoResponse(
            id=tcc.id,
            titulo=tcc.titulo,
            tipo_tcc=tcc.tipo_tcc,
            area_tematica=tcc.area_tematica,
            curso=tcc.curso or "Ciência da Computação",
            aluno_nome=aluno.nome_completo,
            orientador_nome=orientador.nome_completo,
            data_defesa=tcc.data_defesa,
            banca=self._build_banca(session=session, tcc=tcc, orientador=orientador),
        )

    def _build_banca(self, *, session: Session, tcc: TCCRecord, orientador: UserRecord) -> list[str]:
        if tcc.banca:
            return tcc.banca

        banca = [orientador.nome_completo]
        if tcc.coorientador_id:
            coorientador = session.scalar(select(UserRecord).where(UserRecord.id == tcc.coorientador_id))
            if coorientador is not None:
                banca.append(coorientador.nome_completo)
        return banca

    def _build_documentos(self, tcc: TCCRecord) -> list[DocumentoTccPublicoResponse]:
        latest_by_etapa: dict[str, SubmissaoEntregavelRecord] = {}
        for submissao in tcc.submissoes_entregaveis:
            current = latest_by_etapa.get(submissao.etapa)
            if current is None or submissao.versao > current.versao:
                latest_by_etapa[submissao.etapa] = submissao

        return [
            self._build_documento(tcc=tcc, submissao=submissao)
            for submissao in sorted(latest_by_etapa.values(), key=lambda item: (item.etapa, item.versao))
        ]

    def _build_documento(
        self,
        *,
        tcc: TCCRecord,
        submissao: SubmissaoEntregavelRecord,
    ) -> DocumentoTccPublicoResponse:
        base_url = self.settings.api_base_url.rstrip("/")
        url = f"{base_url}/public/tcc/{tcc.id}/documentos/{submissao.id}/arquivo"
        is_pdf = Path(submissao.nome_arquivo).suffix.casefold() == ".pdf"
        return DocumentoTccPublicoResponse(
            id=submissao.id,
            tipo=submissao.etapa,
            nome_arquivo=submissao.nome_arquivo,
            url_download=f"{url}?download=true",
            url_preview=url if is_pdf else None,
        )


async def get_publico_service() -> PublicoService:
    return PublicoService()

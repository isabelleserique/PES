from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import exists, select
from sqlalchemy.orm import Session, aliased, selectinload

from backend.app.core.config import Settings, get_settings
from backend.app.db.models import (
    BancaRecord,
    DepositoFinalRecord,
    DocumentoDepositoRecord,
    TCCRecord,
    UserRecord,
)
from backend.app.models.deposito import StatusDeposito, TipoDocumentoDeposito
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
            .where(
                aluno_alias.publicar_tcc_portal_publico.is_(True),
                self._has_public_document_clause(),
            )
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
            .options(
                selectinload(TCCRecord.deposito_final).selectinload(DepositoFinalRecord.documentos),
                selectinload(TCCRecord.banca_defesa).selectinload(BancaRecord.membros),
            )
            .join(aluno_alias, aluno_alias.id == TCCRecord.aluno_id)
            .join(orientador_alias, orientador_alias.id == TCCRecord.orientador_id)
            .where(
                TCCRecord.id == tcc_id,
                aluno_alias.publicar_tcc_portal_publico.is_(True),
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
        download: bool = False,
    ) -> PublicStoredFile:
        documento = session.scalar(
            select(DocumentoDepositoRecord)
            .join(DepositoFinalRecord, DepositoFinalRecord.id == DocumentoDepositoRecord.deposito_id)
            .join(TCCRecord, TCCRecord.id == DepositoFinalRecord.tcc_id)
            .join(UserRecord, UserRecord.id == TCCRecord.aluno_id)
            .where(
                TCCRecord.id == tcc_id,
                DocumentoDepositoRecord.id == submissao_id,
                DocumentoDepositoRecord.tipo_documento == TipoDocumentoDeposito.TCC_FINAL,
                DepositoFinalRecord.status.in_([StatusDeposito.APROVADO, StatusDeposito.DEPOSITADO]),
                UserRecord.publicar_tcc_portal_publico.is_(True),
            )
        )
        if documento is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=DOCUMENTO_PUBLICO_NOT_FOUND_DETAIL)

        path = Path(documento.caminho_original if download else documento.caminho_preview_pdf or documento.caminho_original)
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=DOCUMENTO_PUBLICO_NOT_FOUND_DETAIL)

        return PublicStoredFile(
            path=str(path),
            filename=documento.nome_original,
            media_type="application/pdf" if path.suffix.lower() == ".pdf" else documento.mime_type or "application/octet-stream",
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
            select(DocumentoDepositoRecord.id)
            .join(DepositoFinalRecord, DepositoFinalRecord.id == DocumentoDepositoRecord.deposito_id)
            .where(
                DepositoFinalRecord.tcc_id == TCCRecord.id,
                DepositoFinalRecord.status.in_([StatusDeposito.APROVADO, StatusDeposito.DEPOSITADO]),
                DocumentoDepositoRecord.tipo_documento == TipoDocumentoDeposito.TCC_FINAL,
            )
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
        if tcc.banca_defesa is not None and tcc.banca_defesa.membros:
            return [
                f"{membro.nome} ({membro.titulacao}, {membro.instituicao})"
                for membro in sorted(tcc.banca_defesa.membros, key=lambda item: item.papel.value)
            ]
        if tcc.banca:
            return tcc.banca

        banca = [orientador.nome_completo]
        if tcc.coorientador_id:
            coorientador = session.scalar(select(UserRecord).where(UserRecord.id == tcc.coorientador_id))
            if coorientador is not None:
                banca.append(coorientador.nome_completo)
        return banca

    def _build_documentos(self, tcc: TCCRecord) -> list[DocumentoTccPublicoResponse]:
        if tcc.deposito_final is None:
            return []
        if tcc.deposito_final.status not in {StatusDeposito.APROVADO, StatusDeposito.DEPOSITADO}:
            return []

        documentos = [
            documento
            for documento in tcc.deposito_final.documentos
            if documento.tipo_documento == TipoDocumentoDeposito.TCC_FINAL
        ]
        return [self._build_documento(tcc=tcc, documento=documento) for documento in documentos]

    def _build_documento(
        self,
        *,
        tcc: TCCRecord,
        documento: DocumentoDepositoRecord,
    ) -> DocumentoTccPublicoResponse:
        base_url = self.settings.api_base_url.rstrip("/")
        url = f"{base_url}/public/tcc/{tcc.id}/documentos/{documento.id}/arquivo"
        has_pdf_preview = bool(documento.caminho_preview_pdf and Path(documento.caminho_preview_pdf).suffix.casefold() == ".pdf")
        return DocumentoTccPublicoResponse(
            id=documento.id,
            tipo=documento.tipo_documento.value,
            nome_arquivo=documento.nome_original,
            url_download=f"{url}?download=true",
            url_preview=url if has_pdf_preview else None,
        )


async def get_publico_service() -> PublicoService:
    return PublicoService()

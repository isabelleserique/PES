from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.core.config import Settings, get_settings
from backend.app.db.models import DepositoFinalRecord, DocumentoDepositoRecord, PeriodoLetivoRecord, TCCRecord, UserRecord
from backend.app.models.deposito import StatusDeposito, TipoDocumentoDeposito
from backend.app.models.tcc import StatusTCC
from backend.app.models.user import Perfil
from backend.app.schemas.deposito import DepositoResponse, DocumentoDepositoResponse
from backend.app.services.audit_service import AuditService
from backend.app.services.email_service import EmailService

INVALID_DEPOSITO_FILE_DETAIL = "Arquivos do deposito devem estar nos formatos PDF ou DOCX."
DEPOSITO_NOT_FOUND_DETAIL = "Deposito final nao encontrado."
DOCUMENTO_DEPOSITO_NOT_FOUND_DETAIL = "Documento de deposito nao encontrado."
DEPOSITO_ACCESS_FORBIDDEN_DETAIL = "Perfil sem permissao para acessar este deposito."
NO_ACTIVE_TCC_DETAIL = "Aluno nao possui TCC no periodo letivo ativo."
DEPOSITO_CONFLICT_DETAIL = "Deposito final ja esta em revisao ou finalizado."
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
DEPOSITO_EXTENSIONS = {".pdf", ".docx"}
DOCUMENTOS_OBRIGATORIOS = {
    TipoDocumentoDeposito.TCC_FINAL,
    TipoDocumentoDeposito.ATA_DEFESA,
    TipoDocumentoDeposito.FOLHA_APROVACAO,
    TipoDocumentoDeposito.FORMULARIOS,
    TipoDocumentoDeposito.DECLARACOES,
}


@dataclass(frozen=True)
class DepositoStoredFile:
    path: Path
    filename: str
    media_type: str


class DepositoService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def submeter_deposito(
        self,
        *,
        session: Session,
        current_user: UserRecord,
        documentos: dict[TipoDocumentoDeposito, UploadFile],
        audit_service: AuditService,
    ) -> DepositoResponse:
        missing = DOCUMENTOS_OBRIGATORIOS - set(documentos)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Todos os documentos obrigatorios de deposito devem ser enviados.",
            )

        tcc = self._get_active_tcc_for_student(session=session, aluno_id=current_user.id)
        deposito = session.scalar(
            select(DepositoFinalRecord)
            .options(selectinload(DepositoFinalRecord.documentos))
            .where(DepositoFinalRecord.tcc_id == tcc.id)
        )
        if deposito is not None and deposito.status not in {
            StatusDeposito.AGUARDANDO_ENVIO,
            StatusDeposito.DEVOLVIDO_PARA_CORRECAO,
        }:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=DEPOSITO_CONFLICT_DETAIL)

        if deposito is None:
            deposito = DepositoFinalRecord(
                id=str(uuid4()),
                tcc_id=tcc.id,
                status=StatusDeposito.EM_REVISAO,
                submetido_em=datetime.utcnow(),
            )
            session.add(deposito)
            session.flush()
        else:
            deposito.status = StatusDeposito.EM_REVISAO
            deposito.observacao_revisao = None
            deposito.submetido_em = datetime.utcnow()
            for documento in list(deposito.documentos):
                session.delete(documento)
            session.flush()

        base_dir = self.settings.upload_dir / "depositos-finais" / tcc.id / deposito.id
        base_dir.mkdir(parents=True, exist_ok=True)

        for tipo_documento, upload in documentos.items():
            content = await self._read_and_validate_file(upload)
            arquivo_path = self._write_file(
                base_dir=base_dir / tipo_documento.value,
                upload=upload,
                content=content,
                prefix=tipo_documento.value.lower(),
            )
            preview_path = self._build_preview_path(arquivo_path)
            session.add(
                DocumentoDepositoRecord(
                    id=str(uuid4()),
                    deposito_id=deposito.id,
                    tipo_documento=tipo_documento,
                    nome_original=Path(upload.filename or tipo_documento.value).name,
                    caminho_original=str(arquivo_path),
                    mime_type=upload.content_type,
                    tamanho_bytes=len(content),
                    caminho_preview_pdf=str(preview_path) if preview_path is not None else None,
                )
            )

        session.commit()
        session.refresh(deposito)
        audit_service.log_event(
            session=session,
            user_id=current_user.id,
            action="SUBMISSAO_DEPOSITO_FINAL",
            entity="DEPOSITO",
            description="Submeteu versao final e documentos de deposito.",
            data={"tcc_id": tcc.id, "deposito_id": deposito.id},
        )
        return self._build_response(session=session, deposito_id=deposito.id)

    def get_meu_deposito(self, *, session: Session, current_user: UserRecord) -> DepositoResponse:
        tcc = self._get_active_tcc_for_student(session=session, aluno_id=current_user.id)
        deposito = session.scalar(
            select(DepositoFinalRecord)
            .options(selectinload(DepositoFinalRecord.documentos))
            .where(DepositoFinalRecord.tcc_id == tcc.id)
        )
        if deposito is None:
            return self._build_empty_response(tcc=tcc, aluno=current_user)
        return self._build_response(session=session, deposito_id=deposito.id)

    def listar_depositos(self, *, session: Session) -> list[DepositoResponse]:
        depositos = session.scalars(
            select(DepositoFinalRecord)
            .options(selectinload(DepositoFinalRecord.documentos))
            .order_by(DepositoFinalRecord.atualizado_em.desc())
        ).all()
        return [self._build_response(session=session, deposito_id=deposito.id) for deposito in depositos]

    def atualizar_status(
        self,
        *,
        session: Session,
        current_user: UserRecord,
        deposito_id: str,
        status_deposito: StatusDeposito,
        observacao_revisao: str | None,
        email_service: EmailService,
        audit_service: AuditService,
    ) -> DepositoResponse:
        row = session.execute(
            select(DepositoFinalRecord, TCCRecord, UserRecord)
            .join(TCCRecord, TCCRecord.id == DepositoFinalRecord.tcc_id)
            .join(UserRecord, UserRecord.id == TCCRecord.aluno_id)
            .where(DepositoFinalRecord.id == deposito_id)
        ).one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=DEPOSITO_NOT_FOUND_DETAIL)

        deposito, tcc, aluno = row
        deposito.status = status_deposito
        deposito.observacao_revisao = observacao_revisao
        if status_deposito == StatusDeposito.DEPOSITADO:
            tcc.status = StatusTCC.APROVADO
        session.commit()
        session.refresh(deposito)

        email_service.send_deposito_status_notification(
            to_email=aluno.email,
            aluno_nome=aluno.nome_completo,
            titulo=tcc.titulo,
            status_deposito=status_deposito.value,
            observacao=observacao_revisao,
        )
        audit_service.log_event(
            session=session,
            user_id=current_user.id,
            action="ATUALIZACAO_STATUS_DEPOSITO",
            entity="DEPOSITO",
            description=f"Atualizou status de deposito para {status_deposito.value}.",
            data={"deposito_id": deposito.id, "tcc_id": tcc.id, "status": status_deposito.value},
        )
        return self._build_response(session=session, deposito_id=deposito.id)

    def get_documento(
        self,
        *,
        session: Session,
        current_user: UserRecord,
        documento_id: str,
        preview: bool,
    ) -> DepositoStoredFile:
        row = session.execute(
            select(DocumentoDepositoRecord, DepositoFinalRecord, TCCRecord)
            .join(DepositoFinalRecord, DepositoFinalRecord.id == DocumentoDepositoRecord.deposito_id)
            .join(TCCRecord, TCCRecord.id == DepositoFinalRecord.tcc_id)
            .where(DocumentoDepositoRecord.id == documento_id)
        ).one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=DOCUMENTO_DEPOSITO_NOT_FOUND_DETAIL)

        documento, deposito, tcc = row
        self._ensure_can_access_document(current_user=current_user, tcc=tcc)
        path = Path(documento.caminho_preview_pdf) if preview and documento.caminho_preview_pdf else Path(documento.caminho_original)
        if not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=DOCUMENTO_DEPOSITO_NOT_FOUND_DETAIL)

        media_type = "application/pdf" if preview and path.suffix.lower() == ".pdf" else documento.mime_type
        return DepositoStoredFile(
            path=path,
            filename=path.name if preview else documento.nome_original,
            media_type=media_type or "application/octet-stream",
        )

    def _get_active_tcc_for_student(self, *, session: Session, aluno_id: str) -> TCCRecord:
        tcc = session.scalar(
            select(TCCRecord)
            .join(PeriodoLetivoRecord, PeriodoLetivoRecord.id == TCCRecord.periodo_id)
            .where(
                TCCRecord.aluno_id == aluno_id,
                PeriodoLetivoRecord.ativo.is_(True),
            )
            .order_by(TCCRecord.criado_em.desc())
        )
        if tcc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_ACTIVE_TCC_DETAIL)
        return tcc

    async def _read_and_validate_file(self, upload: UploadFile) -> bytes:
        filename = Path(upload.filename or "").name
        if Path(filename).suffix.lower() not in DEPOSITO_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=INVALID_DEPOSITO_FILE_DETAIL)

        content = await upload.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Arquivo enviado esta vazio.")
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Arquivo excede o limite de 50 MB.",
            )
        return content

    def _write_file(self, *, base_dir: Path, upload: UploadFile, content: bytes, prefix: str) -> Path:
        base_dir.mkdir(parents=True, exist_ok=True)
        filename = self._safe_filename(upload.filename or prefix)
        path = base_dir / f"{prefix}-{uuid4().hex}-{filename}"
        path.write_bytes(content)
        return path

    def _build_preview_path(self, arquivo_path: Path) -> Path | None:
        if arquivo_path.suffix.lower() == ".pdf":
            return arquivo_path
        if arquivo_path.suffix.lower() != ".docx":
            return None
        return self._try_convert_docx_to_pdf(arquivo_path)

    def _try_convert_docx_to_pdf(self, arquivo_path: Path) -> Path | None:
        libreoffice = shutil.which("libreoffice") or shutil.which("soffice")
        if libreoffice is None:
            return None
        try:
            subprocess.run(
                [
                    libreoffice,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(arquivo_path.parent),
                    str(arquivo_path),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None

        pdf_path = arquivo_path.with_suffix(".pdf")
        return pdf_path if pdf_path.is_file() else None

    def _ensure_can_access_document(self, *, current_user: UserRecord, tcc: TCCRecord) -> None:
        if current_user.perfil == Perfil.COORDENADOR:
            return
        if current_user.perfil == Perfil.ALUNO and tcc.aluno_id == current_user.id:
            return
        if current_user.perfil == Perfil.ORIENTADOR and current_user.id in {tcc.orientador_id, tcc.coorientador_id}:
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=DEPOSITO_ACCESS_FORBIDDEN_DETAIL)

    def _build_response(self, *, session: Session, deposito_id: str) -> DepositoResponse:
        row = session.execute(
            select(DepositoFinalRecord, TCCRecord, UserRecord)
            .options(selectinload(DepositoFinalRecord.documentos))
            .join(TCCRecord, TCCRecord.id == DepositoFinalRecord.tcc_id)
            .join(UserRecord, UserRecord.id == TCCRecord.aluno_id)
            .where(DepositoFinalRecord.id == deposito_id)
        ).one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=DEPOSITO_NOT_FOUND_DETAIL)

        deposito, tcc, aluno = row
        documentos = sorted(deposito.documentos, key=lambda item: item.tipo_documento.value)
        final_document = next((doc for doc in documentos if doc.tipo_documento == TipoDocumentoDeposito.TCC_FINAL), None)
        return DepositoResponse(
            id=deposito.id,
            tcc_id=tcc.id,
            aluno_id=aluno.id,
            aluno_nome=aluno.nome_completo,
            titulo_tcc=tcc.titulo,
            status=deposito.status,
            versao_final_nome=final_document.nome_original if final_document is not None else None,
            documentos=[self._build_documento_response(documento) for documento in documentos],
            observacao_revisao=deposito.observacao_revisao,
            submetido_em=deposito.submetido_em,
            atualizado_em=deposito.atualizado_em,
        )

    def _build_empty_response(self, *, tcc: TCCRecord, aluno: UserRecord) -> DepositoResponse:
        return DepositoResponse(
            tcc_id=tcc.id,
            aluno_id=aluno.id,
            aluno_nome=aluno.nome_completo,
            titulo_tcc=tcc.titulo,
            status=StatusDeposito.AGUARDANDO_ENVIO,
            documentos=[],
        )

    def _build_documento_response(self, documento: DocumentoDepositoRecord) -> DocumentoDepositoResponse:
        return DocumentoDepositoResponse(
            id=documento.id,
            tipo_documento=documento.tipo_documento,
            nome_arquivo=documento.nome_original,
            mime_type=documento.mime_type,
            tamanho_bytes=documento.tamanho_bytes,
            possui_preview=bool(documento.caminho_preview_pdf),
            criado_em=documento.criado_em,
        )

    def _safe_filename(self, filename: str) -> str:
        name = Path(filename).name
        sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
        return sanitized or "arquivo"


async def get_deposito_service() -> DepositoService:
    return DepositoService()

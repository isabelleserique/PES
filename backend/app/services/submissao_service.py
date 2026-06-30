from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.core.config import Settings, get_settings
from backend.app.db.models import (
    ApresentacaoArtigoRecord,
    PeriodoLetivoRecord,
    PrazoEtapaRecord,
    SubmissaoEntregavelRecord,
    TCCRecord,
    UserRecord,
)
from backend.app.models.periodo import TipoTCC
from backend.app.models.user import Perfil
from backend.app.schemas.submissao import (
    ApresentacaoArtigoPayload,
    ApresentacaoArtigoResponse,
    SubmissaoAtrasadaResponse,
    SubmissaoEntregavelCreateResponse,
    SubmissaoEntregavelResponse,
    SubmissaoHistoricoResponse,
)
from backend.app.services.audit_service import AuditService
from backend.app.services.email_service import EmailService

NO_ACTIVE_PERIODO_FOUND_DETAIL = "Nenhum periodo letivo ativo encontrado."
NO_ACTIVE_TCC_DETAIL = "Aluno nao possui TCC no periodo letivo ativo."
ONLY_ARTIGO_PRESENTATION_DETAIL = "Registro de apresentacao disponivel apenas para TCC do tipo Artigo."
SUBMISSAO_NOT_FOUND_DETAIL = "Submissao nao encontrada."
SUBMISSAO_FILE_NOT_FOUND_DETAIL = "Arquivo da submissao nao encontrado."
SUBMISSAO_FILE_FORBIDDEN_DETAIL = "Perfil sem permissao para acessar o arquivo desta submissao."
COMPROVANTE_FILE_NOT_FOUND_DETAIL = "Comprovante da submissao nao encontrado."
INVALID_ETAPA_DETAIL = "Etapa de entrega invalida para o tipo de TCC do aluno."
COMPROVANTE_REQUIRED_DETAIL = "Comprovante de aceite e obrigatorio quando o artigo ja foi aceito."
PRESENTATION_DATA_REQUIRED_DETAIL = "Dados de apresentacao/publicacao sao obrigatorios quando o artigo ja foi aceito."
INVALID_FILE_DETAIL = "Arquivo deve estar nos formatos PDF ou DOCX."
INVALID_COMPROVANTE_FILE_DETAIL = "Comprovante deve estar nos formatos PDF, DOCX, JPG ou PNG."
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
DELIVERABLE_EXTENSIONS = {".pdf", ".docx"}
PROOF_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}

ETAPAS_BY_TIPO: dict[TipoTCC, tuple[str, ...]] = {
    TipoTCC.MONOGRAFIA: (
        "Revisão Bibliográfica",
        "1ª Entrega",
        "2ª Entrega",
        "Monografia Final",
    ),
    TipoTCC.RELATORIO_ESTAGIO: (
        "1º Entregável intermediário",
        "2º Entregável intermediário",
        "Relatório Final",
    ),
    TipoTCC.ARTIGO: (
        "1ª Entrega",
        "2ª Entrega",
        "Artigo Final",
    ),
}


@dataclass(frozen=True)
class SubmissionStoredFile:
    path: Path
    filename: str
    media_type: str


class SubmissaoService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def listar_entregaveis(
        self,
        *,
        session: Session,
        current_user: UserRecord,
    ) -> list[SubmissaoEntregavelResponse]:
        tcc = self._get_active_tcc(session=session, current_user=current_user, raise_if_missing=False)
        if tcc is None:
            return []

        submissoes = session.scalars(
            select(SubmissaoEntregavelRecord)
            .where(SubmissaoEntregavelRecord.tcc_id == tcc.id)
            .order_by(SubmissaoEntregavelRecord.criado_em.desc(), SubmissaoEntregavelRecord.versao.desc())
        ).all()
        ultimas_versoes = self._build_latest_version_map(submissoes)
        return [
            self._build_response(
                submissao,
                ultima_versao=submissao.versao == ultimas_versoes[(submissao.tcc_id, submissao.etapa)],
            )
            for submissao in submissoes
        ]

    def listar_historico_coordenador(
        self,
        *,
        session: Session,
        current_user: UserRecord,
    ) -> list[SubmissaoHistoricoResponse]:
        return self._listar_historico(session=session)

    def listar_historico_orientador(
        self,
        *,
        session: Session,
        current_user: UserRecord,
    ) -> list[SubmissaoHistoricoResponse]:
        return self._listar_historico(session=session, orientador_id=current_user.id)

    def get_arquivo_submissao(
        self,
        *,
        session: Session,
        current_user: UserRecord,
        submissao_id: str,
        comprovante: bool,
    ) -> SubmissionStoredFile:
        row = session.execute(
            select(SubmissaoEntregavelRecord, TCCRecord)
            .join(TCCRecord, TCCRecord.id == SubmissaoEntregavelRecord.tcc_id)
            .where(SubmissaoEntregavelRecord.id == submissao_id)
        ).one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=SUBMISSAO_NOT_FOUND_DETAIL)

        submissao, tcc = row
        self._ensure_can_access_submissao_file(current_user=current_user, submissao=submissao, tcc=tcc)

        if comprovante:
            if not submissao.caminho_comprovante or not submissao.nome_comprovante:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=COMPROVANTE_FILE_NOT_FOUND_DETAIL)
            path = Path(submissao.caminho_comprovante)
            media_type = submissao.tipo_conteudo_comprovante or "application/octet-stream"
            filename = submissao.nome_comprovante
            missing_detail = COMPROVANTE_FILE_NOT_FOUND_DETAIL
        else:
            path = Path(submissao.caminho_arquivo)
            media_type = submissao.tipo_conteudo or "application/octet-stream"
            filename = submissao.nome_arquivo
            missing_detail = SUBMISSAO_FILE_NOT_FOUND_DETAIL

        if not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=missing_detail)

        return SubmissionStoredFile(path=path, filename=filename, media_type=media_type)

    def listar_apresentacoes_artigo(
        self,
        *,
        session: Session,
        current_user: UserRecord,
    ) -> list[ApresentacaoArtigoResponse]:
        tcc = self._get_active_tcc(session=session, current_user=current_user, raise_if_missing=False)
        if tcc is None or tcc.tipo_tcc != TipoTCC.ARTIGO:
            return []

        apresentacoes = session.scalars(
            select(ApresentacaoArtigoRecord)
            .where(ApresentacaoArtigoRecord.tcc_id == tcc.id)
            .order_by(ApresentacaoArtigoRecord.data_apresentacao.desc(), ApresentacaoArtigoRecord.criado_em.desc())
        ).all()
        return [self._build_apresentacao_response(apresentacao) for apresentacao in apresentacoes]

    def registrar_apresentacao_artigo(
        self,
        *,
        session: Session,
        current_user: UserRecord,
        payload: ApresentacaoArtigoPayload,
        audit_service: AuditService,
    ) -> ApresentacaoArtigoResponse:
        tcc = self._get_active_tcc(session=session, current_user=current_user, raise_if_missing=True)
        if tcc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_ACTIVE_TCC_DETAIL)
        if tcc.tipo_tcc != TipoTCC.ARTIGO:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ONLY_ARTIGO_PRESENTATION_DETAIL)

        artigo_ja_aceito = session.scalar(
            select(SubmissaoEntregavelRecord.id).where(
                SubmissaoEntregavelRecord.tcc_id == tcc.id,
                SubmissaoEntregavelRecord.foi_aceito.is_(True),
            )
        ) is not None
        apresentacao = ApresentacaoArtigoRecord(
            id=str(uuid4()),
            tcc_id=tcc.id,
            aluno_id=current_user.id,
            data_apresentacao=payload.data_apresentacao,
            tipo_veiculo=self._normalize_optional_text(payload.tipo_veiculo),
            veiculo_publicacao=self._normalize_optional_text(payload.veiculo_publicacao),
            local_apresentacao=self._normalize_optional_text(payload.local_apresentacao),
            observacoes=self._normalize_optional_text(payload.observacoes),
            artigo_ja_aceito=artigo_ja_aceito,
        )
        session.add(apresentacao)
        session.commit()
        session.refresh(apresentacao)

        audit_service.log_event(
            session=session,
            user_id=current_user.id,
            action="REGISTRO_APRESENTACAO_ARTIGO",
            entity="SUBMISSAO",
            description="Registrou apresentacao de artigo.",
            data={
                "apresentacao_id": apresentacao.id,
                "tcc_id": tcc.id,
                "artigo_ja_aceito": artigo_ja_aceito,
            },
        )

        return self._build_apresentacao_response(apresentacao)

    async def submeter_entregavel(
        self,
        *,
        session: Session,
        current_user: UserRecord,
        etapa: str | None,
        arquivo: UploadFile,
        foi_aceito: bool,
        comprovante: UploadFile | None,
        apresentacao_data: date | None = None,
        apresentacao_tipo_veiculo: str | None = None,
        apresentacao_veiculo_publicacao: str | None = None,
        apresentacao_local: str | None = None,
        apresentacao_observacoes: str | None = None,
        email_service: EmailService | None = None,
    ) -> SubmissaoEntregavelCreateResponse:
        tcc = self._get_active_tcc(session=session, current_user=current_user, raise_if_missing=True)
        if tcc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_ACTIVE_TCC_DETAIL)

        etapa_normalizada = self._resolve_etapa(tipo_tcc=tcc.tipo_tcc, etapa=etapa)
        if tcc.tipo_tcc != TipoTCC.ARTIGO and foi_aceito:
            foi_aceito = False
            comprovante = None
            apresentacao_data = None
            apresentacao_tipo_veiculo = None
            apresentacao_veiculo_publicacao = None
            apresentacao_local = None
            apresentacao_observacoes = None
        if tcc.tipo_tcc == TipoTCC.ARTIGO and foi_aceito and comprovante is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=COMPROVANTE_REQUIRED_DETAIL)
        if tcc.tipo_tcc == TipoTCC.ARTIGO and foi_aceito:
            apresentacao_tipo_veiculo = self._normalize_optional_text(apresentacao_tipo_veiculo)
            apresentacao_veiculo_publicacao = self._normalize_optional_text(apresentacao_veiculo_publicacao)
            apresentacao_local = self._normalize_optional_text(apresentacao_local)
            apresentacao_observacoes = self._normalize_optional_text(apresentacao_observacoes)
            if apresentacao_data is None or not apresentacao_tipo_veiculo or not apresentacao_veiculo_publicacao:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=PRESENTATION_DATA_REQUIRED_DETAIL,
                )

        arquivo_bytes = await self._read_and_validate_file(
            upload=arquivo,
            allowed_extensions=DELIVERABLE_EXTENSIONS,
            invalid_detail=INVALID_FILE_DETAIL,
        )
        comprovante_bytes = None
        if comprovante is not None:
            comprovante_bytes = await self._read_and_validate_file(
                upload=comprovante,
                allowed_extensions=PROOF_EXTENSIONS,
                invalid_detail=INVALID_COMPROVANTE_FILE_DETAIL,
            )

        versao = self._next_version(session=session, tcc_id=tcc.id, etapa=etapa_normalizada)
        base_dir = self.settings.upload_dir / "submissoes-entregaveis" / tcc.id / self._safe_filename(etapa_normalizada) / f"v{versao}"
        base_dir.mkdir(parents=True, exist_ok=True)

        arquivo_path = self._write_file(base_dir=base_dir, upload=arquivo, content=arquivo_bytes, prefix="entregavel")
        comprovante_path = None
        if comprovante is not None and comprovante_bytes is not None:
            comprovante_path = self._write_file(
                base_dir=base_dir,
                upload=comprovante,
                content=comprovante_bytes,
                prefix="comprovante",
            )

        fora_do_prazo = self._is_submission_late(periodo=tcc.periodo, tipo_tcc=tcc.tipo_tcc, etapa=etapa_normalizada)
        submissao = SubmissaoEntregavelRecord(
            id=str(uuid4()),
            tcc_id=tcc.id,
            aluno_id=current_user.id,
            tipo_tcc=tcc.tipo_tcc,
            etapa=etapa_normalizada,
            versao=versao,
            nome_arquivo=Path(arquivo.filename or "entregavel").name,
            caminho_arquivo=str(arquivo_path),
            tipo_conteudo=arquivo.content_type,
            tamanho_bytes=len(arquivo_bytes),
            foi_aceito=foi_aceito,
            nome_comprovante=(
                Path(comprovante.filename).name
                if comprovante is not None and comprovante.filename
                else None
            ),
            caminho_comprovante=str(comprovante_path) if comprovante_path is not None else None,
            tipo_conteudo_comprovante=comprovante.content_type if comprovante is not None else None,
            tamanho_comprovante_bytes=len(comprovante_bytes) if comprovante_bytes is not None else None,
            fora_do_prazo=fora_do_prazo,
            nota_automatica=10 if tcc.tipo_tcc == TipoTCC.ARTIGO and foi_aceito else None,
        )
        session.add(submissao)
        if tcc.tipo_tcc == TipoTCC.ARTIGO and foi_aceito:
            session.add(
                ApresentacaoArtigoRecord(
                    id=str(uuid4()),
                    tcc_id=tcc.id,
                    aluno_id=current_user.id,
                    submissao_id=submissao.id,
                    data_apresentacao=apresentacao_data,
                    tipo_veiculo=apresentacao_tipo_veiculo,
                    veiculo_publicacao=apresentacao_veiculo_publicacao,
                    local_apresentacao=apresentacao_local,
                    observacoes=apresentacao_observacoes,
                    artigo_ja_aceito=True,
                )
            )
        session.commit()
        session.refresh(submissao)
        AuditService().log_event(
            session=session,
            user_id=current_user.id,
            action="UPLOAD_DOCUMENTO",
            entity="SUBMISSAO",
            description=f"Submeteu {submissao.etapa} do TCC.",
            data={
                "submissao_id": submissao.id,
                "tcc_id": tcc.id,
                "etapa": submissao.etapa,
                "versao": submissao.versao,
                "arquivo": submissao.nome_arquivo,
                "fora_do_prazo": submissao.fora_do_prazo,
                "artigo_ja_aceito": submissao.foi_aceito,
            },
        )
        self._send_grade_notification_if_needed(
            email_service=email_service,
            aluno=current_user,
            tcc=tcc,
            submissao=submissao,
        )

        return SubmissaoEntregavelCreateResponse(
            id=submissao.id,
            tipo_tcc=submissao.tipo_tcc.value,
            etapa=submissao.etapa,
            versao=submissao.versao,
            mensagem="Entregavel submetido com sucesso.",
            nota_automatica=submissao.nota_automatica,
        )

    def _get_active_tcc(
        self,
        *,
        session: Session,
        current_user: UserRecord,
        raise_if_missing: bool,
    ) -> TCCRecord | None:
        periodo = self._get_active_periodo_record(session=session)
        tcc = session.scalar(
            select(TCCRecord)
            .options(selectinload(TCCRecord.periodo).selectinload(PeriodoLetivoRecord.prazos))
            .where(
                TCCRecord.aluno_id == current_user.id,
                TCCRecord.periodo_id == periodo.id,
            )
        )
        if tcc is None and raise_if_missing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_ACTIVE_TCC_DETAIL)
        return tcc

    def _get_active_periodo_record(self, *, session: Session) -> PeriodoLetivoRecord:
        periodo = session.scalar(
            select(PeriodoLetivoRecord)
            .options(selectinload(PeriodoLetivoRecord.prazos))
            .where(PeriodoLetivoRecord.ativo.is_(True))
            .order_by(PeriodoLetivoRecord.data_inicio.desc())
        )
        if periodo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_ACTIVE_PERIODO_FOUND_DETAIL)
        return periodo

    def _resolve_etapa(self, *, tipo_tcc: TipoTCC, etapa: str | None) -> str:
        etapas = ETAPAS_BY_TIPO.get(tipo_tcc, ())
        if not etapas:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=INVALID_ETAPA_DETAIL)

        normalized = self._normalize_text(etapa or "")
        for allowed in etapas:
            if self._normalize_text(allowed) == normalized:
                return allowed
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=INVALID_ETAPA_DETAIL)

    def _next_version(self, *, session: Session, tcc_id: str, etapa: str) -> int:
        current_version = session.scalar(
            select(func.max(SubmissaoEntregavelRecord.versao)).where(
                SubmissaoEntregavelRecord.tcc_id == tcc_id,
                SubmissaoEntregavelRecord.etapa == etapa,
            )
        )
        return int(current_version or 0) + 1

    async def _read_and_validate_file(
        self,
        *,
        upload: UploadFile,
        allowed_extensions: set[str],
        invalid_detail: str,
    ) -> bytes:
        filename = Path(upload.filename or "").name
        extension = Path(filename).suffix.lower()
        if extension not in allowed_extensions:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=invalid_detail)

        content = await upload.read()
        if len(content) == 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Arquivo enviado esta vazio.")
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Arquivo excede o limite de 50 MB.",
            )
        return content

    def _write_file(self, *, base_dir: Path, upload: UploadFile, content: bytes, prefix: str) -> Path:
        filename = self._safe_filename(upload.filename or prefix)
        path = base_dir / f"{prefix}-{uuid4().hex}-{filename}"
        path.write_bytes(content)
        return path

    def _safe_filename(self, filename: str) -> str:
        name = Path(filename).name
        sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
        return sanitized or "arquivo"

    def _is_submission_late(self, *, periodo: PeriodoLetivoRecord, tipo_tcc: TipoTCC, etapa: str) -> bool:
        prazo = self._find_deadline(periodo=periodo, tipo_tcc=tipo_tcc, etapa=etapa)
        if prazo is None:
            return False
        return date.today() > prazo.data_limite

    def _find_deadline(self, *, periodo: PeriodoLetivoRecord, tipo_tcc: TipoTCC, etapa: str) -> PrazoEtapaRecord | None:
        etapa_normalizada = self._normalize_text(etapa)
        matching = [
            prazo
            for prazo in periodo.prazos
            if prazo.tipo_tcc in {TipoTCC.TODOS, tipo_tcc}
            and self._deadline_matches_etapa(prazo.nome_etapa, etapa_normalizada)
        ]
        if not matching:
            return None
        return min(matching, key=lambda prazo: (prazo.data_limite, prazo.nome_etapa.casefold(), prazo.id))

    def _deadline_matches_etapa(self, nome_etapa: str, etapa_normalizada: str) -> bool:
        nome_normalizado = self._normalize_text(nome_etapa)
        if "artigo" in etapa_normalizada and "artigo" in nome_normalizado:
            return True
        return etapa_normalizada in nome_normalizado or nome_normalizado in etapa_normalizada

    def _normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.strip().casefold())
        without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
        return " ".join(without_accents.split())

    def _normalize_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None

    def listar_submissoes_atrasadas(
        self,
        *,
        session: Session,
    ) -> list[SubmissaoAtrasadaResponse]:
        rows = session.execute(
            select(SubmissaoEntregavelRecord, TCCRecord, UserRecord)
            .join(TCCRecord, TCCRecord.id == SubmissaoEntregavelRecord.tcc_id)
            .join(UserRecord, UserRecord.id == TCCRecord.aluno_id)
            .options(selectinload(SubmissaoEntregavelRecord.tcc).selectinload(TCCRecord.periodo).selectinload(PeriodoLetivoRecord.prazos))
            .where(SubmissaoEntregavelRecord.fora_do_prazo.is_(True))
            .order_by(SubmissaoEntregavelRecord.criado_em.desc())
        ).all()

        resultados: list[SubmissaoAtrasadaResponse] = []
        for submissao, tcc, aluno in rows:
            prazo = self._find_deadline(periodo=tcc.periodo, tipo_tcc=tcc.tipo_tcc, etapa=submissao.etapa)
            if prazo is None:
                continue

            data_submissao = submissao.criado_em.date()
            dias_atraso = max((data_submissao - prazo.data_limite).days, 0)
            if dias_atraso <= 0:
                continue

            resultados.append(
                SubmissaoAtrasadaResponse(
                    id=submissao.id,
                    aluno_id=aluno.id,
                    aluno_nome=aluno.nome_completo,
                    matricula=aluno.matricula,
                    tcc_id=tcc.id,
                    titulo_tcc=tcc.titulo,
                    tipo_tcc=submissao.tipo_tcc.value,
                    etapa=submissao.etapa,
                    versao=submissao.versao,
                    nome_arquivo=submissao.nome_arquivo,
                    data_limite=prazo.data_limite,
                    data_submissao=submissao.criado_em,
                    dias_atraso=dias_atraso,
                )
            )

        return resultados

    def _ensure_can_access_submissao_file(
        self,
        *,
        current_user: UserRecord,
        submissao: SubmissaoEntregavelRecord,
        tcc: TCCRecord,
    ) -> None:
        if current_user.perfil == Perfil.COORDENADOR:
            return
        if current_user.perfil == Perfil.ALUNO and submissao.aluno_id == current_user.id:
            return
        if current_user.perfil == Perfil.ORIENTADOR and current_user.id in {tcc.orientador_id, tcc.coorientador_id}:
            return

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SUBMISSAO_FILE_FORBIDDEN_DETAIL)

    def _listar_historico(
        self,
        *,
        session: Session,
        orientador_id: str | None = None,
    ) -> list[SubmissaoHistoricoResponse]:
        statement = (
            select(SubmissaoEntregavelRecord, TCCRecord, UserRecord)
            .join(TCCRecord, TCCRecord.id == SubmissaoEntregavelRecord.tcc_id)
            .join(UserRecord, UserRecord.id == TCCRecord.aluno_id)
            .order_by(
                SubmissaoEntregavelRecord.criado_em.desc(),
                SubmissaoEntregavelRecord.versao.desc(),
                SubmissaoEntregavelRecord.etapa.asc(),
            )
        )
        if orientador_id is not None:
            statement = statement.where(
                (TCCRecord.orientador_id == orientador_id)
                | (TCCRecord.coorientador_id == orientador_id)
            )

        rows = session.execute(statement).all()
        ultimas_versoes = self._build_latest_version_map([submissao for submissao, _, _ in rows])
        return [
            self._build_historico_response(
                submissao=submissao,
                tcc=tcc,
                aluno=aluno,
                ultima_versao=submissao.versao == ultimas_versoes[(submissao.tcc_id, submissao.etapa)],
            )
            for submissao, tcc, aluno in rows
        ]

    def _build_latest_version_map(self, submissoes) -> dict[tuple[str, str], int]:
        ultimas_versoes: dict[tuple[str, str], int] = {}
        for submissao in submissoes:
            chave = (submissao.tcc_id, submissao.etapa)
            ultimas_versoes[chave] = max(ultimas_versoes.get(chave, 0), submissao.versao)
        return ultimas_versoes

    def _build_response(
        self,
        submissao: SubmissaoEntregavelRecord,
        *,
        ultima_versao: bool,
    ) -> SubmissaoEntregavelResponse:
        return SubmissaoEntregavelResponse(
            id=submissao.id,
            tipo_tcc=submissao.tipo_tcc.value,
            etapa=submissao.etapa,
            versao=submissao.versao,
            nome_arquivo=submissao.nome_arquivo,
            data_submissao=submissao.criado_em,
            fora_do_prazo=submissao.fora_do_prazo,
            foi_aceito=submissao.foi_aceito,
            ultima_versao=ultima_versao,
            nome_comprovante=submissao.nome_comprovante,
            nota_automatica=submissao.nota_automatica,
        )

    def _build_historico_response(
        self,
        *,
        submissao: SubmissaoEntregavelRecord,
        tcc: TCCRecord,
        aluno: UserRecord,
        ultima_versao: bool,
    ) -> SubmissaoHistoricoResponse:
        return SubmissaoHistoricoResponse(
            id=submissao.id,
            aluno_id=aluno.id,
            aluno_nome=aluno.nome_completo,
            matricula=aluno.matricula,
            tcc_id=tcc.id,
            titulo_tcc=tcc.titulo,
            tipo_tcc=submissao.tipo_tcc.value,
            etapa=submissao.etapa,
            versao=submissao.versao,
            nome_arquivo=submissao.nome_arquivo,
            data_submissao=submissao.criado_em,
            fora_do_prazo=submissao.fora_do_prazo,
            foi_aceito=submissao.foi_aceito,
            ultima_versao=ultima_versao,
            nome_comprovante=submissao.nome_comprovante,
            nota_automatica=submissao.nota_automatica,
        )

    def _build_apresentacao_response(
        self,
        apresentacao: ApresentacaoArtigoRecord,
    ) -> ApresentacaoArtigoResponse:
        return ApresentacaoArtigoResponse(
            id=apresentacao.id,
            tcc_id=apresentacao.tcc_id,
            submissao_id=apresentacao.submissao_id,
            data_apresentacao=apresentacao.data_apresentacao,
            tipo_veiculo=apresentacao.tipo_veiculo,
            veiculo_publicacao=apresentacao.veiculo_publicacao,
            local_apresentacao=apresentacao.local_apresentacao,
            observacoes=apresentacao.observacoes,
            artigo_ja_aceito=apresentacao.artigo_ja_aceito,
            criado_em=apresentacao.criado_em,
        )

    def _send_grade_notification_if_needed(
        self,
        *,
        email_service: EmailService | None,
        aluno: UserRecord,
        tcc: TCCRecord,
        submissao: SubmissaoEntregavelRecord,
    ) -> None:
        if email_service is None or submissao.nota_automatica is None:
            return

        is_final = "final" in self._normalize_text(submissao.etapa)
        if is_final and not aluno.email_notas_finais:
            return
        if not is_final and not aluno.email_notas_parciais:
            return

        email_service.send_grade_notification(
            to_email=aluno.email,
            aluno_nome=aluno.nome_completo,
            titulo=tcc.titulo,
            etapa=submissao.etapa,
            nota=submissao.nota_automatica,
        )


async def get_submissao_service() -> SubmissaoService:
    return SubmissaoService()

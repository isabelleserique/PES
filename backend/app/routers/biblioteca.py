from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.api.deps import require_perfis
from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.models.deposito import TipoDocumentoDeposito
from backend.app.models.user import Perfil
from backend.app.schemas.deposito import DepositoResponse, DepositoStatusUpdateRequest
from backend.app.services.audit_service import AuditService, get_audit_service
from backend.app.services.deposito_service import DepositoService, get_deposito_service
from backend.app.services.email_service import EmailService, get_email_service

router = APIRouter(prefix="/biblioteca", tags=["biblioteca"])


@router.post(
    "/deposito",
    status_code=status.HTTP_201_CREATED,
)
async def submeter_deposito(
    versao_final: UploadFile = File(...),
    documento_ata_defesa: UploadFile = File(...),
    documento_folha_aprovacao: UploadFile = File(...),
    documento_formularios: UploadFile = File(...),
    documento_declaracoes: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    deposito_service: DepositoService = Depends(get_deposito_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_aluno: UserRecord = Depends(require_perfis(Perfil.ALUNO)),
) -> DepositoResponse:
    return await deposito_service.submeter_deposito(
        session=session,
        current_user=current_aluno,
        documentos={
            TipoDocumentoDeposito.TCC_FINAL: versao_final,
            TipoDocumentoDeposito.ATA_DEFESA: documento_ata_defesa,
            TipoDocumentoDeposito.FOLHA_APROVACAO: documento_folha_aprovacao,
            TipoDocumentoDeposito.FORMULARIOS: documento_formularios,
            TipoDocumentoDeposito.DECLARACOES: documento_declaracoes,
        },
        audit_service=audit_service,
    )


@router.get(
    "/deposito/me",
    status_code=status.HTTP_200_OK,
)
async def buscar_meu_deposito(
    session: Session = Depends(get_db_session),
    deposito_service: DepositoService = Depends(get_deposito_service),
    current_aluno: UserRecord = Depends(require_perfis(Perfil.ALUNO)),
) -> DepositoResponse:
    return deposito_service.get_meu_deposito(session=session, current_user=current_aluno)


@router.get(
    "/depositos",
    status_code=status.HTTP_200_OK,
)
async def listar_depositos(
    session: Session = Depends(get_db_session),
    deposito_service: DepositoService = Depends(get_deposito_service),
    current_coordenador: UserRecord = Depends(require_perfis(Perfil.COORDENADOR)),
) -> list[DepositoResponse]:
    _ = current_coordenador
    return deposito_service.listar_depositos(session=session)


@router.patch(
    "/deposito/{deposito_id}/status",
    status_code=status.HTTP_200_OK,
)
async def atualizar_status_deposito(
    deposito_id: str,
    payload: DepositoStatusUpdateRequest,
    session: Session = Depends(get_db_session),
    deposito_service: DepositoService = Depends(get_deposito_service),
    email_service: EmailService = Depends(get_email_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_coordenador: UserRecord = Depends(require_perfis(Perfil.COORDENADOR)),
) -> DepositoResponse:
    return deposito_service.atualizar_status(
        session=session,
        current_user=current_coordenador,
        deposito_id=deposito_id,
        status_deposito=payload.status,
        observacao_revisao=payload.observacao_revisao,
        email_service=email_service,
        audit_service=audit_service,
    )


@router.get(
    "/deposito/documentos/{documento_id}/arquivo",
    status_code=status.HTTP_200_OK,
)
async def visualizar_documento_deposito(
    documento_id: str,
    preview: bool = False,
    session: Session = Depends(get_db_session),
    deposito_service: DepositoService = Depends(get_deposito_service),
    current_user: UserRecord = Depends(require_perfis(Perfil.ALUNO, Perfil.ORIENTADOR, Perfil.COORDENADOR)),
) -> FileResponse:
    arquivo = deposito_service.get_documento(
        session=session,
        current_user=current_user,
        documento_id=documento_id,
        preview=preview,
    )
    return FileResponse(
        path=arquivo.path,
        media_type=arquivo.media_type,
        filename=arquivo.filename,
        content_disposition_type="inline",
    )

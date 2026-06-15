from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import require_perfis
from backend.app.db.models import AuditLogRecord, UserRecord
from backend.app.db.session import get_db_session
from backend.app.models.user import Perfil
from backend.app.schemas.audit import AuditLogResponse

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
)
async def listar_logs(
    acao: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
    current_coordenador: UserRecord = Depends(require_perfis(Perfil.COORDENADOR)),
) -> list[AuditLogResponse]:
    _ = current_coordenador
    statement = (
        select(AuditLogRecord, UserRecord)
        .join(UserRecord, UserRecord.id == AuditLogRecord.user_id, isouter=True)
        .order_by(AuditLogRecord.criado_em.desc())
    )
    if acao:
        statement = statement.where(AuditLogRecord.acao == acao)
    if user_id:
        statement = statement.where(AuditLogRecord.user_id == user_id)

    rows = session.execute(statement).all()
    return [
        AuditLogResponse(
            id=log.id,
            usuario_nome=user.nome_completo if user is not None else "Usuario removido",
            usuario_email=user.email if user is not None else "-",
            usuario_perfil=user.perfil.value if user is not None else "-",
            acao=log.acao,
            entidade=log.entidade,
            descricao=log.descricao,
            criado_em=log.criado_em,
        )
        for log, user in rows
    ]

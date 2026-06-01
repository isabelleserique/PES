from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import require_admin
from backend.app.db.models import AuditLogRecord
from backend.app.db.session import get_db_session
from backend.app.db.models import UserRecord
from datetime import datetime
from fastapi import Query

router = APIRouter(prefix="/logs", tags=["Audit Logs"])


@router.get("/")
def list_logs(
    user: UserRecord = Depends(require_admin),
    session: Session = Depends(get_db_session),
    user_id: str | None = Query(None),
    action: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
):
    query = select(AuditLogRecord)

    if user_id:
        query = query.where(AuditLogRecord.user_id == user_id)

    if action:
        query = query.where(AuditLogRecord.acao == action)

    if start_date:
        query = query.where(AuditLogRecord.criado_em >= start_date)

    if end_date:
        query = query.where(AuditLogRecord.criado_em <= end_date)

    query = query.order_by(AuditLogRecord.criado_em.desc())

    logs = session.scalars(query).all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "acao": log.acao,
            "entidade": log.entidade,
            "dados": log.dados,
            "data": log.criado_em.date().isoformat(),
            "hora": log.criado_em.time().isoformat(),
        }
        for log in logs
    ]
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.db.models import UserRecord
from backend.app.models.user import Perfil
from backend.app.schemas.user import CoordenadorCreateRequest, UserCreatedResponse
from backend.app.services.audit_service import AuditService
from backend.app.services.email_service import EmailService

CONFLICT_DETAIL = "Nao foi possivel concluir o cadastro com os dados informados."


class UserService:
    def create_coordenador(
        self,
        *,
        session: Session,
        payload: CoordenadorCreateRequest,
        email_service: EmailService,
        audit_service: AuditService,
    ) -> UserCreatedResponse:
        normalized_username = payload.username.strip().lower()

        existing_user = session.scalar(
            select(UserRecord).where(
                or_(
                    UserRecord.email == payload.email,
                    UserRecord.username == normalized_username,
                )
            )
        )
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=CONFLICT_DETAIL,
            )

        user = UserRecord(
            id=str(uuid4()),
            nome_completo=payload.nome_completo,
            email=payload.email,
            username=normalized_username,
            senha_hash=hash_password(payload.senha),
            perfil=Perfil.COORDENADOR,
            ativo=True,
        )

        session.add(user)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=CONFLICT_DETAIL,
            ) from exc

        session.refresh(user)
        audit_service.log_user_registration(user_id=user.id, perfil=user.perfil)
        email_service.send_welcome_email(
            to_email=user.email,
            full_name=user.nome_completo,
            username=user.username,
            temporary_password=payload.senha,
        )
        return UserCreatedResponse.model_validate(user)

async def get_user_service() -> UserService:
    return UserService()

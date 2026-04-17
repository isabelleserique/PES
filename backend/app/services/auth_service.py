from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.core.security import create_access_token, verify_password
from backend.app.db.models import UserRecord
from backend.app.models.user import StatusCadastro
from backend.app.schemas.auth import AuthenticatedUserResponse, LoginRequest, LoginResponse
from backend.app.services.audit_service import AuditService

INVALID_CREDENTIALS_DETAIL = "Credenciais invalidas."
PENDING_REGISTRATION_DETAIL = "Seu cadastro ainda esta em analise. Aguarde aprovacao."
INACTIVE_REGISTRATION_DETAIL = "Seu acesso nao esta disponivel."
ACCOUNT_BLOCKED_DETAIL = "Conta temporariamente bloqueada. Tente novamente em 15 minutos."
MAX_FAILED_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCK_MINUTES = 15


class AuthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def login(
        self,
        *,
        session: Session,
        payload: LoginRequest,
        audit_service: AuditService,
    ) -> LoginResponse:
        user = session.scalar(select(UserRecord).where(UserRecord.email == payload.email))
        if user is None:
            audit_service.log_login_failed(email=payload.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_CREDENTIALS_DETAIL,
            )

        now = datetime.now(UTC)
        self._clear_expired_block(session=session, user=user, reference_time=now)

        if user.blocked_until is not None and user.blocked_until.replace(tzinfo=UTC) > now:
            audit_service.log_login_blocked(
                user_id=user.id,
                email=user.email,
                blocked_until=user.blocked_until,
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=ACCOUNT_BLOCKED_DETAIL,
            )

        if verify_password(payload.senha, user.senha_hash) is not True:
            self._register_failed_login(
                session=session,
                user=user,
                reference_time=now,
            )
            audit_service.log_login_failed(
                email=user.email,
                user_id=user.id,
                attempt_count=user.failed_login_attempts,
                blocked_until=user.blocked_until,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_CREDENTIALS_DETAIL,
            )

        if user.status == StatusCadastro.PENDENTE:
            audit_service.log_login_denied(
                user_id=user.id,
                email=user.email,
                reason=StatusCadastro.PENDENTE.value,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=PENDING_REGISTRATION_DETAIL,
            )

        if user.status != StatusCadastro.ATIVO or user.ativo is not True:
            audit_service.log_login_denied(
                user_id=user.id,
                email=user.email,
                reason=user.status.value,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=INACTIVE_REGISTRATION_DETAIL,
            )

        self._reset_login_attempts(session=session, user=user)
        expires_at = now + timedelta(hours=self.settings.session_timeout_hours)
        access_token = create_access_token(
            payload={
                "user_id": user.id,
                "perfil": user.perfil.value,
            },
            secret_key=self.settings.jwt_secret,
            expires_delta=timedelta(hours=self.settings.session_timeout_hours),
            algorithm=self.settings.jwt_algorithm,
        )

        audit_service.log_login_success(user_id=user.id, perfil=user.perfil)
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_at=expires_at,
            user=AuthenticatedUserResponse(
                id=user.id,
                nome_completo=user.nome_completo,
                email=user.email,
                perfil=user.perfil,
            ),
        )

    def _register_failed_login(
        self,
        *,
        session: Session,
        user: UserRecord,
        reference_time: datetime,
    ) -> None:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            user.blocked_until = (reference_time + timedelta(minutes=ACCOUNT_LOCK_MINUTES)).replace(tzinfo=None)
        session.commit()
        session.refresh(user)

    def _reset_login_attempts(self, *, session: Session, user: UserRecord) -> None:
        user.failed_login_attempts = 0
        user.blocked_until = None
        session.commit()
        session.refresh(user)

    def _clear_expired_block(
        self,
        *,
        session: Session,
        user: UserRecord,
        reference_time: datetime,
    ) -> None:
        if user.blocked_until is None:
            return
        if user.blocked_until.replace(tzinfo=UTC) > reference_time:
            return

        user.failed_login_attempts = 0
        user.blocked_until = None
        session.commit()
        session.refresh(user)


async def get_auth_service() -> AuthService:
    return AuthService(get_settings())

from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.db.models import UserRecord
from backend.app.models.user import Perfil, StatusCadastro
from backend.app.schemas.user import (
    AuthenticatedUserProfileResponse,
    CadastroApprovalRequest,
    CadastroApprovalResponse,
    CoordenadorCreateRequest,
    PendingRegistrationResponse,
    SolicitarCadastroRequest,
    SolicitarCadastroResponse,
    UserCreatedResponse,
)
from backend.app.services.audit_service import AuditService
from backend.app.services.email_service import EmailService

CONFLICT_DETAIL = "Nao foi possivel concluir o cadastro com os dados informados."
REGISTRATION_REVIEW_CONFLICT_DETAIL = "Solicitacao de cadastro nao esta pendente."
INVALID_REGISTRATION_TARGET_DETAIL = "Cadastro informado nao pode ser avaliado por este endpoint."


class UserService:
    def get_authenticated_profile(self, *, current_user: UserRecord) -> AuthenticatedUserProfileResponse:
        return AuthenticatedUserProfileResponse.model_validate(current_user)

    def create_coordenador(
        self,
        *,
        session: Session,
        payload: CoordenadorCreateRequest,
        email_service: EmailService,
        audit_service: AuditService,
    ) -> UserCreatedResponse:
        normalized_username = payload.username.strip().lower()
        self._ensure_user_uniqueness(
            session=session,
            email=payload.email,
            username=normalized_username,
        )

        user = UserRecord(
            id=str(uuid4()),
            nome_completo=payload.nome_completo,
            email=payload.email,
            username=normalized_username,
            senha_hash=hash_password(payload.senha),
            perfil=Perfil.COORDENADOR,
            matricula=None,
            status=StatusCadastro.ATIVO,
            failed_login_attempts=0,
            blocked_until=None,
            ativo=True,
        )

        self._persist_user(session=session, user=user)
        audit_service.log_user_registration(user_id=user.id, perfil=user.perfil)
        email_service.send_welcome_email(
            to_email=user.email,
            full_name=user.nome_completo,
            username=user.username,
            temporary_password=payload.senha,
        )
        return UserCreatedResponse.model_validate(user)

    def request_registration(
        self,
        *,
        session: Session,
        payload: SolicitarCadastroRequest,
        email_service: EmailService,
        audit_service: AuditService,
    ) -> SolicitarCadastroResponse:
        normalized_username = payload.username.strip().lower()
        self._ensure_user_uniqueness(
            session=session,
            email=payload.email,
            username=normalized_username,
        )

        user = UserRecord(
            id=str(uuid4()),
            nome_completo=payload.nome_completo,
            email=payload.email,
            username=normalized_username,
            senha_hash=hash_password(payload.senha),
            perfil=payload.perfil,
            matricula=payload.matricula if payload.perfil == Perfil.ALUNO else None,
            status=StatusCadastro.PENDENTE,
            failed_login_attempts=0,
            blocked_until=None,
            ativo=False,
        )

        self._persist_user(session=session, user=user)
        audit_service.log_registration_request(user_id=user.id, perfil=user.perfil)
        self._notify_active_coordenadores(
            session=session,
            email_service=email_service,
            requester=user,
        )
        return SolicitarCadastroResponse(
            id=user.id,
            nome_completo=user.nome_completo,
            status=user.status,
            mensagem="Seu cadastro esta em analise. Aguarde aprovacao.",
        )

    def review_registration(
        self,
        *,
        session: Session,
        target_user_id: str,
        payload: CadastroApprovalRequest,
        acted_by: UserRecord,
        email_service: EmailService,
        audit_service: AuditService,
    ) -> CadastroApprovalResponse:
        user = session.scalar(select(UserRecord).where(UserRecord.id == target_user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario nao encontrado.",
            )
        if user.perfil == Perfil.COORDENADOR:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=INVALID_REGISTRATION_TARGET_DETAIL,
            )
        if user.status != StatusCadastro.PENDENTE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=REGISTRATION_REVIEW_CONFLICT_DETAIL,
            )

        if payload.acao == "APROVAR":
            user.status = StatusCadastro.ATIVO
            user.ativo = True
        else:
            user.status = StatusCadastro.REJEITADO
            user.ativo = False

        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Nao foi possivel atualizar a solicitacao informada.",
            ) from exc

        session.refresh(user)
        audit_service.log_registration_decision(
            actor_user_id=acted_by.id,
            target_user_id=user.id,
            decision=payload.acao,
            resulting_status=user.status,
        )
        if payload.acao == "APROVAR":
            email_service.send_registration_approved_email(
                to_email=user.email,
                full_name=user.nome_completo,
                username=user.username,
            )
        return CadastroApprovalResponse.model_validate(user)

    def list_pending_registrations(self, *, session: Session) -> list[PendingRegistrationResponse]:
        pending_users = session.scalars(
            select(UserRecord)
            .where(UserRecord.status == StatusCadastro.PENDENTE)
            .order_by(UserRecord.criado_em.asc(), UserRecord.nome_completo.asc())
        ).all()
        return [PendingRegistrationResponse.model_validate(user) for user in pending_users]

    def _ensure_user_uniqueness(self, *, session: Session, email: str, username: str) -> None:
        existing_user = session.scalar(
            select(UserRecord).where(
                or_(
                    UserRecord.email == email,
                    UserRecord.username == username,
                )
            )
        )
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=CONFLICT_DETAIL,
            )

    def _persist_user(self, *, session: Session, user: UserRecord) -> None:
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

    def _notify_active_coordenadores(
        self,
        *,
        session: Session,
        email_service: EmailService,
        requester: UserRecord,
    ) -> None:
        coordenadores = session.scalars(
            select(UserRecord).where(
                UserRecord.perfil == Perfil.COORDENADOR,
                UserRecord.status == StatusCadastro.ATIVO,
                UserRecord.ativo.is_(True),
            )
        ).all()

        for coordenador in coordenadores:
            email_service.send_pending_registration_notification(
                to_email=coordenador.email,
                requester_name=requester.nome_completo,
                requester_email=requester.email,
                requester_username=requester.username,
                requester_profile=requester.perfil.value,
            )


async def get_user_service() -> UserService:
    return UserService()

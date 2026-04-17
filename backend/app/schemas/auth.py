from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from backend.app.models.user import Perfil


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        normalized = str(value).strip().lower()
        if not normalized:
            raise ValueError("Campo obrigatorio.")
        return normalized

    @field_validator("senha")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Campo obrigatorio.")
        return value


class AuthenticatedUserResponse(BaseModel):
    id: str
    nome_completo: str
    email: str
    perfil: Perfil


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    user: AuthenticatedUserResponse


class PasswordResetRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        normalized = str(value).strip().lower()
        if not normalized:
            raise ValueError("Campo obrigatorio.")
        return normalized


class PasswordResetRequestResponse(BaseModel):
    mensagem: str


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(max_length=255)
    nova_senha: str = Field(max_length=255)

    @field_validator("token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Campo obrigatorio.")
        return normalized

    @field_validator("nova_senha")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Campo obrigatorio.")
        if len(value) < 8:
            raise ValueError("Senha deve ter no minimo 8 caracteres.")
        return value


class PasswordResetConfirmResponse(BaseModel):
    mensagem: str


class AccessTokenPayload(BaseModel):
    user_id: str
    perfil: Perfil
    exp: int

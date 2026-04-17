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


class AccessTokenPayload(BaseModel):
    user_id: str
    perfil: Perfil
    exp: int

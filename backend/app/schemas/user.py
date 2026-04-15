from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from backend.app.models.user import Perfil, StatusCadastro


class UserBaseRequest(BaseModel):
    nome_completo: str = Field(min_length=1, max_length=255)
    email: EmailStr
    username: str = Field(min_length=1, max_length=100)
    senha: str = Field(min_length=8, max_length=255)

    @field_validator("nome_completo", "username")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Campo obrigatorio.")
        return normalized

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
        if len(value) < 8:
            raise ValueError("Senha deve ter no minimo 8 caracteres.")
        return value


class CoordenadorCreateRequest(UserBaseRequest):
    pass


class SolicitarCadastroRequest(UserBaseRequest):
    perfil: Perfil
    matricula: Optional[str] = Field(default=None, max_length=50)

    @field_validator("matricula")
    @classmethod
    def normalize_matricula(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            return None
        return normalized

    @model_validator(mode="after")
    def validate_profile_constraints(self) -> "SolicitarCadastroRequest":
        if self.perfil == Perfil.COORDENADOR:
            raise ValueError("Auto-cadastro nao permite perfil COORDENADOR.")
        if self.perfil == Perfil.ALUNO and not self.matricula:
            raise ValueError("Matricula e obrigatoria para perfil ALUNO.")
        return self


class CadastroApprovalRequest(BaseModel):
    acao: str = Field(min_length=1, max_length=20)

    @field_validator("acao")
    @classmethod
    def normalize_action(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"APROVAR", "REJEITAR"}:
            raise ValueError("Acao invalida. Use APROVAR ou REJEITAR.")
        return normalized


class UserCreatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome_completo: str


class SolicitarCadastroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome_completo: str
    status: StatusCadastro
    mensagem: str


class CadastroApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome_completo: str
    perfil: Perfil
    status: StatusCadastro

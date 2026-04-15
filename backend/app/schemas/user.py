from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CoordenadorCreateRequest(BaseModel):
    nome_completo: str = Field(min_length=1, max_length=255)
    email: EmailStr
    username: str = Field(min_length=1, max_length=100)
    senha: str = Field(min_length=1, max_length=255)

    @field_validator("nome_completo", "username")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Campo obrigatório.")
        return normalized

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        normalized = str(value).strip().lower()
        if not normalized:
            raise ValueError("Campo obrigatório.")
        return normalized

    @field_validator("senha")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Campo obrigatório.")
        return value


class UserCreatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome_completo: str

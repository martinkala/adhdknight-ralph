from pydantic import BaseModel, EmailStr, field_validator, ConfigDict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    # Required when REGISTRATION_MODE=invite, ignored when open.
    invite_token: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user@example.com", "password": "secret123", "invite_token": "Xy3..."}
        }
    )

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    schema_version: str = "1.0"
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schema_version": "1.0",
                "access_token": "eyJ...",
                "refresh_token": "eyJ...",
                "token_type": "bearer",
                "expires_in": 900,
            }
        }
    )


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"old_password": "secret123", "new_password": "new-secret-456"}}
    )

    @field_validator("new_password")
    @classmethod
    def new_password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

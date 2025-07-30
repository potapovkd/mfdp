"""Структуры данных для приложения."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JWTPayloadDTO(BaseModel):
    """DTO для полезной нагрузки JWT токена."""

    id: int
    exp: Optional[int] = None  # Unix timestamp вместо datetime
    type: Optional[str] = None


class TokenResponse(BaseModel):
    """Ответ с токенами."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None

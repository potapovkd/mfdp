"""Структуры данных для формализации запросов и ответов API."""

from typing import Literal

from pydantic import BaseModel


class JWTPayloadDTO(BaseModel):
    """DTO с данными для создания JWT."""

    id: int


class JWTPayloadExtendedDTO(JWTPayloadDTO):
    """DTO с данными JWT."""

    token_type: Literal["access", "refresh"]
    exp: int


class AccessTokenDTO(BaseModel):
    """DTO с access_token."""

    access_token: str


class TokenPairDTO(AccessTokenDTO):
    """DTO с access и refresh токеном."""

    refresh_token: str

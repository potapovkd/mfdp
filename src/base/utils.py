"""Утилиты."""

from datetime import datetime, timedelta, timezone


import jwt

from base.data_structures import (
    AccessTokenDTO,
    JWTPayloadDTO,
    JWTPayloadExtendedDTO,
    TokenPairDTO,
)
from base.exceptions import InvalidTokenException


class JWTHandler:
    """Обработчик JSON Web Token'ов."""

    def __init__(self, secret_key: str) -> None:
        """Инициализация обработчика."""
        self.__secret_key = secret_key

    def encode_token(
        self, payload: JWTPayloadDTO, expires_minutes: int
    ) -> AccessTokenDTO:
        """Создание токена доступа."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        extended_payload = JWTPayloadExtendedDTO(
            id=payload.id,
            token_type="access",
            exp=int(expire.timestamp()),
        )
        encoded_jwt = jwt.encode(
            extended_payload.model_dump(), self.__secret_key, algorithm="HS256"
        )
        return AccessTokenDTO(access_token=encoded_jwt, expire=expire)

    def decode_token(self, token: str) -> JWTPayloadDTO:
        """Декодирование токена доступа."""
        try:
            payload = jwt.decode(token, self.__secret_key, algorithms=["HS256"])
            payload_obj = JWTPayloadDTO(id=payload["id"])
            return payload_obj
        except Exception as exc:
            raise InvalidTokenException("Invalid token") from exc

    def create_new_access_token_by_refresh_token(
        self, payload_with_refresh_exp: JWTPayloadExtendedDTO, expires_minutes: int
    ) -> TokenPairDTO:
        """Создание нового токена доступа через refresh-токен."""
        if payload_with_refresh_exp.exp < datetime.now(timezone.utc):
            raise InvalidTokenException("Refresh token is expired")

        new_access_token = self.encode_token(
            JWTPayloadDTO(id=payload_with_refresh_exp.id), expires_minutes
        )
        return TokenPairDTO(
            access_token=new_access_token.access_token,
            refresh_token="",  # Здесь должен быть новый refresh токен
        )

    def create_refresh_token(
        self, payload: JWTPayloadDTO, expires_hours: int
    ) -> str:
        """Создание refresh токена."""
        expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
        extended_payload = JWTPayloadExtendedDTO(
            id=payload.id,
            token_type="refresh",
            exp=int(expire.timestamp()),
        )
        return jwt.encode(
            extended_payload.model_dump(), self.__secret_key, algorithm="HS256"
        )

    def decode_refresh_token(self, token: str) -> JWTPayloadExtendedDTO:
        """Декодирование refresh токена."""
        try:
            payload = jwt.decode(token, self.__secret_key, algorithms=["HS256"])
            return JWTPayloadExtendedDTO(
                id=payload["id"],
                iat=datetime.fromisoformat(payload["iat"].replace("Z", "+00:00")),
                exp=datetime.fromisoformat(payload["exp"].replace("Z", "+00:00")),
            )
        except Exception as exc:
            raise InvalidTokenException("Invalid refresh token") from exc

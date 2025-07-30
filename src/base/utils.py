"""Утилиты для работы с JWT токенами."""

from datetime import datetime, timedelta
from typing import Optional

import jwt

from base.config import get_settings
from base.data_structures import JWTPayloadDTO
from base.exceptions import AuthenticationError, InvalidTokenException

settings = get_settings()


class JWTHandler:
    """Класс для работы с JWT токенами."""

    def __init__(self, secret_key: str):
        """Инициализация обработчика JWT."""
        self.secret_key = secret_key

    def create_access_token(
        self, user_id: int, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Создание JWT токена."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expires_minutes
            )

        to_encode = {"id": user_id, "exp": expire, "type": "access"}
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
            return str(encoded_jwt)
        except Exception as e:
            raise AuthenticationError(f"Failed to create token: {str(e)}")

    def decode_token(self, token: str) -> JWTPayloadDTO:
        """Декодирование JWT токена."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return JWTPayloadDTO(**payload)
        except jwt.ExpiredSignatureError:
            raise InvalidTokenException("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenException(f"Invalid token: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Failed to decode token: {str(e)}")

    def create_refresh_token(self, user_id: int) -> str:
        """Создание refresh токена."""
        expires_delta = timedelta(hours=settings.refresh_token_expires_hours)
        expire = datetime.utcnow() + expires_delta

        to_encode = {"id": user_id, "exp": expire, "type": "refresh"}
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
            return str(encoded_jwt)
        except Exception as e:
            raise AuthenticationError(f"Failed to create refresh token: {str(e)}")

    def verify_refresh_token(self, token: str) -> int:
        """Проверка refresh токена."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            if payload.get("type") != "refresh":
                raise InvalidTokenException("Not a refresh token")
            user_id = payload.get("id")
            if user_id is None:
                raise InvalidTokenException("Token does not contain user ID")
            return int(user_id)
        except jwt.ExpiredSignatureError:
            raise InvalidTokenException("Refresh token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenException(f"Invalid refresh token: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Failed to verify refresh token: {str(e)}")

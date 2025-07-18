"""API эндпойнты для работы с пользователями."""

from fastapi import APIRouter, status
from fastapi.responses import Response

from base.config import get_settings
from base.dependencies import (
    UserServiceDependency,
)
from base.utils import JWTHandler
from base.data_structures import JWTPayloadDTO
from users.domain.models import UserCredentials

settings = get_settings()
router = APIRouter()


@router.post("/", status_code=status.HTTP_204_NO_CONTENT)
async def register_user(
    user: UserCredentials, service: UserServiceDependency
) -> Response:
    """Регистрация пользователя."""
    await service.add_user(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/auth/", status_code=status.HTTP_200_OK)
async def login_user(
    user: UserCredentials, service: UserServiceDependency
) -> dict[str, str]:
    """Авторизация пользователя."""
    verified_user = await service.verify_credentials(user.email, user.password)
    if not verified_user:
        return {"error": "Invalid credentials"}

    jwt_handler = JWTHandler(settings.secret_key)
    access_token = jwt_handler.encode_token(
        payload=JWTPayloadDTO(id=verified_user.id),
        expires_minutes=settings.access_token_expires_minutes,
    )

    return {"access_token": access_token.access_token}

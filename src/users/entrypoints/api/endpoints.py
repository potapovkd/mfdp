"""API эндпоинты для работы с пользователями."""

from fastapi import APIRouter, Response, Depends
from fastapi.security import HTTPBearer

from base.dependencies import get_token_from_header
from base.data_structures import JWTPayloadDTO
from users.domain.models import UserCredentials
from users.entrypoints.api.dependencies import UserServiceDependency

router = APIRouter()
security = HTTPBearer()


@router.post("/", status_code=204)
async def register_user(
    user: UserCredentials, service: UserServiceDependency
) -> Response:
    """Регистрация нового пользователя."""
    await service.add_user(user)
    return Response(status_code=204)


@router.post("/auth/", status_code=200)
async def authenticate_user(
    user: UserCredentials, service: UserServiceDependency
) -> dict:
    """Аутентификация пользователя."""
    token = await service.authenticate_user(user)
    return {"access_token": token, "token_type": "bearer"}

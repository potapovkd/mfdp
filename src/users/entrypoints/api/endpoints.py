"""API endpoints для работы с пользователями."""

from fastapi import APIRouter, HTTPException, status
from fastapi.security import HTTPBearer

from base.exceptions import AuthenticationError, DatabaseError
from users.domain.models import UserCreateDTO, UserLoginDTO, UserLoginResponse
from users.entrypoints.api.dependencies import UserServiceDependency

router = APIRouter()
security = HTTPBearer()


@router.post("/", status_code=204)
async def register_user(user: UserCreateDTO, service: UserServiceDependency) -> None:
    """Регистрация нового пользователя."""
    try:
        await service.add_user(user)
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/auth/", status_code=200)
async def authenticate_user(
    user: UserLoginDTO, service: UserServiceDependency
) -> UserLoginResponse:
    """Аутентификация пользователя."""
    try:
        token = await service.authenticate_user(user)
        return UserLoginResponse(access_token=token, token_type="bearer")
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

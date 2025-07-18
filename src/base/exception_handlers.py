"""Обработчики исключений для FastAPI."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .exceptions import (
    EntityNotFoundException,
    AlreadyExistsException,
    AuthException,
    InvalidCredentialsException,
)


async def handle_entity_not_found(
    request: Request, exc: EntityNotFoundException
) -> JSONResponse:
    """Обработчик для EntityNotFoundException."""
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail}
    )


async def handle_already_exists(
    request: Request, exc: AlreadyExistsException
) -> JSONResponse:
    """Обработчик для AlreadyExistsException."""
    return JSONResponse(
        status_code=400,
        content={"detail": exc.detail}
    )


async def handle_auth_exception(
    request: Request, exc: AuthException
) -> JSONResponse:
    """Обработчик для AuthException."""
    return JSONResponse(
        status_code=401,
        content={"detail": exc.detail}
    )


async def handle_invalid_credentials(
    request: Request, exc: InvalidCredentialsException
) -> JSONResponse:
    """Обработчик для InvalidCredentialsException."""
    return JSONResponse(
        status_code=400,
        content={"detail": exc.detail}
    )


def add_exception_handlers(app: FastAPI) -> None:
    """Добавление обработчиков исключений к приложению."""
    app.add_exception_handler(EntityNotFoundException, handle_entity_not_found)
    app.add_exception_handler(AlreadyExistsException, handle_already_exists)
    app.add_exception_handler(AuthException, handle_auth_exception)
    app.add_exception_handler(InvalidCredentialsException, handle_invalid_credentials)

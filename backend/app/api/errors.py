"""Traduce los errores de negocio y de validación a un formato de respuesta único."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.schemas import ErrorDetail, ErrorOut
from app.application.errors import NotFoundError
from app.domain.errors import InvalidActivityError

VALIDATION_ERROR_CODE = "VALIDATION_ERROR"
INVALID_ACTIVITY_CODE = "INVALID_ACTIVITY"

NOT_FOUND_RESPONSE = {"model": ErrorOut, "description": "El recurso no existe."}
VALIDATION_RESPONSE = {"model": ErrorOut, "description": "Los datos enviados no son válidos."}


def _error_response(
    status_code: int, code: str, message: str, details: list[dict[str, object]] | None = None
) -> JSONResponse:
    body = ErrorOut(error=ErrorDetail(code=code, message=message, details=details))
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


async def _handle_not_found(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, NotFoundError)
    return _error_response(status.HTTP_404_NOT_FOUND, error.code, str(error))


async def _handle_invalid_activity(_: Request, error: Exception) -> JSONResponse:
    return _error_response(status.HTTP_422_UNPROCESSABLE_CONTENT, INVALID_ACTIVITY_CODE, str(error))


async def _handle_validation(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, RequestValidationError)
    details = [
        {"field": ".".join(str(part) for part in item["loc"][1:]), "message": item["msg"]}
        for item in error.errors()
    ]
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        VALIDATION_ERROR_CODE,
        "Los datos enviados no son válidos.",
        details,
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, _handle_not_found)
    app.add_exception_handler(InvalidActivityError, _handle_invalid_activity)
    app.add_exception_handler(RequestValidationError, _handle_validation)

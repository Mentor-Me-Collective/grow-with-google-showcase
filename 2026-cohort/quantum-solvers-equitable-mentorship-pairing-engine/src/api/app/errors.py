from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class Problem(Exception):
    """An error in the shape the contract defines.

    FastAPI's default error body is {"detail": ...}, but the contract's Problem
    is {code, message} and the frontend reads `error.message` to decide what to
    show a person. Left as-is, every error in the interface would render as
    undefined — so this is not cosmetic.
    """

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        field: str | None = None,
    ) -> None:
        self.status = status
        self.code = code
        self.message = message
        self.field = field
        super().__init__(message)

    def body(self) -> dict[str, str]:
        payload = {"code": self.code, "message": self.message}
        if self.field:
            payload["field"] = self.field
        return payload


def not_found(what: str) -> Problem:
    return Problem(404, "not_found", f"No such {what}.")


def unauthorized() -> Problem:
    return Problem(401, "no_session", "Sign in to continue.")


def forbidden(message: str = "You do not have access to this.") -> Problem:
    return Problem(403, "forbidden", message)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Problem)
    async def _problem(_: Request, exc: Problem) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=exc.body())

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Anything raised as a plain HTTPException still leaves in the
        # contract's shape rather than FastAPI's.
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": _CODES.get(exc.status_code, "error"),
                "message": str(exc.detail),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # The first failing field, named in words a person can act on. A dump of
        # pydantic's error list is accurate and useless on screen.
        first = exc.errors()[0] if exc.errors() else None
        field = None
        if first and first.get("loc"):
            field = str(first["loc"][-1])
        return JSONResponse(
            status_code=400,
            content={
                "code": "invalid_body",
                "message": (
                    f"{field} is missing or not valid."
                    if field
                    else "That request was not valid."
                ),
                **({"field": field} if field else {}),
            },
        )


_CODES = {
    400: "bad_request",
    401: "no_session",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    410: "gone",
    429: "too_many_requests",
}

from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from .api.charges import ChargeStore
from .api.charges import router as charges_router
from .api.middleware import log_request
from .api.problems import problem
from .api.system import router as system_router
from .config import Settings, get_settings
from .logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="DomProzrachno", version=settings.app_version)
    app.state.settings = settings
    app.state.charges = ChargeStore()
    app.middleware("http")(log_request)
    app.include_router(system_router)
    app.include_router(charges_router)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError) -> JSONResponse:
        issues = []
        for issue in error.errors():
            location = issue["loc"]
            if issue["type"] == "extra_forbidden":
                location = location[:-1]
            pointer = "".join(f"/{part}" for part in location)
            issues.append({"pointer": pointer, "detail": issue["type"]})
        return problem(
            request,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "invalid_request",
            "Request data failed validation.",
            errors=issues,
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException) -> JSONResponse:
        status = HTTPStatus(error.status_code)
        return problem(request, status, status.name.lower(), status.phrase, headers=error.headers)

    return app

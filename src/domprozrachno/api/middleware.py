import re
from http import HTTPStatus
from time import perf_counter
from uuid import uuid4

import structlog
from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from .problems import problem

log = structlog.get_logger("domprozrachno")
REQUEST_ID = re.compile(r"[a-zA-Z0-9_-]{1,64}")
METHODS = {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT"}


async def log_request(request: Request, call_next: RequestResponseEndpoint) -> Response:
    supplied = request.headers.get("X-Request-Id", "")
    request_id = supplied if REQUEST_ID.fullmatch(supplied) else str(uuid4())
    request.state.request_id = request_id

    started = perf_counter()
    with structlog.contextvars.bound_contextvars(request_id=request_id):
        try:
            response = await call_next(request)
        except Exception:
            log.error("request_failed")
            response = problem(
                request, HTTPStatus.INTERNAL_SERVER_ERROR, "server_error", "Internal server error."
            )
        response.headers["X-Request-Id"] = request_id
        route = request.scope.get("route")
        log.info(
            "request_handled",
            method=request.method if request.method in METHODS else "OTHER",
            route=getattr(route, "path", None),
            status_code=response.status_code,
            duration_ms=round((perf_counter() - started) * 1000, 2),
        )
    return response

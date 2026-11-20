from collections.abc import Mapping, Sequence
from http import HTTPStatus

from fastapi import Request
from fastapi.responses import JSONResponse


def problem(
    request: Request,
    status: HTTPStatus,
    code: str,
    detail: str,
    *,
    errors: Sequence[Mapping[str, str]] = (),
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    request_id = request.state.request_id
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        headers=headers,
        content={
            "type": "urn:domprozrachno:problem:" + code.replace("_", "-"),
            "title": status.phrase,
            "status": status.value,
            "detail": detail,
            "instance": f"/v1/problems/{request_id}",
            "code": code.upper(),
            "correlation_id": request_id,
            **({"errors": errors} if errors else {}),
        },
    )

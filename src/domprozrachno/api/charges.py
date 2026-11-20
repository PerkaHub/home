import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from http import HTTPStatus
from threading import Lock
from typing import cast
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from .charge_schemas import ChargeDraftInput, ChargeLineResponse, ChargeResponse
from .problems import problem

router = APIRouter(tags=["charges"])
log = structlog.get_logger("domprozrachno")
DEMO_ACCOUNT = UUID("00000000-0000-4000-8000-000000000001")


@dataclass
class ChargeStore:
    charges: dict[UUID, ChargeResponse] = field(default_factory=dict)
    lock: Lock = field(default_factory=Lock)


@router.post("/v1/accounts/{account_id}/charges", status_code=201, response_model=ChargeResponse)
def create_draft(
    account_id: UUID, payload: ChargeDraftInput, request: Request, response: Response
) -> ChargeResponse | JSONResponse:
    if request.app.state.settings.app_env == "production" or account_id != DEMO_ACCOUNT:
        return problem(request, HTTPStatus.NOT_FOUND, "not_found", "Resource was not found.")
    if not re.fullmatch(r"(?!0000)[0-9]{4}-(0[1-9]|1[0-2])", payload.period):
        return problem(
            request, HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_charge", "Invalid period."
        )
    if not 1 <= payload.amount_minor <= 100_000_000:
        return problem(
            request, HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_charge", "Amount is out of range."
        )
    if any(line.amount_minor <= 0 for line in payload.lines):
        return problem(
            request,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "invalid_charge",
            "Line amount must be positive.",
        )
    if payload.amount_minor != sum(line.amount_minor for line in payload.lines):
        return problem(
            request,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "invalid_charge",
            "Line amounts do not add up.",
        )

    draft = ChargeResponse(
        id=uuid4(),
        account_id=account_id,
        period=payload.period,
        amount_minor=payload.amount_minor,
        status="draft",
        lines=[ChargeLineResponse(id=uuid4(), **line.model_dump()) for line in payload.lines],
        created_at=datetime.now(UTC),
    )
    store = cast(ChargeStore, request.app.state.charges)
    with store.lock:
        store.charges[draft.id] = draft
    response.headers["Location"] = f"/v1/charges/{draft.id}"
    return draft


@router.post("/v1/charges/{charge_id}/publications", status_code=201, response_model=ChargeResponse)
def publish(charge_id: UUID, request: Request, response: Response) -> ChargeResponse | JSONResponse:
    store = cast(ChargeStore, request.app.state.charges)
    with store.lock:
        draft = store.charges.get(charge_id)
        if draft is None:
            return problem(request, HTTPStatus.NOT_FOUND, "not_found", "Resource was not found.")
        if draft.status == "published":
            return problem(
                request, HTTPStatus.CONFLICT, "already_published", "Charge is already published."
            )
        for other in store.charges.values():
            if other.account_id == draft.account_id and other.period == draft.period:
                if other.status == "published":
                    return problem(
                        request,
                        HTTPStatus.CONFLICT,
                        "period_already_published",
                        "A charge is already published for this account and period.",
                    )

        draft.status = "published"
        draft.published_at = datetime.now(UTC)
        store.charges[charge_id] = draft
    log.info("charge_published")
    response.headers["Location"] = f"/v1/charges/{draft.id}"
    return draft


@router.get("/v1/charges/{charge_id}", response_model=ChargeResponse)
def read_charge(charge_id: UUID, request: Request) -> ChargeResponse | JSONResponse:
    store = cast(ChargeStore, request.app.state.charges)
    with store.lock:
        charge = store.charges.get(charge_id)
        if charge is None or charge.status != "published":
            return problem(request, HTTPStatus.NOT_FOUND, "not_found", "Resource was not found.")
        return charge

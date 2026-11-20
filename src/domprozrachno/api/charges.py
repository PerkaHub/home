from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from ..modules.billing.application.charges import DraftLine
from ..modules.billing.domain.errors import (
    AlreadyPublished,
    ChargeNotFound,
    InvalidCharge,
    PeriodAlreadyPublished,
)
from ..modules.billing.domain.models import Charge
from .charge_schemas import ChargeDraftInput, ChargeLineResponse, ChargeResponse
from .dependencies import ChargeUseCase
from .problems import problem

router = APIRouter(tags=["charges"])

ERROR_RESPONSES: dict[type[Exception], tuple[HTTPStatus, str]] = {
    ChargeNotFound: (HTTPStatus.NOT_FOUND, "not_found"),
    InvalidCharge: (HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_charge"),
    AlreadyPublished: (HTTPStatus.CONFLICT, "already_published"),
    PeriodAlreadyPublished: (HTTPStatus.CONFLICT, "period_already_published"),
}


async def charge_problem(request: Request, error: Exception) -> JSONResponse:
    status, code = ERROR_RESPONSES[type(error)]
    return problem(request, status, code, str(error))


def charge_response(charge: Charge) -> ChargeResponse:
    return ChargeResponse(
        id=charge.id,
        account_id=charge.account_id,
        period=charge.period.value,
        amount_minor=charge.amount.amount_minor,
        currency=charge.amount.currency,
        status=charge.status,
        created_at=charge.created_at,
        published_at=charge.published_at,
        lines=[
            ChargeLineResponse(
                id=line.id,
                service=line.service,
                basis=line.basis,
                amount_minor=line.amount.amount_minor,
            )
            for line in charge.lines
        ],
    )


@router.post("/v1/accounts/{account_id}/charges", status_code=201, response_model=ChargeResponse)
def create_draft(
    account_id: UUID, payload: ChargeDraftInput, response: Response, service: ChargeUseCase
) -> ChargeResponse:
    lines = (DraftLine(line.service, line.basis, line.amount_minor) for line in payload.lines)
    charge = service.create_draft(account_id, payload.period, payload.amount_minor, lines)
    response.headers["Location"] = f"/v1/charges/{charge.id}"
    return charge_response(charge)


@router.post("/v1/charges/{charge_id}/publications", status_code=201, response_model=ChargeResponse)
def publish(charge_id: UUID, response: Response, service: ChargeUseCase) -> ChargeResponse:
    charge = service.publish(charge_id)
    response.headers["Location"] = f"/v1/charges/{charge.id}"
    return charge_response(charge)


@router.get("/v1/charges/{charge_id}", response_model=ChargeResponse)
def read_charge(charge_id: UUID, service: ChargeUseCase) -> ChargeResponse:
    return charge_response(service.read(charge_id))

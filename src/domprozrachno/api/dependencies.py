from datetime import UTC, datetime
from typing import Annotated, cast
from uuid import UUID, uuid4

from fastapi import Depends, Request

from ..config import Settings
from ..modules.billing.application.charges import ChargeService
from ..modules.billing.infrastructure.adapters import InMemoryChargeRepository, log_publication

DEMO_ACCOUNT = UUID("00000000-0000-4000-8000-000000000001")


def utc_now() -> datetime:
    return datetime.now(UTC)


def allow_demo_account(account_id: UUID) -> bool:
    return account_id == DEMO_ACCOUNT


def deny_all_accounts(account_id: UUID) -> bool:
    return False


def build_charge_service(settings: Settings) -> ChargeService:
    return ChargeService(
        repository=InMemoryChargeRepository(),
        clock=utc_now,
        new_id=uuid4,
        allows_account=deny_all_accounts
        if settings.app_env == "production"
        else allow_demo_account,
        publish_event=log_publication,
    )


def charge_service(request: Request) -> ChargeService:
    return cast(ChargeService, request.app.state.charge_service)


ChargeUseCase = Annotated[ChargeService, Depends(charge_service)]

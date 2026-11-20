from threading import Lock
from uuid import UUID

import structlog

from ..domain.errors import AlreadyPublished, PeriodAlreadyPublished
from ..domain.models import BillingPeriod, Charge, ChargePublished

log = structlog.get_logger("domprozrachno")


class InMemoryChargeRepository:
    def __init__(self) -> None:
        self._charges: dict[UUID, Charge] = {}
        self._published: set[tuple[UUID, BillingPeriod]] = set()
        self._lock = Lock()

    def add(self, charge: Charge) -> None:
        with self._lock:
            if charge.id in self._charges:
                raise ValueError("Charge id already exists.")
            self._charges[charge.id] = charge

    def find(self, charge_id: UUID) -> Charge | None:
        with self._lock:
            return self._charges.get(charge_id)

    def publish(self, charge: Charge) -> None:
        with self._lock:
            if self._charges[charge.id].published_at is not None:
                raise AlreadyPublished("Charge is already published.")
            key = (charge.account_id, charge.period)
            if key in self._published:
                raise PeriodAlreadyPublished(
                    "A charge is already published for this account and period."
                )
            self._charges[charge.id] = charge
            self._published.add(key)


def log_publication(event: ChargePublished) -> None:
    # The journal correlates the operation by request id, without copying the billing data.
    log.info("charge_published")

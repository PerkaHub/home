from collections.abc import Callable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from ..domain.models import Charge, ChargePublished

type Clock = Callable[[], datetime]
type NewId = Callable[[], UUID]
type AccountPolicy = Callable[[UUID], bool]
type PublishEvent = Callable[[ChargePublished], None]


class ChargeRepository(Protocol):
    def add(self, charge: Charge) -> None: ...

    def find(self, charge_id: UUID) -> Charge | None: ...

    def publish(self, charge: Charge) -> None:
        """Store the published charge atomically, enforcing the unique account/period."""

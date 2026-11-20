from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from ..domain.errors import ChargeNotFound
from ..domain.models import BillingPeriod, Charge, ChargeLine, ChargePublished, Money
from .ports import AccountPolicy, ChargeRepository, Clock, NewId, PublishEvent


@dataclass(frozen=True)
class DraftLine:
    service: str
    basis: str
    amount_minor: int


@dataclass
class ChargeService:
    repository: ChargeRepository
    clock: Clock
    new_id: NewId
    allows_account: AccountPolicy
    publish_event: PublishEvent

    def create_draft(
        self, account_id: UUID, month: str, amount_minor: int, lines: Iterable[DraftLine]
    ) -> Charge:
        if not self.allows_account(account_id):
            raise ChargeNotFound("Resource was not found.")
        charge = Charge(
            id=self.new_id(),
            account_id=account_id,
            period=BillingPeriod(month),
            amount=Money(amount_minor),
            lines=tuple(
                ChargeLine(self.new_id(), line.service, line.basis, Money(line.amount_minor))
                for line in lines
            ),
            created_at=self.clock(),
        )
        self.repository.add(charge)
        return charge

    def publish(self, charge_id: UUID) -> Charge:
        charge = self._find(charge_id).publish(self.clock())
        self.repository.publish(charge)
        self.publish_event(
            ChargePublished(charge.id, charge.account_id, charge.period, charge.amount)
        )
        return charge

    def read(self, charge_id: UUID) -> Charge:
        charge = self._find(charge_id)
        if charge.published_at is None:
            raise ChargeNotFound("Resource was not found.")
        return charge

    def _find(self, charge_id: UUID) -> Charge:
        charge = self.repository.find(charge_id)
        if charge is None or not self.allows_account(charge.account_id):
            raise ChargeNotFound("Resource was not found.")
        return charge

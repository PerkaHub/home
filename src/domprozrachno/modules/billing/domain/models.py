from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime
from typing import ClassVar, Literal
from uuid import UUID

from .errors import AlreadyPublished, InvalidCharge

MIN_CHARGE_MINOR = 1
MAX_CHARGE_MINOR = 100_000_000
PERIOD_PATTERN = re.compile(r"(?!0000)[0-9]{4}-(0[1-9]|1[0-2])")


@dataclass(frozen=True)
class BillingPeriod:
    value: str

    def __post_init__(self) -> None:
        if not PERIOD_PATTERN.fullmatch(self.value):
            raise InvalidCharge("Invalid period.")


@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: ClassVar[Literal["RUB"]] = "RUB"

    def __post_init__(self) -> None:
        if type(self.amount_minor) is not int:
            raise InvalidCharge("Amount must be whole kopecks.")


@dataclass(frozen=True)
class ChargeLine:
    id: UUID
    service: str
    basis: str
    amount: Money


@dataclass(frozen=True)
class Charge:
    id: UUID
    account_id: UUID
    period: BillingPeriod
    amount: Money
    lines: tuple[ChargeLine, ...]
    created_at: datetime
    published_at: datetime | None = None

    def __post_init__(self) -> None:
        if not MIN_CHARGE_MINOR <= self.amount.amount_minor <= MAX_CHARGE_MINOR:
            raise InvalidCharge("Amount is out of range.")
        if not self.lines or any(line.amount.amount_minor <= 0 for line in self.lines):
            raise InvalidCharge("Line amount must be positive.")
        if self.amount.amount_minor != sum(line.amount.amount_minor for line in self.lines):
            raise InvalidCharge("Line amounts do not add up.")

    @property
    def status(self) -> Literal["draft", "published"]:
        return "draft" if self.published_at is None else "published"

    def publish(self, now: datetime) -> Charge:
        if self.published_at is not None:
            raise AlreadyPublished("Charge is already published.")
        return replace(self, published_at=now)


@dataclass(frozen=True)
class ChargePublished:
    charge_id: UUID
    account_id: UUID
    period: BillingPeriod
    amount: Money

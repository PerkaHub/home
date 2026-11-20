from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from domprozrachno.modules.billing.domain.models import ChargePublished


@dataclass
class FixedClock:
    now: datetime

    def __call__(self) -> datetime:
        return self.now


@dataclass
class SequenceIds:
    ids: Iterator[UUID]

    def __call__(self) -> UUID:
        return next(self.ids)


@dataclass
class PublicationSpy:
    events: list[ChargePublished] = field(default_factory=list)

    def __call__(self, event: ChargePublished) -> None:
        self.events.append(event)

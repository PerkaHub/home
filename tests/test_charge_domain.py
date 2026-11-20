from datetime import UTC, datetime
from uuid import UUID

import pytest

from domprozrachno.modules.billing.domain.errors import AlreadyPublished, InvalidCharge
from domprozrachno.modules.billing.domain.models import BillingPeriod, Charge, ChargeLine, Money

NOW = datetime(2026, 11, 20, tzinfo=UTC)
LINES = (ChargeLine(UUID(int=1), "Water", "Meter", Money(1)),)


def test_domain_does_not_depend_on_http_to_reject_mismatched_total() -> None:
    with pytest.raises(InvalidCharge, match="do not add up"):
        Charge(UUID(int=2), UUID(int=3), BillingPeriod("2026-11"), Money(2), LINES, NOW)


def test_domain_rejects_a_second_publication() -> None:
    draft = Charge(UUID(int=2), UUID(int=3), BillingPeriod("2026-11"), Money(1), LINES, NOW)
    published = draft.publish(NOW)

    with pytest.raises(AlreadyPublished):
        published.publish(NOW)

    assert draft.published_at is None
    assert published.published_at == NOW

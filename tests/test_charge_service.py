from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from doubles import FixedClock, PublicationSpy, SequenceIds

from domprozrachno.modules.billing.application.charges import ChargeService, DraftLine
from domprozrachno.modules.billing.domain.errors import ChargeNotFound, PeriodAlreadyPublished
from domprozrachno.modules.billing.domain.models import BillingPeriod, ChargePublished, Money
from domprozrachno.modules.billing.infrastructure.adapters import InMemoryChargeRepository

ACCOUNT = UUID(int=1)
OTHER_ACCOUNT = UUID(int=2)
START = datetime(2026, 11, 1, 12, tzinfo=UTC)
LINES = (DraftLine("Water", "Meter", 3000),)


@pytest.fixture
def scenario() -> tuple[ChargeService, FixedClock, PublicationSpy]:
    clock = FixedClock(START)
    ids = SequenceIds(iter(UUID(int=n) for n in range(100, 110)))
    spy = PublicationSpy()
    service = ChargeService(InMemoryChargeRepository(), clock, ids, lambda _: True, spy)
    return service, clock, spy


def test_publication_uses_injected_time_and_emits_the_saved_charge(
    scenario: tuple[ChargeService, FixedClock, PublicationSpy],
) -> None:
    service, clock, spy = scenario
    draft = service.create_draft(ACCOUNT, "2026-11", 3000, LINES)
    clock.now = START + timedelta(hours=1)

    published = service.publish(draft.id)

    assert draft.status == "draft"
    assert draft.id == UUID(int=100)
    assert published.lines[0].id == UUID(int=101)
    assert published.created_at == START
    assert published.published_at == START + timedelta(hours=1)
    assert service.read(draft.id) == published
    assert spy.events == [ChargePublished(draft.id, ACCOUNT, BillingPeriod("2026-11"), Money(3000))]
    with pytest.raises(FrozenInstanceError):
        published.lines[0].amount = Money(1000)  # type: ignore[misc]


def test_conflict_does_not_emit_a_second_publication(
    scenario: tuple[ChargeService, FixedClock, PublicationSpy],
) -> None:
    service, _, spy = scenario
    original = service.create_draft(ACCOUNT, "2026-11", 3000, LINES)
    duplicate = service.create_draft(ACCOUNT, "2026-11", 3000, LINES)
    service.publish(original.id)

    with pytest.raises(PeriodAlreadyPublished):
        service.publish(duplicate.id)

    assert [event.charge_id for event in spy.events] == [original.id]
    with pytest.raises(ChargeNotFound):
        service.read(duplicate.id)


def test_account_policy_can_be_replaced_for_existing_charges(
    scenario: tuple[ChargeService, FixedClock, PublicationSpy],
) -> None:
    service, _, spy = scenario
    first = service.create_draft(ACCOUNT, "2026-11", 3000, LINES)
    second = service.create_draft(OTHER_ACCOUNT, "2026-11", 3000, LINES)
    service.publish(first.id)
    service.allows_account = lambda account_id: account_id == OTHER_ACCOUNT

    published = service.publish(second.id)

    assert published.account_id == OTHER_ACCOUNT
    assert [event.account_id for event in spy.events] == [ACCOUNT, OTHER_ACCOUNT]
    with pytest.raises(ChargeNotFound):
        service.read(first.id)

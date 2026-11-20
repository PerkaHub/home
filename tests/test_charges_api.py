from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from domprozrachno.app import create_app
from domprozrachno.config import Settings

ACCOUNT = "00000000-0000-4000-8000-000000000001"
OTHER_ACCOUNT = "00000000-0000-4000-8000-000000000002"
DRAFTS = f"/v1/accounts/{ACCOUNT}/charges"
PERIOD = "2026-11"


def create_draft(client: TestClient, *, period: str = PERIOD, amount_minor: int = 1) -> str:
    response = client.post(
        DRAFTS,
        json={
            "period": period,
            "amount_minor": amount_minor,
            "lines": [{"service": "Heating", "basis": "Meter", "amount_minor": amount_minor}],
        },
    )
    assert response.status_code == 201, response.text
    return response.headers["Location"]


def test_published_charge_can_be_read_with_original_lines_and_total(client: TestClient) -> None:
    lines = [
        {"service": "Heat", "basis": "Meter", "amount_minor": 10_000},
        {"service": "Water", "basis": "Meter", "amount_minor": 20_000},
    ]
    draft = client.post(DRAFTS, json={"period": PERIOD, "amount_minor": 30_000, "lines": lines})
    assert draft.status_code == 201, draft.text
    location = draft.headers["Location"]

    before_publication = client.get(location)
    published = client.post(f"{location}/publications")
    read = client.get(location)

    assert before_publication.status_code == 404
    assert draft.json()["status"] == "draft"
    assert draft.json()["published_at"] is None
    assert published.status_code == 201
    assert published.headers["Location"] == location
    assert read.status_code == 200
    result = published.json()
    assert read.json() == result
    assert result["account_id"] == ACCOUNT
    assert location == f"/v1/charges/{UUID(result['id'])}"
    assert result["period"] == PERIOD
    assert result["amount_minor"] == 30_000
    assert result["currency"] == "RUB"
    assert result["status"] == "published"
    assert result["lines"] == draft.json()["lines"]
    assert len({UUID(line["id"]) for line in result["lines"]}) == 2
    assert datetime.fromisoformat(result["published_at"]) >= datetime.fromisoformat(
        result["created_at"]
    )


def test_only_one_charge_can_be_published_per_account_and_month(client: TestClient) -> None:
    first = create_draft(client)
    duplicate = create_draft(client)
    next_month = create_draft(client, period="2026-12")
    assert client.post(f"{first}/publications").status_code == 201

    conflict = client.post(f"{duplicate}/publications", headers={"X-Request-Id": "conflict-42"})
    retry = client.post(f"{first}/publications")
    edit = client.patch(first, json={"amount_minor": 9})

    assert conflict.status_code == 409
    assert conflict.headers["content-type"] == "application/problem+json"
    assert conflict.json()["code"] == "PERIOD_ALREADY_PUBLISHED"
    assert conflict.json()["correlation_id"] == "conflict-42"
    assert retry.status_code == 409
    assert retry.json()["code"] == "ALREADY_PUBLISHED"
    assert edit.status_code == 405
    assert client.get(first).json()["amount_minor"] == 1
    assert client.get(duplicate).status_code == 404
    assert client.post(f"{next_month}/publications").status_code == 201


@pytest.mark.parametrize("amount_minor", [1, 100_000_000], ids=["minimum", "maximum"])
def test_boundary_amount_can_be_published(client: TestClient, amount_minor: int) -> None:
    location = create_draft(client, amount_minor=amount_minor)

    published = client.post(f"{location}/publications")

    assert published.status_code == 201
    assert published.json()["amount_minor"] == amount_minor


@pytest.mark.parametrize(
    ("period", "total", "line"),
    [
        ("2026-13", 1, 1),
        ("0000-11", 1, 1),
        (PERIOD, 0, 1),
        (PERIOD, 100_000_001, 100_000_001),
        (PERIOD, 1, 0),
        (PERIOD, 2, 1),
        (PERIOD, 1, True),
    ],
    ids=["month", "year-zero", "zero", "too-large", "zero-line", "wrong-total", "bool-line"],
)
def test_invalid_draft_is_rejected(
    client: TestClient, period: str, total: int, line: int | bool
) -> None:
    response = client.post(
        DRAFTS,
        json={
            "period": period,
            "amount_minor": total,
            "lines": [{"service": "Heat", "basis": "Meter", "amount_minor": line}],
        },
    )

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["status"] == 422
    assert "Location" not in response.headers
    assert client.post(f"{create_draft(client)}/publications").status_code == 201


def test_unknown_charge_and_other_account_are_hidden(client: TestClient) -> None:
    response = client.post(f"/v1/charges/{OTHER_ACCOUNT}/publications")
    draft = client.post(
        f"/v1/accounts/{OTHER_ACCOUNT}/charges",
        json={
            "period": PERIOD,
            "amount_minor": 1,
            "lines": [{"service": "Heat", "basis": "Meter", "amount_minor": 1}],
        },
    )

    assert response.status_code == draft.status_code == 404
    assert response.json()["code"] == draft.json()["code"] == "NOT_FOUND"


def test_production_rejects_demo_drafts(settings: Settings) -> None:
    client = TestClient(create_app(settings.model_copy(update={"app_env": "production"})))

    draft = client.post(
        DRAFTS,
        json={
            "period": PERIOD,
            "amount_minor": 1,
            "lines": [{"service": "Heat", "basis": "Meter", "amount_minor": 1}],
        },
    )

    assert draft.status_code == 404


def test_concurrent_publications_have_one_winner(client: TestClient) -> None:
    drafts = [create_draft(client), create_draft(client)]

    def publish(location: str) -> int:
        return client.post(f"{location}/publications").status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        status_codes = list(pool.map(publish, drafts))

    assert sorted(status_codes) == [201, 409]

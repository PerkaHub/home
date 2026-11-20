import json
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from domprozrachno.logging import configure_logging


def test_health_reports_liveness_with_unreachable_database(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_uses_application_settings(client: TestClient) -> None:
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "0.8.0-test", "environment": "test"}


def test_request_log_reuses_id_and_omits_private_input(
    client: TestClient, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_logging("info")

    response = client.get(
        "/health?token=private-query",
        headers={"X-Request-Id": "external-42", "Authorization": "Bearer private-header"},
    )

    output = capsys.readouterr().out
    event = json.loads(output)
    assert response.headers["X-Request-Id"] == event["request_id"] == "external-42"
    assert event["timestamp"].endswith("Z")
    assert event["level"] == "info"
    assert event["event"] == "request_handled"
    assert event["route"] == "/health"
    assert event["status_code"] == 200
    assert event["duration_ms"] >= 0
    assert "private-" not in output


def test_request_id_is_generated_when_missing_or_malformed(client: TestClient) -> None:
    first = client.get("/health")
    second = client.get("/health", headers={"X-Request-Id": "alice@example.org"})

    assert UUID(first.headers["X-Request-Id"]).version == 4
    assert UUID(second.headers["X-Request-Id"]).version == 4
    assert first.headers["X-Request-Id"] != second.headers["X-Request-Id"]

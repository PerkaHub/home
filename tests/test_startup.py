import json
from pathlib import Path

import pytest

from domprozrachno.__main__ import main
from domprozrachno.config import Settings


@pytest.mark.parametrize(
    ("dsn", "reason"),
    [(None, "missing"), ("https://private-password@example.test", "url_scheme")],
    ids=["missing-dsn", "invalid-dsn"],
)
def test_startup_exits_and_logs_configuration_error_without_input(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    dsn: str | None,
    reason: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    for field in Settings.model_fields:
        monkeypatch.delenv(field, raising=False)
        monkeypatch.delenv(field.upper(), raising=False)
    if dsn is not None:
        monkeypatch.setenv("DATABASE_URL", dsn)

    exit_code = main()

    output = capsys.readouterr().out
    event = json.loads(output)
    assert exit_code == 2
    assert event["event"] == "configuration_invalid"
    assert event["issues"] == [{"field": "DATABASE_URL", "reason": reason}]
    assert "private-password" not in output

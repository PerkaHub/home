from pathlib import Path

import pytest
from pydantic import ValidationError

from domprozrachno.config import Settings, get_settings

DSN = "postgresql://test:secret@localhost:1/test"


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for name in Settings.model_fields:
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.upper(), raising=False)


@pytest.mark.parametrize("port", [1, 8080, 65535], ids=["first", "usual", "last"])
def test_valid_port_is_loaded_as_integer(monkeypatch: pytest.MonkeyPatch, port: int) -> None:
    monkeypatch.setenv("DATABASE_URL", DSN)
    monkeypatch.setenv("PORT", str(port))

    settings = get_settings()

    assert settings.port == port


@pytest.mark.parametrize(
    ("key", "value", "reason"),
    [
        ("PORT", "abc", "int_parsing"),
        ("PORT", "0", "greater_than_equal"),
        ("PORT", "70000", "less_than_equal"),
        ("DATABASE_URL", "https://host", "url_scheme"),
        ("LOG_LEVEL", "loud", "literal_error"),
        ("APP_ENV", "staging", "literal_error"),
        ("HOST", "local network", "ip_any_address"),
    ],
    ids=["text-port", "zero-port", "large-port", "scheme", "log-level", "environment", "host"],
)
def test_invalid_environment_values_fail(
    monkeypatch: pytest.MonkeyPatch, key: str, value: str, reason: str
) -> None:
    monkeypatch.setenv("DATABASE_URL", DSN)
    monkeypatch.setenv(key, value)

    with pytest.raises(ValidationError) as rejected:
        get_settings()

    assert [(issue["loc"], issue["type"]) for issue in rejected.value.errors()] == [
        ((key.lower(),), reason)
    ]


def test_database_url_is_required() -> None:
    with pytest.raises(ValidationError) as rejected:
        get_settings()

    assert rejected.value.errors()[0]["loc"] == ("database_url",)


def test_unknown_dotenv_key_is_rejected(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(f"DATABASE_URL={DSN}\nLOG_LEVLE=warning\n", encoding="utf-8")

    with pytest.raises(ValidationError) as rejected:
        get_settings()

    assert rejected.value.errors()[0]["type"] == "extra_forbidden"


def test_environment_overrides_dotenv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(f"DATABASE_URL={DSN}\nPORT=8000\n", encoding="utf-8")
    monkeypatch.setenv("PORT", "9000")

    settings = get_settings()

    assert settings.port == 9000

import json
import logging

import pytest

from domprozrachno.logging import configure_logging


def test_server_errors_are_json_without_raw_exception_details(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("info")

    try:
        raise OSError("private-traceback")
    except OSError:
        logging.getLogger("uvicorn.error").exception("Server message: %s", "private-input")

    captured = capsys.readouterr()
    event = json.loads(captured.out)
    assert event["event"] == "server_message"
    assert event["level"] == "error"
    assert event["timestamp"].endswith("Z")
    assert "private-" not in captured.out
    assert captured.err == ""

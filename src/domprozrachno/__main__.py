import sys

import structlog
import uvicorn
from pydantic import ValidationError

from .app import create_app
from .config import Settings, get_settings
from .logging import configure_logging


def main() -> int:
    try:
        settings = get_settings()
    except ValidationError as error:
        configure_logging("error")
        issues = [
            {
                "field": str(item["loc"][0]).upper()
                if item["loc"] and item["loc"][0] in Settings.model_fields
                else "unknown",
                "reason": item["type"],
            }
            for item in error.errors(include_input=False, include_url=False)
        ]
        structlog.get_logger("domprozrachno").error("configuration_invalid", issues=issues)
        return 2

    app = create_app(settings)
    structlog.get_logger("domprozrachno").info(
        "service_starting", port=settings.port, version=settings.app_version
    )
    uvicorn.run(app, host="0.0.0.0", port=settings.port, access_log=False, log_config=None)
    return 0


if __name__ == "__main__":
    sys.exit(main())

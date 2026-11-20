import logging
import sys
from typing import Any

import structlog


def configure_logging(level: str) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    def server_event(
        logger: Any, method: str, fields: structlog.typing.EventDict
    ) -> structlog.typing.EventDict:
        # Framework diagnostics can include raw exception text or request input.
        return {"event": "server_message", "level": method}

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=[server_event, timestamper],
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
        pass_foreign_args=False,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    for name in ("domprozrachno", "uvicorn"):
        logger = logging.getLogger(name)
        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(level.upper())

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            timestamper,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )

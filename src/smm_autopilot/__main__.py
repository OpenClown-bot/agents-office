from __future__ import annotations

import asyncio
import logging
import signal

import structlog

from smm_autopilot.config import load_config
from smm_autopilot.db import Database


async def main() -> None:
    config = load_config()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, config.log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    db = Database(config)
    await db.connect()
    await db.init_schema()
    logger = structlog.get_logger()
    logger.info("smm_autopilot_started", version="0.1.0")

    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, _signal_handler)
    loop.add_signal_handler(signal.SIGTERM, _signal_handler)

    await stop_event.wait()
    logger.info("smm_autopilot_stopping")
    await db.close()


if __name__ == "__main__":
    asyncio.run(main())

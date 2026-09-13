"""Structured logging configuration.

Handlers/log calls in this codebase must never receive raw image bytes or
embedding vectors — only outcomes, identifiers, scores, and error codes
(blueprint section 12 / PRD section 18).
"""
from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt='{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":%(message)r}',
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

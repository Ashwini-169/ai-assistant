"""Centralized structured metrics logging."""
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def log_metrics(metrics: Dict[str, Any]) -> None:
    try:
        logger.info(json.dumps({"metrics": metrics}))
    except Exception:  # pragma: no cover - defensive
        pass

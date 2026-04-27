"""Write execution log as JSON after each pipeline run."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MODULE = "orchestration"
_REQUIRED_KEYS = (
    "timestamp",
    "files_processed",
    "rows_total",
    "rows_per_stage",
    "errors",
    "warnings",
    "duration_seconds",
)


def write_execution_log(log_data: dict[str, Any], output_path: Path) -> Path:
    """Validate log_data, write timestamped JSON inside output_path; return the file path."""
    output_path = Path(output_path)
    _check_log_data(log_data)
    _check_output_path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / _log_filename()
    _write_json(log_data, file_path)
    logger.info("[%s] Execution log written — %s", _MODULE, file_path.name)
    return file_path


# ── private helpers ───────────────────────────────────────────────────────────

def _check_log_data(log_data: Any) -> None:
    if not isinstance(log_data, dict):
        logger.error(
            "[%s] log_data must be a dict, got %s", _MODULE, type(log_data).__name__
        )
        raise TypeError(
            f"[{_MODULE}] log_data must be a dict, got {type(log_data).__name__}"
        )
    missing = [key for key in _REQUIRED_KEYS if key not in log_data]
    if missing:
        logger.error("[%s] Missing required log keys: %s", _MODULE, missing)
        raise KeyError(f"[{_MODULE}] Missing required log keys: {missing}")


def _check_output_path(output_path: Path) -> None:
    if output_path.exists() and output_path.is_file():
        logger.error(
            "[%s] output_path must be a directory, got a file: %s", _MODULE, output_path
        )
        raise ValueError(
            f"[{_MODULE}] output_path must be a directory, got a file: {output_path}"
        )


def _log_filename() -> str:
    return f"execution_log_{datetime.now().strftime('%Y%m%d_%H%M')}.json"


def _write_json(log_data: dict[str, Any], file_path: Path) -> None:
    with open(file_path, "w", encoding="utf-8") as fh:
        json.dump(log_data, fh, ensure_ascii=False, indent=2)

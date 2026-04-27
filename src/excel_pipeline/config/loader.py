"""Load and validate JSON pipeline configuration."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MODULE = "config"
_REQUIRED_KEYS = ("column_order", "required_columns", "mapping")


def load_config(config_path: Path) -> dict[str, Any]:
    """Load and structurally validate the pipeline JSON config; return the config dict."""
    config_path = Path(config_path)
    _check_path(config_path)
    raw = _read_json(config_path)
    _check_dict(raw, config_path)
    _check_required_keys(raw, config_path)
    logger.info("[%s] Config loaded — %s", _MODULE, config_path.name)
    return raw


# ── private helpers ───────────────────────────────────────────────────────────

def _check_path(config_path: Path) -> None:
    if not config_path.exists():
        logger.error("[%s] Config file not found: %s", _MODULE, config_path)
        raise FileNotFoundError(f"[{_MODULE}] Config file not found: {config_path}")
    if not config_path.is_file():
        logger.error("[%s] Config path is not a file: %s", _MODULE, config_path)
        raise ValueError(f"[{_MODULE}] Config path is not a file: {config_path}")


def _read_json(config_path: Path) -> Any:
    try:
        with open(config_path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        logger.error("[%s] Malformed JSON in %s: %s", _MODULE, config_path.name, exc)
        raise ValueError(
            f"[{_MODULE}] Malformed JSON in {config_path.name}: {exc}"
        ) from exc


def _check_dict(raw: Any, config_path: Path) -> None:
    if not isinstance(raw, dict):
        logger.error(
            "[%s] Config must be a JSON object, got %s: %s",
            _MODULE, type(raw).__name__, config_path.name,
        )
        raise TypeError(
            f"[{_MODULE}] Config must be a JSON object, got {type(raw).__name__}: {config_path.name}"
        )


def _check_required_keys(config: dict, config_path: Path) -> None:
    missing = [key for key in _REQUIRED_KEYS if key not in config]
    if missing:
        logger.error(
            "[%s] Missing required keys %s in %s", _MODULE, missing, config_path.name
        )
        raise KeyError(
            f"[{_MODULE}] Missing required keys {missing} in {config_path.name}"
        )

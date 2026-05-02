"""AWS Lambda entry point for the Excel pipeline."""

from __future__ import annotations

import logging
import shutil
import traceback
from pathlib import Path

from ..orchestration.pipeline import run_pipeline
from .s3_io import download_s3_file, download_s3_prefix, upload_directory

logger = logging.getLogger(__name__)

_MODULE = "cloud.lambda_handler"

_TMP_INPUTS = Path("/tmp/inputs")
_TMP_OUTPUTS = Path("/tmp/outputs")
_TMP_CONFIG  = Path("/tmp/config.json")

_REQUIRED_EVENT_KEYS = ("bucket", "input_prefix", "output_prefix", "config_key")


def lambda_handler(event: dict, context) -> dict:
    """Lambda entry point: download from S3, run pipeline, upload outputs."""
    logger.info("[%s] Invoked -- event: %s", _MODULE, event)

    try:
        params        = _validate_event(event)
        bucket        = params["bucket"]
        input_prefix  = params["input_prefix"]
        output_prefix = params["output_prefix"]
        config_key    = params["config_key"]

        _clean_directory(_TMP_INPUTS)
        _clean_directory(_TMP_OUTPUTS)

        download_s3_prefix(bucket, input_prefix, _TMP_INPUTS)
        download_s3_file(bucket, config_key, _TMP_CONFIG)

        summary = run_pipeline(_TMP_INPUTS, _TMP_OUTPUTS, _TMP_CONFIG)

        uploaded_keys = upload_directory(bucket, output_prefix, _TMP_OUTPUTS)

        logger.info("[%s] Completed -- %d files uploaded", _MODULE, len(uploaded_keys))
        return {
            "status":        "success",
            "summary":       summary,
            "uploaded_keys": uploaded_keys,
        }

    except Exception as exc:
        logger.error(
            "[%s] Pipeline failed -- %s: %s\n%s",
            _MODULE, type(exc).__name__, exc, traceback.format_exc(),
        )
        return {
            "status":        "error",
            "error_type":    type(exc).__name__,
            "error_message": str(exc),
        }


# -- private helpers ----------------------------------------------------------


def _clean_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _validate_event(event: dict) -> dict:
    missing = [k for k in _REQUIRED_EVENT_KEYS if k not in event]
    if missing:
        raise ValueError(f"[{_MODULE}] Missing required event keys: {missing}")
    params = {k: event[k] for k in _REQUIRED_EVENT_KEYS}
    empty = [k for k, v in params.items() if v is None or str(v).strip() == ""]
    if empty:
        raise ValueError(f"[{_MODULE}] Event keys must not be null or empty: {empty}")
    return params

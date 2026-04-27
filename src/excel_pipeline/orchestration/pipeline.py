"""Orchestrate the full pipeline: Stage 1 → Stage 2 → Stage 3."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ..config.loader import load_config
from .execution_log import write_execution_log
from ..stage_1_consolidation.consolidation import consolidate_dfs
from ..stage_1_consolidation.ingestion import load_excels
from ..stage_1_consolidation.normalization import normalize_dfs
from ..stage_2_cleaning.cleaning import run_cleaning
from ..stage_3_formatting.report_writer import write_report

logger = logging.getLogger(__name__)
_MODULE = "orchestration"


def run_pipeline(
    input_path: Path,
    output_path: Path,
    config_path: Path,
) -> dict[str, Any]:
    """Run Stage 1 → Stage 2 → Stage 3; write execution log; return summary dict."""
    input_path  = Path(input_path)
    output_path = Path(output_path)
    config_path = Path(config_path)

    started_at               = datetime.now()
    errors:   list[str]      = []
    warnings: list[str]      = []
    current_stage            = "config"
    files_processed          = 0
    rows_after_consolidation = 0
    rows_after_cleaning      = 0
    report_path: Path | None = None
    cleaning_summary: dict[str, Any] = {}

    logger.info("[%s] Pipeline started — input: %s", _MODULE, input_path)

    try:
        config = load_config(config_path)

        current_stage = "stage1"
        df_unified, files_processed = _run_stage_1(input_path, config, warnings)
        rows_after_consolidation = len(df_unified)

        current_stage = "stage2"
        df_validated, cleaning_summary = run_cleaning(df_unified)
        rows_after_cleaning = len(df_validated)

        current_stage = "stage3"
        report_path = write_report(df_validated, output_path)

    except Exception as exc:
        duration = (datetime.now() - started_at).total_seconds()
        errors.append(f"[{current_stage}] {type(exc).__name__}: {exc}")
        log_data = _build_log_data(
            started_at=started_at,
            duration=duration,
            files_processed=files_processed,
            rows_after_consolidation=rows_after_consolidation,
            rows_after_cleaning=rows_after_cleaning,
            cleaning_summary=cleaning_summary,
            errors=errors,
            warnings=warnings,
            config_path=config_path,
            input_path=input_path,
            output_path=output_path,
            report_path=None,
        )
        try:
            write_execution_log(log_data, output_path)
        except Exception as log_exc:
            logger.error("[%s] Failed to write execution log — %s", _MODULE, log_exc)
        logger.error("[%s] Pipeline failed — %s: %s", _MODULE, type(exc).__name__, exc)
        raise

    duration = (datetime.now() - started_at).total_seconds()
    log_data = _build_log_data(
        started_at=started_at,
        duration=duration,
        files_processed=files_processed,
        rows_after_consolidation=rows_after_consolidation,
        rows_after_cleaning=rows_after_cleaning,
        cleaning_summary=cleaning_summary,
        errors=errors,
        warnings=warnings,
        config_path=config_path,
        input_path=input_path,
        output_path=output_path,
        report_path=report_path,
    )
    write_execution_log(log_data, output_path)
    logger.info("[%s] Pipeline completed — %d rows exported", _MODULE, rows_after_cleaning)
    return log_data


# ── private helpers ───────────────────────────────────────────────────────────

def _run_stage_1(
    input_path: Path,
    config: dict[str, Any],
    warnings: list[str],
) -> tuple[pd.DataFrame, int]:
    """Load, normalize, and consolidate Excel files into df_unified."""
    mapping        = config["mapping"]
    schema_columns = config["column_order"]

    file_paths = sorted(
        fp for fp in input_path.glob("*.xlsx")
        if not fp.name.startswith("~$")
    )
    if not file_paths:
        raise FileNotFoundError(
            f"[stage1] No .xlsx files found in: {input_path}"
        )

    raw_dfs, source_names = _load_files_with_names(file_paths, warnings)
    normalized_dfs = normalize_dfs(raw_dfs, mapping, source_names, schema_columns)
    df_unified = consolidate_dfs(normalized_dfs)
    return df_unified, len(raw_dfs)


def _load_files_with_names(
    file_paths: list[Path],
    warnings: list[str],
) -> tuple[list[pd.DataFrame], list[str]]:
    """Call load_excels per file; track which filenames succeed."""
    raw_dfs:      list[pd.DataFrame] = []
    source_names: list[str]          = []

    for fp in file_paths:
        try:
            dfs = load_excels([fp])
            raw_dfs.append(dfs[0])
            source_names.append(fp.name)
        except RuntimeError:
            msg = f"[stage1] Skipped file: {fp.name}"
            logger.warning("[%s] %s", _MODULE, msg)
            warnings.append(msg)

    if not raw_dfs:
        raise RuntimeError(
            "[stage1] All files failed to load. Pipeline cannot continue."
        )

    return raw_dfs, source_names


def _build_log_data(
    *,
    started_at: datetime,
    duration: float,
    files_processed: int,
    rows_after_consolidation: int,
    rows_after_cleaning: int,
    cleaning_summary: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    config_path: Path,
    input_path: Path,
    output_path: Path,
    report_path: Path | None,
) -> dict[str, Any]:
    return {
        "timestamp":        started_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "files_processed":  files_processed,
        "rows_total":       rows_after_consolidation,
        "rows_per_stage":   {
            "after_consolidation": rows_after_consolidation,
            "after_cleaning":      rows_after_cleaning,
        },
        "cleaning_summary": cleaning_summary,
        "errors":           errors,
        "warnings":         warnings,
        "duration_seconds": round(duration, 3),
        "config_path":      str(config_path),
        "input_path":       str(input_path),
        "output_path":      str(output_path),
        "report_path":      str(report_path) if report_path else None,
    }

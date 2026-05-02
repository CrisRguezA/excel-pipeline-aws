"""Stage 2 public entrypoint — runs all cleaning steps and returns cleaning_summary."""

from __future__ import annotations

import logging
from typing import Callable

import pandas as pd

from .deduplication import drop_empty_rows, remove_duplicates
from .null_handling import fill_nulls
from .standardization import standardize_categoricals
from .type_coercion import coerce_dates, coerce_numerics
from .validation import validate

logger = logging.getLogger(__name__)
_STAGE = "stage2"


def run_cleaning(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply all Stage 2 cleaning steps; return (df_validated, cleaning_summary)."""
    rows_input = len(df)
    steps: dict[str, dict] = {}

    rows_before = len(df)
    df = coerce_numerics(df)
    df = coerce_dates(df)
    steps["type_coercion"] = _make_step(rows_before, len(df))

    df, steps["null_handling"]      = _apply(df, fill_nulls)
    df, steps["deduplication"]      = _apply(df, remove_duplicates)
    df, steps["standardization"]    = _apply(df, standardize_categoricals)
    df, steps["empty_row_removal"]  = _apply(df, drop_empty_rows)
    df, steps["validation"]         = _apply(df, validate)

    rows_output = len(df)
    summary = {
        "rows_in":      rows_input,
        "rows_out":     rows_output,
        "rows_removed": rows_input - rows_output,
        "steps":        steps,
        "warnings":     [],
    }
    logger.info(
        "[%s] run_cleaning — %d in, %d out, %d removed",
        _STAGE, rows_input, rows_output, rows_input - rows_output,
    )
    return df, summary


def _apply(
    df: pd.DataFrame,
    fn: Callable[[pd.DataFrame], pd.DataFrame],
) -> tuple[pd.DataFrame, dict]:
    rows_before = len(df)
    df = fn(df)
    return df, _make_step(rows_before, len(df))


def _make_step(rows_before: int, rows_after: int) -> dict:
    return {
        "rows_before":  rows_before,
        "rows_after":   rows_after,
        "rows_removed": rows_before - rows_after,
    }

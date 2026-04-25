"""Concatenates normalized DataFrames into a single unified DataFrame for Stage 1."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_STAGE = "stage1"


def consolidate_dfs(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate normalized DataFrames into a single df_unified; raises on invalid inputs."""
    _validate_input_dfs(dfs)
    _validate_column_structure(dfs)
    _log_input_row_counts(dfs)
    df_unified = pd.concat(dfs, ignore_index=True)
    logger.info(
        "[%s] Consolidation complete — %d total rows from %d DataFrames.",
        _STAGE, len(df_unified), len(dfs),
    )
    return df_unified


# ── private helpers ──────────────────────────────────────────────────────────

def _validate_input_dfs(dfs: list[pd.DataFrame]) -> None:
    if not dfs:
        logger.error("[%s] dfs must not be empty", _STAGE)
        raise ValueError(f"[{_STAGE}] dfs must not be empty")
    for i, df in enumerate(dfs):
        if not isinstance(df, pd.DataFrame):
            logger.error(
                "[%s] Item at index %d is not a DataFrame, got %s",
                _STAGE, i, type(df).__name__,
            )
            raise TypeError(
                f"[{_STAGE}] All items in dfs must be pd.DataFrame; "
                f"got {type(df).__name__} at index {i}"
            )


def _validate_column_structure(dfs: list[pd.DataFrame]) -> None:
    reference_cols = list(dfs[0].columns)
    mismatches: list[int] = []

    for i, df in enumerate(dfs[1:], start=1):
        if list(df.columns) != reference_cols:
            logger.error(
                "[%s] Column structure mismatch in DataFrame %d: expected %s, got %s",
                _STAGE, i, reference_cols, list(df.columns),
            )
            mismatches.append(i)

    if mismatches:
        raise ValueError(
            f"[{_STAGE}] Column structure mismatch in DataFrames at positions: {mismatches}"
        )


def _log_input_row_counts(dfs: list[pd.DataFrame]) -> None:
    for i, df in enumerate(dfs):
        if "source_file" in df.columns and not df.empty:
            source = df["source_file"].iloc[0]
        else:
            source = f"dataframe[{i}]"
        logger.info("[%s] Input — %s: %d rows", _STAGE, source, len(df))

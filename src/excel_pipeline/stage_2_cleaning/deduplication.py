"""Row deduplication and empty-row removal for Stage 2 cleaning."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_STAGE = "stage2"
_METADATA_COLUMNS = ("source_file",)
_ID_VENTA_COLUMN = "id_venta"


def drop_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows where all business columns are null, ignoring metadata columns."""
    _check_dataframe(df)
    df = df.copy()

    business_columns = [col for col in df.columns if col not in _METADATA_COLUMNS]
    if not business_columns:
        logger.error(
            "[%s] No business columns found in DataFrame — only metadata columns present",
            _STAGE,
        )
        raise ValueError(f"[{_STAGE}] No business columns found in DataFrame")

    rows_before = len(df)
    empty_mask = df[business_columns].isna().all(axis=1)
    df = df[~empty_mask].reset_index(drop=True)
    rows_removed = rows_before - len(df)

    logger.info(
        "[%s] drop_empty_rows — %d rows removed, %d rows remaining",
        _STAGE, rows_removed, len(df),
    )
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate non-null id_venta rows; null id_venta rows are preserved."""
    _check_dataframe(df)
    df = df.copy()
    _check_column(df, _ID_VENTA_COLUMN)

    rows_before = len(df)
    null_id_mask = df[_ID_VENTA_COLUMN].isna()
    duplicate_mask = ~null_id_mask & df[_ID_VENTA_COLUMN].duplicated(keep="first")

    df = df[~duplicate_mask].reset_index(drop=True)
    rows_removed = rows_before - len(df)

    logger.info(
        "[%s] remove_duplicates — %d duplicate rows removed, %d rows remaining",
        _STAGE, rows_removed, len(df),
    )
    return df


# ── private helpers ──────────────────────────────────────────────────────────

def _check_dataframe(df: pd.DataFrame) -> None:
    if not isinstance(df, pd.DataFrame):
        logger.error(
            "[%s] Input must be a pandas DataFrame, got %s", _STAGE, type(df).__name__
        )
        raise TypeError(
            f"[{_STAGE}] Input must be a pandas DataFrame, got {type(df).__name__}"
        )


def _check_column(df: pd.DataFrame, column: str) -> None:
    if column not in df.columns:
        logger.error("[%s] Expected column '%s' not found in DataFrame", _STAGE, column)
        raise KeyError(f"[{_STAGE}] Expected column '{column}' not found in DataFrame")

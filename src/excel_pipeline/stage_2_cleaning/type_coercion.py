"""Parses and coerces date and numeric columns for Stage 2 cleaning."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_STAGE = "stage2"
_DATE_COLUMN = "fecha_venta"
_NUMERIC_COLUMNS = ("cantidad_m3", "precio_m3", "importe")


def coerce_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse fecha_venta to datetime; invalid values become NaT."""
    df = df.copy()
    _check_column(df, _DATE_COLUMN)
    nulls_before = int(df[_DATE_COLUMN].isna().sum())
    df[_DATE_COLUMN] = pd.to_datetime(df[_DATE_COLUMN], dayfirst=True, errors="coerce")
    nulls_after = int(df[_DATE_COLUMN].isna().sum())
    _log_coercion_result(_DATE_COLUMN, nulls_before, nulls_after)
    return df


def coerce_numerics(df: pd.DataFrame) -> pd.DataFrame:
    """Parse cantidad_m3, precio_m3, and importe to float; invalid values become NaN."""
    df = df.copy()
    for column in _NUMERIC_COLUMNS:
        _check_column(df, column)
    for column in _NUMERIC_COLUMNS:
        nulls_before = int(df[column].isna().sum())
        df[column] = pd.to_numeric(_normalize_numeric_string(df[column]), errors="coerce")
        nulls_after = int(df[column].isna().sum())
        _log_coercion_result(column, nulls_before, nulls_after)
    return df


# ── private helpers ──────────────────────────────────────────────────────────

def _check_column(df: pd.DataFrame, column: str) -> None:
    if column not in df.columns:
        logger.error("[%s] Expected column '%s' not found in DataFrame", _STAGE, column)
        raise KeyError(f"[{_STAGE}] Expected column '{column}' not found in DataFrame")


def _normalize_numeric_string(series: pd.Series) -> pd.Series:
    null_mask = series.isna()
    normalized = (
        series.astype(str)
        .str.strip()
        .str.replace(r"[$€£]", "", regex=True)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
    )
    return normalized.mask(null_mask)


def _log_coercion_result(column: str, nulls_before: int, nulls_after: int) -> None:
    new_nulls = nulls_after - nulls_before
    logger.info(
        "[%s] Coerced '%s' — nulls before: %d, after: %d (%+d from coercion)",
        _STAGE, column, nulls_before, nulls_after, new_nulls,
    )

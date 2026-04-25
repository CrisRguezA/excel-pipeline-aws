"""Validation step for Stage 2 — drops rows that fail business rules."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_STAGE = "stage2"
_REQUIRED_NOT_NULL = ("id_venta", "fecha_venta", "importe")
_REQUIRED_POSITIVE = ("importe", "cantidad_m3", "precio_m3")
_UNIQUE_COLUMN = "id_venta"
_ALL_VALIDATED_COLUMNS = ("id_venta", "fecha_venta", "importe", "cantidad_m3", "precio_m3")


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows failing validation rules: required not null, positive numerics, unique id_venta."""
    _check_dataframe(df)
    df = df.copy()
    for column in _ALL_VALIDATED_COLUMNS:
        _check_column(df, column)

    df = _drop_null_required(df)
    df = _drop_non_positive(df)
    df = _drop_duplicate_ids(df)
    return df


# ── private helpers ──────────────────────────────────────────────────────────

def _drop_null_required(df: pd.DataFrame) -> pd.DataFrame:
    for column in _REQUIRED_NOT_NULL:
        rows_before = len(df)
        df = df[df[column].notna()].reset_index(drop=True)
        rows_dropped = rows_before - len(df)
        logger.info(
            "[%s] validate — rule: null_%s — %d rows checked, %d rows dropped",
            _STAGE, column, rows_before, rows_dropped,
        )
    return df


def _drop_non_positive(df: pd.DataFrame) -> pd.DataFrame:
    for column in _REQUIRED_POSITIVE:
        rows_before = len(df)
        df = df[df[column].isna() | (df[column] > 0)].reset_index(drop=True)
        rows_dropped = rows_before - len(df)
        logger.info(
            "[%s] validate — rule: positive_%s — %d rows checked, %d rows dropped",
            _STAGE, column, rows_before, rows_dropped,
        )
    return df


def _drop_duplicate_ids(df: pd.DataFrame) -> pd.DataFrame:
    rows_before = len(df)
    null_id_mask = df[_UNIQUE_COLUMN].isna()
    duplicate_mask = ~null_id_mask & df[_UNIQUE_COLUMN].duplicated(keep="first")
    df = df[~duplicate_mask].reset_index(drop=True)
    rows_dropped = rows_before - len(df)
    logger.info(
        "[%s] validate — rule: unique_%s — %d rows checked, %d rows dropped",
        _STAGE, _UNIQUE_COLUMN, rows_before, rows_dropped,
    )
    return df


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

"""Null-handling operations for Stage 2 cleaning."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_STAGE = "stage2"
_IMPORTE_COLUMNS = ("importe", "cantidad_m3", "precio_m3")


def recalculate_importe(df: pd.DataFrame) -> pd.DataFrame:
    """Recalculate importe as cantidad_m3 × precio_m3 where importe is null."""
    df = df.copy()
    for column in _IMPORTE_COLUMNS:
        _check_column(df, column)

    mask_recalc = (
        df["importe"].isna()
        & df["cantidad_m3"].notna()
        & df["precio_m3"].notna()
    )
    mask_unrecoverable = df["importe"].isna() & ~mask_recalc

    df.loc[mask_recalc, "importe"] = (
        df.loc[mask_recalc, "cantidad_m3"] * df.loc[mask_recalc, "precio_m3"]
    )

    n_recovered = int(mask_recalc.sum())
    n_unrecoverable = int(mask_unrecoverable.sum())
    n_zero_result = int((mask_recalc & (df["importe"] == 0)).sum())

    logger.info(
        "[%s] recalculate_importe — %d rows recovered, %d rows unrecoverable",
        _STAGE, n_recovered, n_unrecoverable,
    )
    if n_unrecoverable > 0:
        logger.warning(
            "[%s] %d rows have null importe and missing cantidad_m3 or precio_m3 — cannot recalculate",
            _STAGE, n_unrecoverable,
        )
    if n_zero_result > 0:
        logger.warning(
            "[%s] %d rows recalculated importe as zero — will fail importe > 0 validation",
            _STAGE, n_zero_result,
        )

    return df


def fill_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Fill nulls in importe (via recalculation), certificacion, and pais."""
    df = recalculate_importe(df)
    df = _fill_column(df, "certificacion", "Sin certificación")
    df = _fill_column(df, "pais", "España")
    return df


# ── private helpers ──────────────────────────────────────────────────────────

def _check_column(df: pd.DataFrame, column: str) -> None:
    if column not in df.columns:
        logger.error("[%s] Expected column '%s' not found in DataFrame", _STAGE, column)
        raise KeyError(f"[{_STAGE}] Expected column '{column}' not found in DataFrame")


def _fill_column(df: pd.DataFrame, column: str, fill_value: str) -> pd.DataFrame:
    _check_column(df, column)

    if pd.api.types.is_string_dtype(df[column]) or df[column].dtype == "object":
        blank_mask = df[column].astype("string").str.strip().eq("")
        df.loc[blank_mask, column] = pd.NA

    nulls_before = int(df[column].isna().sum())
    df[column] = df[column].fillna(fill_value)
    nulls_filled = nulls_before - int(df[column].isna().sum())
    logger.info(
        "[%s] Filled '%s' — %d nulls filled with %r",
        _STAGE, column, nulls_filled, fill_value,
    )
    return df

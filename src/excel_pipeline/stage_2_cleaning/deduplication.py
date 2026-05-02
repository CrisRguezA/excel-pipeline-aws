"""Row deduplication and empty-row removal for Stage 2 cleaning."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_STAGE = "stage2"
_METADATA_COLUMNS = ("source_file",)
_ID_VENTA_COLUMN = "id_venta"
_COMPLETENESS_FIELDS = ("id_venta", "fecha_venta", "importe", "cantidad_m3", "precio_m3")


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
    """Keep the most complete row per non-null id_venta; null id_venta rows are all preserved."""
    _check_dataframe(df)
    df = df.copy()
    _check_column(df, _ID_VENTA_COLUMN)

    rows_before = len(df)
    df["_row_order"] = range(len(df))
    null_id_mask = _is_null_or_empty(df[_ID_VENTA_COLUMN])

    df_null    = df[null_id_mask]
    df_nonnull = df[~null_id_mask].copy()

    if not df_nonnull.empty:
        df_nonnull["_score"] = _completeness_score(df_nonnull)
        df_nonnull = (
            df_nonnull
            .sort_values(
                [_ID_VENTA_COLUMN, "_score", "_row_order"],
                ascending=[True, False, True],
                kind="stable",
            )
            .drop_duplicates(subset=[_ID_VENTA_COLUMN], keep="first")
            .drop(columns=["_score"])
        )

    df = (
        pd.concat([df_null, df_nonnull])
        .sort_values("_row_order")
        .drop(columns=["_row_order"])
        .reset_index(drop=True)
    )
    rows_removed = rows_before - len(df)

    logger.info(
        "[%s] remove_duplicates — %d duplicate rows removed, %d rows remaining",
        _STAGE, rows_removed, len(df),
    )
    return df


# ── private helpers ──────────────────────────────────────────────────────────


def _completeness_score(df: pd.DataFrame) -> pd.Series:
    """Count non-null, non-empty values across _COMPLETENESS_FIELDS for each row."""
    present = [col for col in _COMPLETENESS_FIELDS if col in df.columns]
    return (~df[present].apply(_is_null_or_empty)).sum(axis=1)


def _is_null_or_empty(series: pd.Series) -> pd.Series:
    """Return True where a value is null or an empty/whitespace-only string."""
    null_mask      = series.isna()
    empty_str_mask = (~null_mask) & (series.astype(str).str.strip() == "")
    return null_mask | empty_str_mask


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

"""Categorical and text standardization for Stage 2 cleaning."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_STAGE = "stage2"

_ESTADO_MAP = {
    "cerrado":   "Cerrado",
    "cerrada":   "Cerrado",
    "ok":        "Cerrado",
    "pendiente": "Pendiente",
    "cancelado": "Cancelado",
}

_PAIS_MAP = {
    "es":     "España",
    "españa": "España",
    "espana": "España",
}

_TEXT_COLUMNS = ("cliente", "comercial", "tipo_madera")


def standardize_estado(df: pd.DataFrame) -> pd.DataFrame:
    """Map known estado variants to canonical values; unknown values are only stripped."""
    df = df.copy()
    _check_column(df, "estado")

    original = df["estado"].copy()
    mask = df["estado"].notna()

    stripped = df.loc[mask, "estado"].astype(str).str.strip()
    mapped = stripped.str.lower().map(_ESTADO_MAP)
    df.loc[mask, "estado"] = mapped.where(mapped.notna(), stripped)

    n_changed = int((df["estado"].notna() & (df["estado"] != original)).sum())
    logger.info("[%s] Standardized 'estado' — %d values changed", _STAGE, n_changed)
    return df


def standardize_pais(df: pd.DataFrame) -> pd.DataFrame:
    """Map known pais variants to España; unknown values are only stripped."""
    df = df.copy()
    _check_column(df, "pais")

    original = df["pais"].copy()
    mask = df["pais"].notna()

    stripped = df.loc[mask, "pais"].astype(str).str.strip()
    mapped = stripped.str.lower().map(_PAIS_MAP)
    df.loc[mask, "pais"] = mapped.where(mapped.notna(), stripped)

    n_changed = int((df["pais"].notna() & (df["pais"] != original)).sum())
    logger.info("[%s] Standardized 'pais' — %d values changed", _STAGE, n_changed)
    return df


def standardize_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from cliente, comercial, and tipo_madera."""
    df = df.copy()
    for column in _TEXT_COLUMNS:
        _check_column(df, column)

    for column in _TEXT_COLUMNS:
        original = df[column].copy()
        mask = df[column].notna()

        df.loc[mask, column] = df.loc[mask, column].astype(str).str.strip()

        n_changed = int((df[column].notna() & (df[column] != original)).sum())
        logger.info(
            "[%s] Standardized '%s' — %d values changed", _STAGE, column, n_changed
        )

    return df


def standardize_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all categorical and text standardization for Stage 2."""
    df = standardize_estado(df)
    df = standardize_pais(df)
    df = standardize_text_fields(df)
    return df


# ── private helpers ──────────────────────────────────────────────────────────

def _check_column(df: pd.DataFrame, column: str) -> None:
    if column not in df.columns:
        logger.error("[%s] Expected column '%s' not found in DataFrame", _STAGE, column)
        raise KeyError(f"[{_STAGE}] Expected column '{column}' not found in DataFrame")

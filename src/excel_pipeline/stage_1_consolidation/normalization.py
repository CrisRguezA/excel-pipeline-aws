"""Normalizes raw DataFrames to a standard schema for Stage 1 consolidation."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_STAGE = "stage1"


def normalize_df(
    df: pd.DataFrame,
    mapping: dict[str, list[str]],
    source_name: str,
    schema_columns: list[str],
) -> pd.DataFrame:
    """Map raw column variants to standard names for a single DataFrame."""
    _validate_schema_columns(schema_columns)
    df = _strip_column_headers(df)
    _check_duplicate_headers(df, source_name)
    out, matched_source_cols = _apply_mapping(df, mapping, schema_columns, source_name)
    _log_unmapped_columns(df, matched_source_cols, source_name)
    out["source_file"] = source_name
    return out.reset_index(drop=True)


def normalize_dfs(
    dfs: list[pd.DataFrame],
    mapping: dict[str, list[str]],
    source_names: list[str],
    schema_columns: list[str],
) -> list[pd.DataFrame]:
    """Apply normalize_df() to a list of raw DataFrames; raises on invalid inputs."""
    if len(dfs) != len(source_names):
        raise ValueError(
            f"[{_STAGE}] dfs and source_names must have the same length "
            f"(got {len(dfs)} and {len(source_names)})"
        )
    if not mapping:
        raise ValueError(f"[{_STAGE}] mapping must not be empty")
    _validate_schema_columns(schema_columns)

    normalized = []
    for df, source_name in zip(dfs, source_names):
        df_norm = normalize_df(df, mapping, source_name, schema_columns)
        logger.info(
            "[%s] Normalized — %s: %d rows × %d columns",
            _STAGE, source_name, df_norm.shape[0], df_norm.shape[1],
        )
        normalized.append(df_norm)

    logger.info(
        "[%s] Normalization complete — %d/%d files normalized successfully.",
        _STAGE, len(normalized), len(dfs),
    )
    return normalized


# ── private helpers ──────────────────────────────────────────────────────────

def _validate_schema_columns(schema_columns: list[str]) -> None:
    if not schema_columns:
        logger.error("[%s] schema_columns must not be empty", _STAGE)
        raise ValueError(f"[{_STAGE}] schema_columns must not be empty")
    for col in schema_columns:
        if not isinstance(col, str) or not col.strip():
            logger.error(
                "[%s] schema_columns must contain only non-empty strings, got %r", _STAGE, col
            )
            raise ValueError(
                f"[{_STAGE}] schema_columns must contain only non-empty strings, got {col!r}"
            )
    if "source_file" in schema_columns:
        logger.error(
            '[%s] "source_file" is reserved metadata and must not appear in schema_columns',
            _STAGE,
        )
        raise ValueError(
            f'[{_STAGE}] "source_file" is reserved metadata and must not appear in schema_columns'
        )


def _strip_column_headers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
    return df


def _check_duplicate_headers(df: pd.DataFrame, source_name: str) -> None:
    cols = pd.Index(df.columns)
    duplicates = cols[cols.duplicated()].tolist()
    if duplicates:
        logger.error(
            "[%s] Duplicate column headers after stripping in %s: %s",
            _STAGE, source_name, duplicates,
        )
        raise ValueError(
            f"[{_STAGE}] Duplicate column headers found in {source_name}: {duplicates}"
        )


def _apply_mapping(
    df: pd.DataFrame,
    mapping: dict[str, list[str]],
    schema_columns: list[str],
    source_name: str,
) -> tuple[pd.DataFrame, set[str]]:
    out = pd.DataFrame()
    matched_source_cols: set[str] = set()

    for standard_name in schema_columns:
        synonyms = list(dict.fromkeys([standard_name, *mapping.get(standard_name, [])]))
        found = [s for s in synonyms if s in df.columns]

        if not found:
            out[standard_name] = pd.NA
            logger.warning(
                "[%s] Missing standard column '%s' — filled with NaN — %s",
                _STAGE, standard_name, source_name,
            )
        elif len(found) == 1:
            out[standard_name] = df[found[0]]
            matched_source_cols.add(found[0])
        else:
            out[standard_name] = _merge_duplicate_columns(
                df, found, standard_name, source_name
            )
            matched_source_cols.update(found)

    return out, matched_source_cols


def _merge_duplicate_columns(
    df: pd.DataFrame,
    found: list[str],
    standard_name: str,
    source_name: str,
) -> pd.Series:
    logger.info(
        "[%s] Merging %d variant columns for '%s': %s — %s",
        _STAGE, len(found), standard_name, found, source_name,
    )
    combined = df[found[0]]
    for col in found[1:]:
        combined = combined.combine_first(df[col])
    return combined


def _log_unmapped_columns(
    df: pd.DataFrame,
    matched_source_cols: set[str],
    source_name: str,
) -> None:
    unmapped = [col for col in df.columns if col not in matched_source_cols]
    if unmapped:
        logger.warning(
            "[%s] Unmapped source columns in %s: %s",
            _STAGE, source_name, unmapped,
        )

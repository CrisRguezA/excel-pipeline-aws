"""Loads and validates the column mapping section from a pipeline config JSON."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_STAGE = "stage1"


def load_mapping(config_path: Path) -> dict[str, list[str]]:
    """Load config JSON and return the column mapping as {standard_name: [synonyms]}.

    Validates only that the "mapping" key exists and that its value is a dict
    whose keys are non-empty strings and whose values are non-empty lists of
    non-empty strings (after stripping whitespace). Raises on any failure.
    """
    config_path = Path(config_path)
    raw = _read_config(config_path)
    mapping = _extract_mapping(raw, config_path)

    cleaned = _validate_mapping_shape(mapping, config_path)

    logger.info(
        "[%s] Config loaded — %s: %d standard columns mapped.",
        _STAGE, config_path.name, len(cleaned),
    )
    return cleaned


# ── private helpers ──────────────────────────────────────────────────────────

def _read_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(
            f"[{_STAGE}] Config file not found: {config_path}"
        )

    try:
        with open(config_path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except json.JSONDecodeError as exc:
        logger.error("[%s] Config is not valid JSON — %s: %s", _STAGE, config_path.name, exc)
        raise

    if not isinstance(raw, dict):
        raise TypeError(f"[{_STAGE}] Config root must be a JSON object: {config_path}")

    return raw


def _extract_mapping(raw: dict, config_path: Path) -> dict:
    if "mapping" not in raw:
        logger.error(
            '[%s] Config missing required "mapping" key — %s', _STAGE, config_path.name
        )
        raise KeyError(f'[{_STAGE}] "mapping" key not found in config: {config_path}')

    if not isinstance(raw["mapping"], dict):
        logger.error(
            '[%s] "mapping" must be a dict, got %s — %s',
            _STAGE, type(raw["mapping"]).__name__, config_path.name,
        )
        raise TypeError(
            f'[{_STAGE}] "mapping" must be a dict in config: {config_path}'
        )

    return raw["mapping"]


def _validate_mapping_shape(mapping: dict, config_path: Path) -> dict[str, list[str]]:
    cleaned: dict[str, list[str]] = {}

    for standard_name, synonyms in mapping.items():
        if not isinstance(standard_name, str) or not standard_name.strip():
            logger.error(
                '[%s] Standard column name must be a non-empty string, got %r — %s',
                _STAGE, standard_name, config_path.name,
            )
            raise ValueError(
                f'[{_STAGE}] Standard column name must be a non-empty string in config: {config_path}'
            )

        if not isinstance(synonyms, list):
            logger.error(
                '[%s] Synonyms for "%s" must be a list, got %s — %s',
                _STAGE, standard_name, type(synonyms).__name__, config_path.name,
            )
            raise TypeError(
                f'[{_STAGE}] Synonyms for "{standard_name}" must be a list in config: {config_path}'
            )

        if not synonyms:
            logger.error(
                '[%s] Synonym list for "%s" is empty — %s',
                _STAGE, standard_name, config_path.name,
            )
            raise ValueError(
                f'[{_STAGE}] Synonym list for "{standard_name}" is empty in config: {config_path}'
            )

        cleaned_synonyms: list[str] = []
        for i, synonym in enumerate(synonyms):
            if not isinstance(synonym, str):
                logger.error(
                    '[%s] Synonym[%d] for "%s" must be a string, got %s — %s',
                    _STAGE, i, standard_name, type(synonym).__name__, config_path.name,
                )
                raise TypeError(
                    f'[{_STAGE}] Synonym[{i}] for "{standard_name}" must be a string in config: {config_path}'
                )

            stripped = synonym.strip()
            if not stripped:
                logger.error(
                    '[%s] Synonym[%d] for "%s" is empty or blank after stripping — %s',
                    _STAGE, i, standard_name, config_path.name,
                )
                raise ValueError(
                    f'[{_STAGE}] Synonym[{i}] for "{standard_name}" is empty or blank in config: {config_path}'
                )

            cleaned_synonyms.append(stripped)

        cleaned[standard_name.strip()] = cleaned_synonyms

    return cleaned

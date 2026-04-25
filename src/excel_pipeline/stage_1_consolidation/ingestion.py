"""Loads raw Excel source files into DataFrames for Stage 1 consolidation."""

import argparse
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_STAGE = "stage1"


def load_excels(file_paths: list[Path]) -> list[pd.DataFrame]:
    """Loads Excel files as string DataFrames; skips empty or unreadable files."""
    loaded: list[pd.DataFrame] = []

    for file_path in file_paths:
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error("[%s] File not found: %s", _STAGE, file_path)
            continue

        try:
            df = pd.read_excel(file_path, dtype=str)
        except Exception as exc:
            logger.error("[%s] Read error — %s: %s", _STAGE, file_path.name, exc)
            continue

        if df.empty:
            logger.warning(
                "[%s] Empty file skipped — %s (0 rows)", _STAGE, file_path.name
            )
            continue

        logger.info(
            "[%s] Loaded — %s: %d rows × %d columns",
            _STAGE, file_path.name, df.shape[0], df.shape[1],
        )
        loaded.append(df)

    if not loaded:
        raise RuntimeError(
            f"[{_STAGE}] All files failed to load. Pipeline cannot continue."
        )

    logger.info(
        "[%s] Ingestion complete — %d/%d files loaded successfully.",
        _STAGE, len(loaded), len(file_paths),
    )
    return loaded


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s — %(message)s")

    parser = argparse.ArgumentParser(
        description="Stage 1 ingestion — load Excel source files."
    )
    parser.add_argument(
        "data_dir",
        type=Path,
        nargs="?",
        default=Path(__file__).resolve().parents[3] / "data" / "raw",
        help="Directory containing .xlsx files (default: <project_root>/data/raw)",
    )
    args = parser.parse_args()

    source_files = sorted(args.data_dir.glob("*.xlsx"))

    if not source_files:
        raise FileNotFoundError(f"No .xlsx files found in: {args.data_dir}")

    logger.info("[%s] Loading %d files from: %s", _STAGE, len(source_files), args.data_dir)
    load_excels(source_files)

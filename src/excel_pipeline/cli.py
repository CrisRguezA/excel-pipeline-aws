"""CLI entry point for the Excel Pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .orchestration.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Excel processing pipeline.")
    parser.add_argument("--input",  required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args(argv)
    summary = run_pipeline(args.input, args.output, args.config)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

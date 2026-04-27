import json
from pathlib import Path
from unittest.mock import patch

import pytest

from excel_pipeline.cli import main


_SAMPLE_RESULT = {
    "timestamp":        "2026-04-27T11:40:00",
    "files_processed":  2,
    "rows_total":       50,
    "rows_per_stage":   {"after_consolidation": 50, "after_cleaning": 48},
    "errors":           [],
    "warnings":         [],
    "duration_seconds": 0.5,
    "config_path":      "/config.json",
    "input_path":       "/input",
    "output_path":      "/output",
    "report_path":      "/output/report.xlsx",
}

_ARGS = ["--input", "/input", "--output", "/output", "--config", "/config.json"]


class TestCLIMain:
    def test_calls_run_pipeline_with_path_objects(self):
        with patch("excel_pipeline.cli.run_pipeline", return_value=_SAMPLE_RESULT) as mock_run:
            main(_ARGS)
        mock_run.assert_called_once_with(Path("/input"), Path("/output"), Path("/config.json"))

    def test_successful_run_returns_zero_and_prints_json(self, capsys):
        with patch("excel_pipeline.cli.run_pipeline", return_value=_SAMPLE_RESULT):
            exit_code = main(_ARGS)
        out = capsys.readouterr().out
        assert exit_code == 0
        assert '\n  "timestamp":' in out
        assert '\n  "rows_per_stage": {' in out

    def test_missing_required_arg_exits_nonzero(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--input", "/input"])
        assert exc_info.value.code != 0

    def test_pipeline_exception_propagates(self):
        with patch("excel_pipeline.cli.run_pipeline", side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError, match="boom"):
                main(_ARGS)

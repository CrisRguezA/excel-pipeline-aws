import json

import pytest

from excel_pipeline.orchestration.execution_log import write_execution_log


_VALID_LOG = {
    "timestamp":        "2026-04-27T11:40:00",
    "files_processed":  3,
    "rows_total":       100,
    "rows_per_stage":   {"after_consolidation": 100, "after_cleaning": 95},
    "errors":           [],
    "warnings":         [],
    "duration_seconds": 1.5,
}


class TestWriteExecutionLog:
    def test_valid_log_writes_json_and_returns_path(self, tmp_path):
        result = write_execution_log(_VALID_LOG, tmp_path)
        assert result.exists()
        assert result.suffix == ".json"
        assert result.name.startswith("execution_log_")

    def test_output_directory_created_if_missing(self, tmp_path):
        subdir = tmp_path / "new" / "nested"
        result = write_execution_log(_VALID_LOG, subdir)
        assert subdir.is_dir()
        assert result.exists()

    def test_missing_required_key_raises_key_error(self, tmp_path):
        incomplete = {k: v for k, v in _VALID_LOG.items() if k != "rows_per_stage"}
        with pytest.raises(KeyError):
            write_execution_log(incomplete, tmp_path)

    def test_non_dict_log_data_raises_type_error(self, tmp_path):
        with pytest.raises(TypeError):
            write_execution_log(["not", "a", "dict"], tmp_path)

    def test_output_path_file_raises_value_error(self, tmp_path):
        existing_file = tmp_path / "existing.json"
        existing_file.write_text("{}", encoding="utf-8")
        with pytest.raises(ValueError):
            write_execution_log(_VALID_LOG, existing_file)

    def test_json_utf8_ensure_ascii_false_indent2(self, tmp_path):
        log_with_unicode = {**_VALID_LOG, "warnings": ["precio: 10€"]}
        result = write_execution_log(log_with_unicode, tmp_path)
        raw = result.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert data["warnings"] == ["precio: 10€"]
        assert "€" in raw
        assert '\n  "timestamp":' in raw
        assert '\n    "after_consolidation":' in raw

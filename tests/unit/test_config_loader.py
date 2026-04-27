import json

import pytest

from excel_pipeline.config.loader import load_config


_VALID_CONFIG = {
    "column_order":     ["col_a", "col_b"],
    "required_columns": ["col_a"],
    "mapping":          {"col_a": ["Col A", "column_a"]},
}


@pytest.fixture()
def config_file(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(_VALID_CONFIG), encoding="utf-8")
    return path


class TestLoadConfig:
    def test_valid_config_returns_dict(self, config_file):
        result = load_config(config_file)
        assert isinstance(result, dict)
        assert result["column_order"] == ["col_a", "col_b"]

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.json")

    def test_directory_path_raises_value_error(self, tmp_path):
        with pytest.raises(ValueError):
            load_config(tmp_path)

    def test_malformed_json_raises_value_error(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ValueError):
            load_config(bad)

    def test_non_dict_json_raises_type_error(self, tmp_path):
        arr = tmp_path / "array.json"
        arr.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with pytest.raises(TypeError):
            load_config(arr)

    def test_missing_required_key_raises_key_error(self, tmp_path):
        incomplete = tmp_path / "incomplete.json"
        incomplete.write_text(
            json.dumps({"column_order": ["col_a"], "mapping": {}}),
            encoding="utf-8",
        )
        with pytest.raises(KeyError):
            load_config(incomplete)

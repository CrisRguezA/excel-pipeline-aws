"""Integration tests for orchestration.pipeline.run_pipeline."""

from __future__ import annotations

import pytest
import pandas as pd

from excel_pipeline.orchestration.pipeline import run_pipeline

_PATCH_BASE = "excel_pipeline.orchestration.pipeline"

_CLEANING_SUMMARY_STUB = {
    "rows_input":         2,
    "rows_output":        2,
    "rows_removed_total": 0,
    "steps": {
        "type_coercion":    {"rows_before": 2, "rows_after": 2, "rows_removed": 0},
        "null_handling":    {"rows_before": 2, "rows_after": 2, "rows_removed": 0},
        "deduplication":    {"rows_before": 2, "rows_after": 2, "rows_removed": 0},
        "standardization":  {"rows_before": 2, "rows_after": 2, "rows_removed": 0},
        "empty_row_removal":{"rows_before": 2, "rows_after": 2, "rows_removed": 0},
        "validation":       {"rows_before": 2, "rows_after": 2, "rows_removed": 0},
    },
    "warnings": [],
}

_MINIMAL_DF = pd.DataFrame({
    "id_venta":      ["V-001", "V-002"],
    "cliente":       ["ACME", "Beta"],
    "fecha_venta":   [pd.Timestamp("2026-01-05"), pd.Timestamp("2026-01-06")],
    "producto":      ["CLT", "Viga"],
    "tipo_madera":   ["Abeto", "Pino"],
    "certificacion": ["FSC", "PEFC"],
    "cantidad_m3":   [10.0, 5.0],
    "precio_m3":     [150.0, 200.0],
    "importe":       [1500.0, 1000.0],
    "estado":        ["Cerrado", "Pendiente"],
    "comercial":     ["Ana", "Luis"],
    "pais":          ["España", "Francia"],
})

_MINIMAL_CONFIG = {
    "column_order":     list(_MINIMAL_DF.columns),
    "required_columns": ["id_venta"],
    "mapping":          {"id_venta": ["Venta ID"]},
}


@pytest.fixture()
def pipeline_env(tmp_path, monkeypatch):
    input_dir  = tmp_path / "input"
    output_dir = tmp_path / "output"
    config_f   = tmp_path / "config.json"
    input_dir.mkdir()
    (input_dir / "source.xlsx").touch()

    fake_report = output_dir / "weekly_sales_report_20260427_114000.xlsx"
    captured: dict = {}

    monkeypatch.setattr(f"{_PATCH_BASE}.load_config",     lambda p: _MINIMAL_CONFIG)
    monkeypatch.setattr(f"{_PATCH_BASE}.load_excels",     lambda fps: [_MINIMAL_DF])
    monkeypatch.setattr(f"{_PATCH_BASE}.normalize_dfs",   lambda *a, **kw: [_MINIMAL_DF])
    monkeypatch.setattr(f"{_PATCH_BASE}.consolidate_dfs", lambda dfs: _MINIMAL_DF)
    monkeypatch.setattr(
        f"{_PATCH_BASE}.run_cleaning",
        lambda df: (_MINIMAL_DF, _CLEANING_SUMMARY_STUB),
    )
    monkeypatch.setattr(f"{_PATCH_BASE}.write_report", lambda df, p: fake_report)

    def _capture_log(log_data, out_path):
        captured["log_data"] = log_data
        return out_path / "execution_log_stub.json"

    monkeypatch.setattr(f"{_PATCH_BASE}.write_execution_log", _capture_log)

    return {
        "input_dir":   input_dir,
        "output_dir":  output_dir,
        "config_f":    config_f,
        "captured":    captured,
        "fake_report": fake_report,
    }


class TestRunPipeline:
    def test_successful_run_returns_summary(self, pipeline_env):
        env = pipeline_env
        result = run_pipeline(env["input_dir"], env["output_dir"], env["config_f"])
        assert isinstance(result, dict)
        for key in ("timestamp", "files_processed", "rows_total", "rows_per_stage",
                    "cleaning_summary", "errors", "warnings", "duration_seconds"):
            assert key in result

    def test_load_config_called_with_config_path(self, pipeline_env, monkeypatch):
        env = pipeline_env
        called_with: dict = {}
        def capture(p):
            called_with["path"] = p
            return _MINIMAL_CONFIG
        monkeypatch.setattr(f"{_PATCH_BASE}.load_config", capture)
        run_pipeline(env["input_dir"], env["output_dir"], env["config_f"])
        assert called_with["path"] == env["config_f"]

    def test_execution_log_written_on_success(self, pipeline_env):
        env = pipeline_env
        run_pipeline(env["input_dir"], env["output_dir"], env["config_f"])
        assert "log_data" in env["captured"]
        assert env["captured"]["log_data"]["errors"] == []

    def test_execution_log_written_on_failure(self, pipeline_env, monkeypatch):
        env = pipeline_env
        def _raise(df, p):
            raise RuntimeError("boom")
        monkeypatch.setattr(f"{_PATCH_BASE}.write_report", _raise)
        with pytest.raises(RuntimeError):
            run_pipeline(env["input_dir"], env["output_dir"], env["config_f"])
        log = env["captured"]["log_data"]
        assert len(log["errors"]) == 1
        assert log["errors"][0] == "[stage3] RuntimeError: boom"

    def test_original_exception_is_reraised(self, pipeline_env, monkeypatch):
        env = pipeline_env
        def _raise(dfs):
            raise ValueError("stage1 broke")
        monkeypatch.setattr(f"{_PATCH_BASE}.consolidate_dfs", _raise)
        with pytest.raises(ValueError, match="stage1 broke"):
            run_pipeline(env["input_dir"], env["output_dir"], env["config_f"])

    def test_original_exception_raised_when_log_write_also_fails(
        self, pipeline_env, monkeypatch
    ):
        env = pipeline_env
        def _raise_stage(df, p):
            raise RuntimeError("stage3 boom")
        def _raise_log(log_data, out_path):
            raise OSError("disk full")
        monkeypatch.setattr(f"{_PATCH_BASE}.write_report", _raise_stage)
        monkeypatch.setattr(f"{_PATCH_BASE}.write_execution_log", _raise_log)
        with pytest.raises(RuntimeError, match="stage3 boom"):
            run_pipeline(env["input_dir"], env["output_dir"], env["config_f"])

    def test_summary_contains_row_counts_and_report_path(self, pipeline_env):
        env = pipeline_env
        result = run_pipeline(env["input_dir"], env["output_dir"], env["config_f"])
        assert result["files_processed"] == 1
        assert result["rows_per_stage"]["after_consolidation"] == 2
        assert result["rows_per_stage"]["after_cleaning"] == 2
        assert result["report_path"] == str(env["fake_report"])
        assert "cleaning_summary" in result

    def test_lock_files_excluded_from_input(self, pipeline_env, monkeypatch):
        env = pipeline_env
        (env["input_dir"] / "~$locked.xlsx").touch()
        seen: list = []
        def capture_load(fps):
            seen.extend(fps)
            return [_MINIMAL_DF]
        monkeypatch.setattr(f"{_PATCH_BASE}.load_excels", capture_load)
        run_pipeline(env["input_dir"], env["output_dir"], env["config_f"])
        assert not any(fp.name.startswith("~$") for fp in seen)

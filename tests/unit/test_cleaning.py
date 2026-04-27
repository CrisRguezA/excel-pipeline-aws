"""Unit tests for stage_2_cleaning.cleaning.run_cleaning."""

from __future__ import annotations

import pandas as pd
import pytest

from excel_pipeline.stage_2_cleaning.cleaning import run_cleaning

_MODULE = "excel_pipeline.stage_2_cleaning.cleaning"

# Predetermined DataFrames returned by fakes — sized to produce deterministic step drops.
# deduplication: 10→8 (-2), empty_row_removal: 8→6 (-2), validation: 6→4 (-2)
_DF_10 = pd.DataFrame({"id": range(10)})
_DF_8  = pd.DataFrame({"id": range(8)})
_DF_6  = pd.DataFrame({"id": range(6)})
_DF_4  = pd.DataFrame({"id": range(4)})


@pytest.fixture()
def patched_cleaning(monkeypatch):
    """Patch all Stage 2 functions with fakes that produce deterministic row drops."""
    monkeypatch.setattr(f"{_MODULE}.coerce_numerics",          lambda df: df)
    monkeypatch.setattr(f"{_MODULE}.coerce_dates",             lambda df: df)
    monkeypatch.setattr(f"{_MODULE}.fill_nulls",               lambda df: df)
    monkeypatch.setattr(f"{_MODULE}.remove_duplicates",        lambda df: _DF_8)
    monkeypatch.setattr(f"{_MODULE}.standardize_categoricals", lambda df: df)
    monkeypatch.setattr(f"{_MODULE}.drop_empty_rows",          lambda df: _DF_6)
    monkeypatch.setattr(f"{_MODULE}.validate",                 lambda df: _DF_4)


class TestRunCleaning:
    def test_returns_dataframe_and_dict(self, patched_cleaning):
        df, summary = run_cleaning(_DF_10.copy())
        assert isinstance(df, pd.DataFrame)
        assert isinstance(summary, dict)

    def test_summary_has_required_keys(self, patched_cleaning):
        _, summary = run_cleaning(_DF_10.copy())
        for key in ("rows_input", "rows_output", "rows_removed_total", "steps", "warnings"):
            assert key in summary

    def test_steps_has_all_six_step_names(self, patched_cleaning):
        _, summary = run_cleaning(_DF_10.copy())
        assert set(summary["steps"].keys()) == {
            "type_coercion", "null_handling", "deduplication",
            "standardization", "empty_row_removal", "validation",
        }

    def test_each_step_has_row_count_metrics(self, patched_cleaning):
        _, summary = run_cleaning(_DF_10.copy())
        for name, step in summary["steps"].items():
            for metric in ("rows_before", "rows_after", "rows_removed"):
                assert metric in step, f"step '{name}' missing '{metric}'"

    def test_row_counts_per_step(self, patched_cleaning):
        """Fakes: deduplication drops 2, empty_row_removal drops 2, validation drops 2."""
        _, summary = run_cleaning(_DF_10.copy())
        steps = summary["steps"]
        assert steps["type_coercion"]     == {"rows_before": 10, "rows_after": 10, "rows_removed": 0}
        assert steps["null_handling"]     == {"rows_before": 10, "rows_after": 10, "rows_removed": 0}
        assert steps["deduplication"]     == {"rows_before": 10, "rows_after":  8, "rows_removed": 2}
        assert steps["standardization"]   == {"rows_before":  8, "rows_after":  8, "rows_removed": 0}
        assert steps["empty_row_removal"] == {"rows_before":  8, "rows_after":  6, "rows_removed": 2}
        assert steps["validation"]        == {"rows_before":  6, "rows_after":  4, "rows_removed": 2}

    def test_summary_totals(self, patched_cleaning):
        _, summary = run_cleaning(_DF_10.copy())
        assert summary["rows_input"]         == 10
        assert summary["rows_output"]        == 4
        assert summary["rows_removed_total"] == 6

    def test_row_count_arithmetic_is_consistent(self, patched_cleaning):
        _, summary = run_cleaning(_DF_10.copy())
        assert summary["rows_removed_total"] == summary["rows_input"] - summary["rows_output"]
        for step in summary["steps"].values():
            assert step["rows_removed"] == step["rows_before"] - step["rows_after"]

    def test_warnings_is_empty_list(self, patched_cleaning):
        _, summary = run_cleaning(_DF_10.copy())
        assert summary["warnings"] == []

    def test_all_stage2_functions_called_in_order(self, monkeypatch):
        call_order: list[str] = []

        def _tracker(name: str):
            def fn(df):
                call_order.append(name)
                return df
            return fn

        for name in (
            "coerce_numerics", "coerce_dates", "fill_nulls", "remove_duplicates",
            "standardize_categoricals", "drop_empty_rows", "validate",
        ):
            monkeypatch.setattr(f"{_MODULE}.{name}", _tracker(name))

        run_cleaning(_DF_10.copy())
        assert call_order == [
            "coerce_numerics", "coerce_dates", "fill_nulls", "remove_duplicates",
            "standardize_categoricals", "drop_empty_rows", "validate",
        ]

    def test_exception_propagates(self, monkeypatch):
        def _raise(df):
            raise RuntimeError("coerce failed")
        monkeypatch.setattr(f"{_MODULE}.coerce_numerics", _raise)
        with pytest.raises(RuntimeError, match="coerce failed"):
            run_cleaning(_DF_10.copy())

    def test_smoke_real_data(self):
        """run_cleaning returns the expected structure on minimal real valid data."""
        df = pd.DataFrame({
            "id_venta":      ["V-001", "V-002"],
            "fecha_venta":   ["2026-01-05", "2026-01-06"],
            "producto":      ["CLT", "Viga"],
            "tipo_madera":   ["Abeto", "Pino"],
            "certificacion": ["FSC", "PEFC"],
            "cliente":       ["ACME", "Beta"],
            "cantidad_m3":   [10.0, 5.0],
            "precio_m3":     [150.0, 200.0],
            "importe":       [1500.0, 1000.0],
            "estado":        ["Cerrado", "Pendiente"],
            "comercial":     ["Ana", "Luis"],
            "pais":          ["España", "España"],
            "source_file":   ["a.xlsx", "b.xlsx"],
        })
        result_df, summary = run_cleaning(df)
        assert isinstance(result_df, pd.DataFrame)
        assert {"rows_input", "rows_output", "rows_removed_total", "steps", "warnings"} <= summary.keys()
        assert set(summary["steps"].keys()) == {
            "type_coercion", "null_handling", "deduplication",
            "standardization", "empty_row_removal", "validation",
        }

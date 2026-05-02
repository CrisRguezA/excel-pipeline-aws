"""Unit tests for stage_2_cleaning.type_coercion.coerce_dates."""

from __future__ import annotations

import pandas as pd
import pytest

from excel_pipeline.stage_2_cleaning.type_coercion import coerce_dates


def _df(fecha_values: list) -> pd.DataFrame:
    return pd.DataFrame({"fecha_venta": fecha_values})


class TestCoerceDateFormats:
    @pytest.mark.parametrize("raw, expected", [
        ("03/02/2024", "2024-02-03"),  # DD/MM/YYYY
        ("02/03/2024", "2024-03-02"),  # DD/MM/YYYY, not MM/DD/YYYY
        ("03-02-2024", "2024-02-03"),  # DD-MM-YYYY
        ("03.02.2024", "2024-02-03"),  # DD.MM.YYYY
        ("2024-02-03", "2024-02-03"),  # YYYY-MM-DD
        ("2024/02/03", "2024-02-03"),  # YYYY/MM/DD
    ])
    def test_known_format_parses_correctly(self, raw: str, expected: str) -> None:
        result = coerce_dates(_df([raw]))
        assert result["fecha_venta"].iloc[0] == pd.Timestamp(expected)

    def test_invalid_string_becomes_nat(self) -> None:
        result = coerce_dates(_df(["not-a-date"]))
        assert pd.isna(result["fecha_venta"].iloc[0])

    def test_null_input_remains_nat(self) -> None:
        result = coerce_dates(_df([None]))
        assert pd.isna(result["fecha_venta"].iloc[0])

    def test_mixed_formats_in_same_column(self) -> None:
        """Matches the real failure pattern seen in source data."""
        result = coerce_dates(_df([
            "03/02/2024",
            "2024-02-06",
            "05.02.2024",
            "2024/01/15",
            "05-02-2024",
        ]))
        expected = [
            pd.Timestamp("2024-02-03"),
            pd.Timestamp("2024-02-06"),
            pd.Timestamp("2024-02-05"),
            pd.Timestamp("2024-01-15"),
            pd.Timestamp("2024-02-05"),
        ]
        for i, exp in enumerate(expected):
            assert result["fecha_venta"].iloc[i] == exp, f"row {i} mismatch"

    def test_null_and_valid_mixed(self) -> None:
        result = coerce_dates(_df([None, "2024-02-03", None]))
        assert pd.isna(result["fecha_venta"].iloc[0])
        assert result["fecha_venta"].iloc[1] == pd.Timestamp("2024-02-03")
        assert pd.isna(result["fecha_venta"].iloc[2])

    def test_input_dataframe_not_mutated(self) -> None:
        df = _df(["2024-02-03"])
        coerce_dates(df)
        assert df["fecha_venta"].iloc[0] == "2024-02-03"

    def test_missing_column_raises(self) -> None:
        with pytest.raises(KeyError):
            coerce_dates(pd.DataFrame({"other": [1]}))

    def test_us_format_parses_as_last_resort(self) -> None:
        """12/31/2024 cannot be DD/MM (month 31 invalid) -- falls through to MM/DD/YYYY."""
        result = coerce_dates(_df(["12/31/2024"]))
        assert result["fecha_venta"].iloc[0] == pd.Timestamp("2024-12-31")

    def test_does_not_drop_rows(self) -> None:
        df = _df(["2024-02-03", "not-a-date", None])
        result = coerce_dates(df)
        assert len(result) == len(df)

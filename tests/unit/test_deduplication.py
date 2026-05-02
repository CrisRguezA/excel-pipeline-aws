"""Unit tests for stage_2_cleaning.deduplication.remove_duplicates."""

from __future__ import annotations

import pandas as pd
import pytest

from excel_pipeline.stage_2_cleaning.deduplication import remove_duplicates

_BASE_COLS = ("id_venta", "fecha_venta", "importe", "cantidad_m3", "precio_m3", "source_file")


def _df(**kwargs) -> pd.DataFrame:
    """Build a minimal DataFrame with all completeness fields defaulting to None."""
    length = len(next(iter(kwargs.values())))
    data = {col: [None] * length for col in _BASE_COLS}
    data.update(kwargs)
    return pd.DataFrame(data)


class TestRemoveDuplicates:
    def test_poorer_first_row_loses_to_more_complete_later_row(self) -> None:
        """First row has null fecha_venta; later row has it -- later row must be kept."""
        df = _df(
            id_venta    =["V1",             "V1"],
            fecha_venta =[None,              pd.Timestamp("2024-02-03")],
            importe     =[1000.0,            1000.0],
            source_file =["source_01.xlsx",  "source_05.xlsx"],
        )
        result = remove_duplicates(df)
        assert len(result) == 1
        assert result["source_file"].iloc[0] == "source_05.xlsx"
        assert pd.notna(result["fecha_venta"].iloc[0])

    def test_more_complete_first_row_is_kept(self) -> None:
        """First row has all priority fields; later row is poorer -- first row must be kept."""
        df = _df(
            id_venta    =["V2",             "V2"],
            fecha_venta =[pd.Timestamp("2024-02-03"), None],
            importe     =[1000.0,            1000.0],
            source_file =["source_01.xlsx",  "source_05.xlsx"],
        )
        result = remove_duplicates(df)
        assert len(result) == 1
        assert result["source_file"].iloc[0] == "source_01.xlsx"
        assert pd.notna(result["fecha_venta"].iloc[0])

    def test_tie_in_completeness_keeps_first_occurrence(self) -> None:
        """Equal completeness score -- earliest row (first occurrence) must be kept."""
        df = _df(
            id_venta    =["V3",             "V3"],
            fecha_venta =[None,              None],
            importe     =[1000.0,            2000.0],
            source_file =["source_01.xlsx",  "source_05.xlsx"],
        )
        result = remove_duplicates(df)
        assert len(result) == 1
        assert result["source_file"].iloc[0] == "source_01.xlsx"

    def test_null_id_venta_rows_are_all_preserved(self) -> None:
        """Null id_venta rows must never be deduplicated."""
        df = _df(
            id_venta    =[None,   None,   "V4"],
            importe     =[1000.0, 2000.0, 500.0],
            source_file =["s1",   "s2",   "s3"],
        )
        result = remove_duplicates(df)
        assert len(result) == 3
        assert int(result["id_venta"].isna().sum()) == 2

    def test_row_count_removed_is_correct(self) -> None:
        """Three copies of V5, two of V6, one null -- result must be 3 rows."""
        df = _df(
            id_venta =["V5",   "V5",   "V5",   "V6",   "V6",   None],
            importe  =[10.0,   20.0,   30.0,   40.0,   50.0,   60.0],
        )
        result = remove_duplicates(df)
        assert len(result) == 3
        assert int(result["id_venta"].isna().sum()) == 1

    def test_output_preserves_original_row_order(self) -> None:
        """Kept rows must appear in their original relative order, not sorted by id_venta."""
        df = _df(
            id_venta    =["V2",   "V1",                       "V2",                       "V1"],
            fecha_venta =[None,   pd.Timestamp("2024-02-01"), pd.Timestamp("2024-02-03"), None],
            importe     =[1000.0, 1000.0,                     1000.0,                     1000.0],
            source_file =["s_a",  "s_b",                      "s_c",                      "s_d"],
        )
        # V2: row 0 (score 2, no fecha) vs row 2 (score 3, fecha present) -> row 2 wins
        # V1: row 1 (score 3, fecha present) vs row 3 (score 2, no fecha) -> row 1 wins
        # kept originals: row 1 (V1) then row 2 (V2) -> output order must be [V1, V2], not [V2, V1]
        result = remove_duplicates(df)
        assert len(result) == 2
        assert result["id_venta"].tolist()    == ["V1", "V2"]
        assert result["source_file"].tolist() == ["s_b", "s_c"]

    def test_empty_string_id_venta_rows_are_all_preserved(self) -> None:
        """Empty string id_venta must never be deduplicated -- treated same as null."""
        df = _df(
            id_venta    =["",      "",      "V4"],
            importe     =[1000.0,  2000.0,  500.0],
            source_file =["s1",    "s2",    "s3"],
        )
        result = remove_duplicates(df)
        assert len(result) == 3
        assert (result["id_venta"] == "").sum() == 2

    def test_empty_string_in_completeness_field_counts_as_absent(self) -> None:
        """Empty string in a completeness field must not increase the completeness score."""
        df = _df(
            id_venta    =["V6",    "V6"],
            fecha_venta =["",      pd.Timestamp("2024-02-03")],
            importe     =[1000.0,  1000.0],
            source_file =["s1",    "s2"],
        )
        result = remove_duplicates(df)
        assert len(result) == 1
        # s1 has empty string for fecha_venta (absent); s2 has real value -> s2 wins
        assert result["source_file"].iloc[0] == "s2"

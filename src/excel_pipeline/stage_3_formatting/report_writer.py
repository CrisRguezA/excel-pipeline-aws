"""Excel report generation for Stage 3 — writes Weekly_Report and Report_Info sheets."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from .formats import get_formats
from .template_rules import row_bg, cert_bg

logger = logging.getLogger(__name__)

_STAGE = "stage3"

# ── style constants ──────────────────────────────────────────────────────────
_TOTALS_BG       = "#1F4E79"
_TOTALS_FONT     = "#FFFFFF"


_REQUIRED_COLUMNS = [
    "id_venta", "cliente", "fecha_venta", "producto", "tipo_madera",
    "certificacion", "cantidad_m3", "precio_m3", "importe", "estado",
    "comercial", "pais",
]

_COL_TYPE: dict[str, tuple[str | None, str]] = {
    "id_venta":      (None,         "center"),
    "cliente":       (None,         "left"),
    "fecha_venta":   ("DD/MM/YYYY", "center"),
    "producto":      (None,         "left"),
    "tipo_madera":   (None,         "left"),
    "certificacion": (None,         "left"),
    "cantidad_m3":   ("#,##0.00",   "center"),
    "precio_m3":     ("#,##0.00 €", "center"),
    "importe":       ("#,##0.00 €", "center"),
    "estado":        (None,         "center"),
    "comercial":     (None,         "left"),
    "pais":          (None,         "left"),
}

_FIXED_WIDTHS: dict[str, int] = {
    "fecha_venta": 14,
    "cliente":     28,
    "producto":    18,
    "comercial":   14,
    "importe":     16,
}


def write_report(df: pd.DataFrame, output_path: Path) -> Path:
    """Write df to a timestamped Excel report under output_path; return the generated file path."""
    _check_dataframe(df)
    _check_required_columns(df)

    if len(df) == 0:
        logger.warning("[%s] DataFrame is empty — report will have no data rows", _STAGE)

    source_ref = _get_source_ref(df)
    df = df[_REQUIRED_COLUMNS].copy()

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = output_path / f"weekly_sales_report_{timestamp}.xlsx"

    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        workbook = writer.book
        fmts = get_formats(workbook)
        _write_report_sheet(workbook, df, fmts)
        _write_info_sheet(workbook, df, source_ref, fmts)

    logger.info(
        "[%s] Report written — %s — %d rows exported",
        _STAGE, file_path.name, len(df),
    )
    return file_path


# ── private: orchestration ────────────────────────────────────────────────────

def _write_report_sheet(workbook, df: pd.DataFrame, fmts: dict) -> None:
    ws = workbook.add_worksheet("Weekly_Report")
    n_cols = len(df.columns)
    n_rows = len(df)

    _write_title(ws, fmts, n_cols)
    _write_header(ws, fmts, df)
    _write_data_rows(ws, df, fmts)
    _write_totals_row(ws, fmts, df)
    _autofit_columns(ws, df)

    ws.freeze_panes(2, 0)
    ws.autofilter(1, 0, n_rows + 1, n_cols - 1)


def _write_info_sheet(workbook, df: pd.DataFrame, source_ref: str, fmts: dict) -> None:
    ws = workbook.add_worksheet("Report_Info")

    label_fmt = fmts["metadata_label"]
    value_fmt = fmts["metadata_value"]

    n_rows         = len(df)
    n_cerradas     = int((df["estado"] == "Cerrado").sum())
    n_certificadas = int((df["certificacion"] != "Sin certificación").sum())

    meta = [
        ("Proyecto",            "excel-pipeline-aws"),
        ("Archivo fuente",      source_ref),
        ("Fecha generación",    datetime.now().strftime("%d/%m/%Y %H:%M")),
        ("Total filas",         n_rows),
        ("Ventas cerradas",     n_cerradas),
        ("Ventas certificadas", n_certificadas),
        ("Columnas",            len(df.columns)),
        ("Pipeline",            "excel-data-cleaner → excel-report-formatter"),
    ]

    ws.set_column(0, 0, 25)
    ws.set_column(1, 1, 50)

    for row_idx, (label, value) in enumerate(meta):
        ws.write(row_idx, 0, label, label_fmt)
        ws.write(row_idx, 1, value, value_fmt)
        ws.set_row(row_idx, 20)

    ws.hide_gridlines(2)


# ── private: sheet sections ───────────────────────────────────────────────────

def _write_title(ws, fmts: dict, n_cols: int) -> None:
    title_fmt = fmts["title"]
    fecha = datetime.now().strftime("%d/%m/%Y")
    ws.merge_range(0, 0, 0, n_cols - 1, f"Reporte Semanal de Ventas — Generado: {fecha}", title_fmt)
    ws.set_row(0, 24)


def _write_header(ws, fmts: dict, df: pd.DataFrame) -> None:
    header_fmt = fmts["header"]
    for col_idx, col_name in enumerate(df.columns):
        ws.write(1, col_idx, col_name, header_fmt)
    ws.set_row(1, 22)


def _write_data_rows(ws, df: pd.DataFrame, fmts: dict) -> None:
    col_names = list(df.columns)
    for row_idx, (_, row) in enumerate(df.iterrows()):
        estado = str(row.get("estado", ""))
        cert   = str(row.get("certificacion", ""))
        row_bg_color = row_bg(estado, row_idx)
        excel_row = row_idx + 2

        for col_idx, col_name in enumerate(col_names):
            value = row[col_name]
            try:
                if pd.isna(value):
                    value = None
            except (TypeError, ValueError):
                pass

            num_fmt, align = _COL_TYPE.get(col_name, (None, "left"))
            bg = cert_bg(cert) if col_name == "certificacion" else row_bg_color
            cell_fmt = fmts["cell"](bg_color=bg, num_format=num_fmt, align=align)

            if value is None:
                ws.write_blank(excel_row, col_idx, None, cell_fmt)
            elif col_name == "id_venta":
                ws.write_string(excel_row, col_idx, str(value), cell_fmt)
            else:
                ws.write(excel_row, col_idx, value, cell_fmt)


def _write_totals_row(ws, fmts: dict, df: pd.DataFrame) -> None:
    n_rows    = len(df)
    n_cols    = len(df.columns)
    tot_row   = n_rows + 2
    col_names = list(df.columns)

    center_fmt = fmts["total_row"]
    euro_fmt = fmts["cell"](
        bg_color=_TOTALS_BG,
        num_format="#,##0.00 €",
        align="center",
        bold=True,
        font_color=_TOTALS_FONT,
    )
    m3_fmt = fmts["cell"](
        bg_color=_TOTALS_BG,
        num_format="#,##0.00",
        align="center",
        bold=True,
        font_color=_TOTALS_FONT,
    )

    importe_idx  = col_names.index("importe")
    cantidad_idx = col_names.index("cantidad_m3")

    ws.write(tot_row, importe_idx, df["importe"].sum(), euro_fmt)
    ws.write(tot_row, cantidad_idx, df["cantidad_m3"].sum(), m3_fmt)

    filled = {importe_idx, cantidad_idx}
    for col_idx in range(n_cols):
        if col_idx not in filled:
            ws.write_blank(tot_row, col_idx, None, center_fmt)

    ws.set_row(tot_row, 20)


def _autofit_columns(ws, df: pd.DataFrame) -> None:
    for col_idx, col_name in enumerate(df.columns):
        if col_name in _FIXED_WIDTHS:
            width = _FIXED_WIDTHS[col_name]
        else:
            lengths = df[col_name].dropna().astype(str).map(len)
            max_value_len = int(lengths.max()) if not lengths.empty else 0
            width = min(max(max_value_len, len(col_name)) + 2, 40)

        ws.set_column(col_idx, col_idx, width)


# ── private: guards ───────────────────────────────────────────────────────────

def _check_dataframe(df: pd.DataFrame) -> None:
    if not isinstance(df, pd.DataFrame):
        logger.error("[%s] Input must be a pandas DataFrame, got %s", _STAGE, type(df).__name__)
        raise TypeError(f"[{_STAGE}] Input must be a pandas DataFrame, got {type(df).__name__}")


def _check_required_columns(df: pd.DataFrame) -> None:
    missing = [col for col in _REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        logger.error("[%s] Missing required columns: %s", _STAGE, missing)
        raise KeyError(f"[{_STAGE}] Missing required columns: {missing}")


def _get_source_ref(df: pd.DataFrame) -> str:
    if "source_file" in df.columns:
        sources = df["source_file"].dropna().astype(str).unique()
        return ", ".join(sorted(sources))
    return "N/A"

"""Named xlsxwriter format definitions for Stage 3 — weekly sales report."""

from __future__ import annotations


_BASE: dict = {
    "font_name": "Arial",
    "font_size": 10,
    "border": 1,
    "valign": "vcenter",
}


def get_formats(workbook) -> dict:
    """Build and return all named xlsxwriter format objects for the weekly sales report.

    The "cell" key is a cached factory callable:
        formats["cell"](bg_color, num_format, align, bold, font_color)
    Repeated calls with identical arguments return the same Format object.
    """
    cache: dict = {}

    def cell(
        bg_color: str = "#FFFFFF",
        num_format: str | None = None,
        align: str = "left",
        bold: bool = False,
        font_color: str | None = None,
    ):
        key = (bg_color, num_format, align, bold, font_color)
        if key not in cache:
            props: dict = {**_BASE, "bg_color": bg_color, "align": align}
            if num_format:
                props["num_format"] = num_format
            if bold:
                props["bold"] = True
            if font_color:
                props["font_color"] = font_color
            cache[key] = workbook.add_format(props)
        return cache[key]

    return {
        "title":          _title(workbook),
        "header":         _header(workbook),
        "metadata_label": _metadata_label(workbook),
        "metadata_value": _metadata_value(workbook),
        "total_row":      cell(bg_color="#1F4E79", align="center", bold=True, font_color="#FFFFFF"),
        "cell":           cell,
    }


# ── private format helpers ────────────────────────────────────────────────────

def _title(workbook):
    return workbook.add_format({
        "font_name": "Arial", "font_size": 13, "bold": True,
        "bg_color": "#D6E4F0", "font_color": "#1F4E79",
        "align": "left", "valign": "vcenter",
    })

def _header(workbook):
    return workbook.add_format({
        **_BASE, "font_size": 11, "bold": True,
        "bg_color": "#1F4E79", "font_color": "#FFFFFF",
        "align": "center",
    })

def _metadata_label(workbook):
    return workbook.add_format({
        "font_name": "Arial", "font_size": 10, "bold": True,
        "border": 1, "bg_color": "#D6E4F0", "align": "left",
    })

def _metadata_value(workbook):
    return workbook.add_format({
        "font_name": "Arial", "font_size": 10,
        "border": 1, "bg_color": "#EBF3FB", "align": "left",
    })

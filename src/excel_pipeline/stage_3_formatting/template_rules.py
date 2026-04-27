"""Background color rules for the weekly sales report.

Pure mapping logic — no xlsxwriter, no pandas, no side effects.
"""

from __future__ import annotations

_ALT_BG          = "#EBF3FB"
_COLOR_CERRADO   = "#C6EFCE"
_COLOR_PENDIENTE = "#FFEB9C"
_COLOR_CANCELADO = "#FFC7CE"

_COLOR_FSC       = "#E2EFDA"
_COLOR_PEFC      = "#BDD7EE"
_COLOR_CE        = "#FFF2CC"
_COLOR_SIN_CERT  = "#F2F2F2"


def row_bg(estado: str, row_idx: int) -> str:
    return {
        "Cerrado":   _COLOR_CERRADO,
        "Pendiente": _COLOR_PENDIENTE,
        "Cancelado": _COLOR_CANCELADO,
    }.get(estado, _ALT_BG if row_idx % 2 == 0 else "#FFFFFF")


def cert_bg(certificacion: str) -> str:
    return {
        "FSC":               _COLOR_FSC,
        "PEFC":              _COLOR_PEFC,
        "CE":                _COLOR_CE,
        "Sin certificación": _COLOR_SIN_CERT,
    }.get(certificacion, "#FFFFFF")

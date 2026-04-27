import pytest
from excel_pipeline.stage_3_formatting.template_rules import cert_bg, row_bg


class TestRowBg:
    def test_cerrado(self):
        assert row_bg("Cerrado", 0) == "#C6EFCE"

    def test_pendiente(self):
        assert row_bg("Pendiente", 0) == "#FFEB9C"

    def test_cancelado(self):
        assert row_bg("Cancelado", 0) == "#FFC7CE"

    def test_unknown_even_row(self):
        assert row_bg("desconocido", 0) == "#EBF3FB"

    def test_unknown_odd_row(self):
        assert row_bg("desconocido", 1) == "#FFFFFF"


class TestCertBg:
    def test_fsc(self):
        assert cert_bg("FSC") == "#E2EFDA"

    def test_pefc(self):
        assert cert_bg("PEFC") == "#BDD7EE"

    def test_ce(self):
        assert cert_bg("CE") == "#FFF2CC"

    def test_sin_certificacion(self):
        assert cert_bg("Sin certificación") == "#F2F2F2"

    def test_unknown(self):
        assert cert_bg("desconocido") == "#FFFFFF"

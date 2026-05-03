"""Unit tests for renderers.py with mocked Streamlit.

Covers all branch cases: missing data, empty lists, None values, edge cases.
"""

from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture
def mock_st():
    """Mock streamlit module used in renderers."""
    with patch("src.renderers.st") as mock:
        mock.subheader = MagicMock()
        mock.markdown = MagicMock()
        mock.dataframe = MagicMock()
        mock.metric = MagicMock()
        mock.write = MagicMock()
        mock.container = MagicMock()
        mock.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
        mock.altair_chart = MagicMock()
        mock.expander = MagicMock()
        mock.json = MagicMock()
        mock.text = MagicMock()
        yield mock


@pytest.fixture
def sample_producto():
    """Sample product with all fields populated."""
    return {
        "codigoIsin": "IE00B4L5Y983",
        "nombre": "Vanguard LifeStrategy 80% Equity Fund",
        "tipoActivo": "Renta Variable",
        "categoria": "Mixto",
        "categoriaMyInvestor": "Mixto",
        "categoriaMstar": "Mixto",
        "zonaGeografica": "Global",
        "divisasDto": {"codigo": "EUR"},
        "tipoProductoEnum": "FONDOS_INDEXADOS",
        "datosFondo": {
            "indicadorRiesgo": 5,
            "entidadGestora": "Vanguard",
            "entidadDepositaria": "Bank",
            "tipoPerfilPlanEnum": "Arriesgado",
            "urlFichaTecnica": "http://example.com/ficha",
            "urlDatosFundamentales": "http://example.com/datos",
        },
        "descripcion": "A balanced fund.",
        "ter": "0.25",
        "listaComisiones": [
            {"nombre": "Comisión de gestión", "porcentaje": "0.20"},
            {"nombre": "Comisión de depósito", "porcentaje": "0.05"},
        ],
        "listaRegiones": [
            {"nombre": "Norteamérica", "porcent": "40.0"},
            {"nombre": "Europa", "porcent": "30.0"},
        ],
        "listaSectores": [
            {"nombre": "Tecnología", "porcent": "25.0"},
            {"nombre": "Salud", "porcent": "15.0"},
        ],
        "listaComposiciones": [
            {
                "codigoIsin": "US123",
                "nombreFondo": "Apple",
                "categoria": "Tech",
                "porcentaje": "5.0",
            },
        ],
        "urlFichaTecnica": "http://example.com/ficha",
        "urlKiid": "http://example.com/kiid",
        "secIdFondoMorningstar": "12345",
        "ytd": "10.5",
        "yearUno": "8.5",
        "yearTres": "25.0",
        "yearCinco": "45.0",
        "volatilidadYearUno": "12.0",
        "volatilidadYearTres": "15.0",
        "volatilidadYearCinco": "18.0",
    }


class TestHelpers:
    def test_to_float_with_percent(self):
        from src.renderers import to_float

        assert to_float("12.5%") == 12.5

    def test_to_float_without_percent(self):
        from src.renderers import to_float

        assert to_float("12.5") == 12.5

    def test_to_float_invalid(self):
        from src.renderers import to_float

        assert to_float("invalid") == 0.0

    def test_to_float_none(self):
        from src.renderers import to_float

        assert to_float(None) == 0.0

    def test_format_text_with_value(self):
        from src.renderers import format_text

        assert format_text("hello") == "hello"

    def test_format_text_none(self):
        from src.renderers import format_text

        assert format_text(None) == "N/D"

    def test_format_text_empty(self):
        from src.renderers import format_text

        assert format_text("") == "N/D"

    def test_has_value_true(self):
        from src.renderers import has_value

        assert has_value("hello") is True

    def test_has_value_false_none(self):
        from src.renderers import has_value

        assert has_value(None) is False

    def test_has_value_false_empty(self):
        from src.renderers import has_value

        assert has_value("") is False

    def test_has_value_false_dot(self):
        from src.renderers import has_value

        assert has_value(".") is False

    def test_format_percent_from_decimal(self):
        from src.renderers import format_percent_from_decimal

        assert format_percent_from_decimal(0.1234) == "12.34%"


class TestRenderComisiones:
    def test_no_producto(self, mock_st):
        from src.renderers import render_comisiones

        render_comisiones(None)
        mock_st.markdown.assert_called_once_with(
            "No hay información de comisiones disponible."
        )

    def test_no_lista_comisiones(self, mock_st):
        from src.renderers import render_comisiones

        render_comisiones({})
        mock_st.markdown.assert_called_once_with(
            "No hay información de comisiones disponible."
        )

    def test_with_comisiones_and_ter(self, mock_st, sample_producto):
        from src.renderers import render_comisiones

        render_comisiones(sample_producto)
        # Should render subheader + markdown table
        mock_st.subheader.assert_called_once_with("Comisiones")
        assert mock_st.markdown.called

    def test_with_ter_no_urlKiid(self, mock_st):
        from src.renderers import render_comisiones

        producto = {"listaComisiones": [], "ter": "0.25"}
        render_comisiones(producto)
        # Should render table with TER but no KIID link
        assert mock_st.markdown.called
        # Check KIID link not called
        kiid_calls = [c for c in mock_st.markdown.call_args_list if "KIID" in str(c)]
        assert len(kiid_calls) == 0

    def test_with_urlKiid(self, mock_st, sample_producto):
        from src.renderers import render_comisiones

        render_comisiones(sample_producto)
        # Should render KIID link
        kiid_calls = [
            c
            for c in mock_st.markdown.call_args_list
            if "KIID" in str(c) or "kiid" in str(c)
        ]
        assert len(kiid_calls) > 0


class TestRenderRegiones:
    def test_no_producto(self, mock_st):
        from src.renderers import render_regiones

        render_regiones(None)
        mock_st.subheader.assert_not_called()

    def test_no_lista_regiones(self, mock_st):
        from src.renderers import render_regiones

        render_regiones({})
        mock_st.subheader.assert_not_called()

    def test_empty_lista_regiones(self, mock_st):
        from src.renderers import render_regiones

        render_regiones({"listaRegiones": []})
        mock_st.subheader.assert_not_called()

    def test_with_regiones(self, mock_st, sample_producto):
        from src.renderers import render_regiones

        render_regiones(sample_producto)
        mock_st.subheader.assert_called_once_with("Regiones")
        assert mock_st.markdown.called


class TestRenderSectores:
    def test_no_producto(self, mock_st):
        from src.renderers import render_sectores

        render_sectores(None)
        mock_st.subheader.assert_not_called()

    def test_no_lista_sectores(self, mock_st):
        from src.renderers import render_sectores

        render_sectores({})
        mock_st.subheader.assert_not_called()

    def test_empty_lista_sectores(self, mock_st):
        from src.renderers import render_sectores

        render_sectores({"listaSectores": []})
        mock_st.subheader.assert_not_called()

    def test_with_sectores(self, mock_st, sample_producto):
        from src.renderers import render_sectores

        render_sectores(sample_producto)
        mock_st.subheader.assert_called_once_with("Sectores")
        assert mock_st.markdown.called


class TestRenderComposiciones:
    def test_no_producto(self, mock_st):
        from src.renderers import render_composiciones

        render_composiciones(None)
        mock_st.subheader.assert_not_called()

    def test_no_lista_composiciones(self, mock_st):
        from src.renderers import render_composiciones

        render_composiciones({})
        mock_st.subheader.assert_not_called()

    def test_empty_lista_composiciones(self, mock_st):
        from src.renderers import render_composiciones

        render_composiciones({"listaComposiciones": []})
        mock_st.subheader.assert_not_called()

    def test_with_composiciones(self, mock_st, sample_producto):
        from src.renderers import render_composiciones

        render_composiciones(sample_producto)
        mock_st.subheader.assert_called_once_with("Composiciones")
        mock_st.dataframe.assert_called_once()


class TestRenderGeneralInfo:
    def test_basic_info(self, mock_st, sample_producto):
        from src.renderers import render_general_info

        render_general_info(sample_producto)
        mock_st.subheader.assert_called()
        mock_st.metric.assert_called_once()

    def test_no_descripcion(self, mock_st, sample_producto):
        from src.renderers import render_general_info

        sample_producto["descripcion"] = None
        render_general_info(sample_producto)
        mock_st.write.assert_not_called()

    def test_with_descripcion(self, mock_st, sample_producto):
        from src.renderers import render_general_info

        render_general_info(sample_producto)
        mock_st.write.assert_called_once()

    def test_no_links(self, mock_st):
        from src.renderers import render_general_info

        producto = {"nombre": "Test", "codigoIsin": "ISIN123", "tipoActivo": "Tipo"}
        render_general_info(producto)
        # Should not render links section
        link_calls = [c for c in mock_st.markdown.call_args_list if "Links" in str(c)]
        assert len(link_calls) == 0

    def test_with_links(self, mock_st, sample_producto):
        from src.renderers import render_general_info

        render_general_info(sample_producto)
        # Should render links section
        link_calls = [c for c in mock_st.markdown.call_args_list if "Links" in str(c)]
        assert len(link_calls) > 0


class TestRenderGeneralInfoTabla:
    def test_basic(self, mock_st, sample_producto):
        from src.renderers import render_general_info_tabla

        render_general_info_tabla(sample_producto)
        mock_st.subheader.assert_called_once_with("Datos generales")
        assert mock_st.markdown.called

    def test_all_none(self, mock_st):
        from src.renderers import render_general_info_tabla

        producto = {}
        render_general_info_tabla(producto)
        mock_st.subheader.assert_called_once()
        # Should still render table (possibly empty rows filtered)
        assert mock_st.markdown.called


class TestRenderRentabilidad:
    def test_no_data(self, mock_st):
        from src.renderers import render_rentabilidad

        producto = {}
        render_rentabilidad(producto, 2026)
        # Should still render disclaimer
        assert mock_st.markdown.called

    def test_with_data(self, mock_st, sample_producto):
        from src.renderers import render_rentabilidad

        render_rentabilidad(sample_producto, 2026)
        mock_st.columns.assert_called_once()
        assert mock_st.markdown.called

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
        mock.warning = MagicMock()
        mock.error = MagicMock()
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
            {"nombre": "Comision de gestion", "porcentaje": "0.20"},
            {"nombre": "Comision de deposito", "porcentaje": "0.05"},
        ],
        "listaRegiones": [
            {"nombre": "Norteamerica", "porcent": "40.0"},
            {"nombre": "Europa", "porcent": "30.0"},
        ],
        "listaSectores": [
            {"nombre": "Tecnologia", "porcent": "25.0"},
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
        "valorLiquidativo": 12.6231,
        "fechaValorLiquidativo": "2026-04-22T00:00:00Z",
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
        mock_st.subheader.assert_called_once_with("Comisiones")
        assert mock_st.markdown.called

    def test_with_ter_no_urlKiid(self, mock_st):
        from src.renderers import render_comisiones

        producto = {"listaComisiones": [], "ter": "0.25"}
        render_comisiones(producto)
        assert mock_st.markdown.called

    def test_with_urlKiid(self, mock_st, sample_producto):
        from src.renderers import render_comisiones

        render_comisiones(sample_producto)
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
        assert mock_st.metric.call_count == 2
        metric_labels = [call.args[0] for call in mock_st.metric.call_args_list]
        assert any("Valor Liquidativo" in label for label in metric_labels)
        assert "Indicador de riesgo" in metric_labels
        # Check value contains formatted price
        vl_call = [
            c for c in mock_st.metric.call_args_list if "Valor Liquidativo" in c.args[0]
        ][0]
        assert "12.623" in str(vl_call.args[1])
        assert "€" in str(vl_call.args[1])
        # Check label contains formatted date
        vl_label = [label for label in metric_labels if "Valor Liquidativo" in label][0]
        assert "22/04" in vl_label

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
        link_calls = [c for c in mock_st.markdown.call_args_list if "Links" in str(c)]
        assert len(link_calls) == 0

    def test_with_links(self, mock_st, sample_producto):
        from src.renderers import render_general_info

        render_general_info(sample_producto)
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
        assert mock_st.markdown.called


class TestRenderRentabilidad:
    def test_no_data(self, mock_st):
        from src.renderers import render_rentabilidad

        producto = {}
        render_rentabilidad(producto, 2026)
        assert mock_st.markdown.called

    def test_with_data(self, mock_st, sample_producto):
        from src.renderers import render_rentabilidad

        render_rentabilidad(sample_producto, 2026)
        mock_st.columns.assert_called_once()
        assert mock_st.markdown.called


class TestRenderMixMetrics:
    def test_empty_portfolio(self, mock_st):
        from src.renderers import render_mix_metrics

        render_mix_metrics({}, 5)
        mock_st.columns.assert_not_called()

    def test_none_portfolio(self, mock_st):
        from src.renderers import render_mix_metrics

        render_mix_metrics(None, 5)
        mock_st.columns.assert_not_called()

    def test_valid_portfolio(self, mock_st):
        from src.renderers import render_mix_metrics

        portfolio = {
            "net_expected": 0.085,
            "ter_drag": 0.0025,
            "volatility_proxy": 0.12,
        }
        cols = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_st.columns.return_value = cols
        render_mix_metrics(portfolio, 5)
        mock_st.columns.assert_called_once_with(4)
        for col in cols:
            assert col.metric.called

    def test_missing_keys(self, mock_st):
        from src.renderers import render_mix_metrics

        # Non-empty dict with missing keys (still renders with defaults)
        portfolio = {"net_expected": None, "ter_drag": None, "volatility_proxy": None}
        cols = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_st.columns.return_value = cols
        render_mix_metrics(portfolio, 5)
        # Should render with defaults (None becomes 0.0 via format_percent_from_decimal)
        mock_st.columns.assert_called_once_with(4)
        for i in range(4):
            assert cols[i].metric.called


class TestRenderMixAllocations:
    def test_empty_list(self, mock_st):
        from src.renderers import render_mix_allocations

        render_mix_allocations([])
        mock_st.subheader.assert_not_called()

    def test_none(self, mock_st):
        from src.renderers import render_mix_allocations

        render_mix_allocations(None)
        mock_st.subheader.assert_not_called()

    def test_valid_allocations(self, mock_st):
        from src.renderers import render_mix_allocations

        allocations = [
            {
                "isin": "IE00B4L5Y983",
                "nombre": "Fund A",
                "weight": 0.5,
                "expected_return": 0.08,
                "ter": 0.002,
                "volatility": 0.12,
                "raw_score": 0.85,
            },
            {
                "isin": "LU123",
                "nombre": "Fund B",
                "weight": 0.5,
                "expected_return": 0.06,
                "ter": 0.003,
                "volatility": 0.10,
                "raw_score": 0.75,
            },
        ]
        render_mix_allocations(allocations)
        mock_st.subheader.assert_called_once_with("Asignación recomendada")
        mock_st.dataframe.assert_called_once()


class TestRenderMixExplanation:
    def test_empty_string(self, mock_st):
        from src.renderers import render_mix_explanation

        render_mix_explanation("")
        mock_st.subheader.assert_not_called()

    def test_none(self, mock_st):
        from src.renderers import render_mix_explanation

        render_mix_explanation(None)
        mock_st.subheader.assert_not_called()

    def test_valid_markdown(self, mock_st):
        from src.renderers import render_mix_explanation

        md = "## Recomendacion\n- Reason 1\n- Reason 2"
        render_mix_explanation(md)
        mock_st.subheader.assert_called_once_with("Explicación de recomendación")
        mock_st.markdown.assert_called_once_with(md)


class TestRenderMixSimulation:
    def test_empty_simulation(self, mock_st):
        from src.renderers import render_mix_simulation

        render_mix_simulation({})
        mock_st.subheader.assert_not_called()

    def test_none(self, mock_st):
        from src.renderers import render_mix_simulation

        render_mix_simulation(None)
        mock_st.subheader.assert_not_called()

    def test_valid_simulation_with_paths(self, mock_st):
        from src.renderers import render_mix_simulation

        simulation = {
            "paths": [
                {
                    "year": 1,
                    "cumulative_return": 0.08,
                    "annual_return": 0.08,
                    "scenario": "base",
                },
                {
                    "year": 2,
                    "cumulative_return": 0.16,
                    "annual_return": 0.07,
                    "scenario": "base",
                },
            ],
            "historical_proxy": [],
        }
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        render_mix_simulation(simulation)
        mock_st.subheader.assert_called_with("Simulación de escenarios")
        mock_st.altair_chart.assert_called()

    def test_valid_simulation_with_historical(self, mock_st):
        from src.renderers import render_mix_simulation

        simulation = {
            "paths": [],
            "historical_proxy": [
                {
                    "year_index": 1,
                    "cumulative_return": 0.08,
                    "annual_return": 0.08,
                    "coverage_weight": 1.0,
                },
            ],
        }
        render_mix_simulation(simulation)
        assert mock_st.altair_chart.call_count >= 1

    def test_no_paths_no_historical(self, mock_st):
        from src.renderers import render_mix_simulation

        simulation = {"paths": [], "historical_proxy": []}
        render_mix_simulation(simulation)
        mock_st.subheader.assert_not_called()


class TestRenderMixExcluded:
    def test_empty_list(self, mock_st):
        from src.renderers import render_mix_excluded

        render_mix_excluded([])
        mock_st.warning.assert_not_called()

    def test_none(self, mock_st):
        from src.renderers import render_mix_excluded

        render_mix_excluded(None)
        mock_st.warning.assert_not_called()

    def test_with_excluded(self, mock_st):
        from src.renderers import render_mix_excluded

        excluded = [{"isin": "IE123", "reason": "Missing data"}]
        render_mix_excluded(excluded)
        mock_st.warning.assert_called_once()
        mock_st.dataframe.assert_called_once()


class TestRenderMixRecommendation:
    def test_error_status(self, mock_st):
        from src.renderers import render_mix_recommendation

        recommendation = {"status": "error", "message": "Something went wrong"}
        render_mix_recommendation(recommendation, {}, "")
        mock_st.error.assert_called_once()

    def test_valid_recommendation(self, mock_st):
        from src.renderers import render_mix_recommendation

        recommendation = {
            "status": "success",
            "portfolio": {
                "net_expected": 0.08,
                "ter_drag": 0.002,
                "volatility_proxy": 0.12,
            },
            "horizon_bucket": 5,
            "allocations": [
                {
                    "isin": "IE00B4L5Y983",
                    "nombre": "Fund A",
                    "weight": 1.0,
                    "expected_return": 0.08,
                    "ter": 0.002,
                    "volatility": 0.12,
                    "raw_score": 0.85,
                }
            ],
            "excluded": [],
        }
        simulation = {"paths": [], "historical_proxy": []}
        explanation_md = "Test explanation"
        cols = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_st.columns.return_value = cols
        render_mix_recommendation(recommendation, simulation, explanation_md)
        for col in cols:
            assert col.metric.called
        assert mock_st.dataframe.call_count >= 1
        mock_st.markdown.assert_called()

    def test_with_excluded_products(self, mock_st):
        from src.renderers import render_mix_recommendation

        recommendation = {
            "status": "success",
            "portfolio": {
                "net_expected": 0.08,
                "ter_drag": 0.002,
                "volatility_proxy": 0.12,
            },
            "horizon_bucket": 5,
            "allocations": [],
            "excluded": [{"isin": "IE123", "reason": "Missing data"}],
        }
        simulation = {}
        cols = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_st.columns.return_value = cols
        render_mix_recommendation(recommendation, simulation, "")
        mock_st.warning.assert_called_once()

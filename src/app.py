import streamlit as st
import duckdb
import pandas as pd
from dotenv import load_dotenv
from datetime import date

from vars import CACHE_TTL, LOCAL_FILE_TIMESTAMP

from productos import (
    get_productos,
    get_df_productos,
    get_listas_opciones,
)
from recommendador import recommend_mix, RecommendationError
from simulacion import build_simulation
from explicabilidad import build_recommendation_explanation
from queries import (
    build_product_query,
    FilterState,
)
from renderers import (
    render_comisiones,
    render_regiones,
    render_composiciones,
    render_sectores,
    render_general_info,
    render_general_info_tabla,
    render_rentabilidad,
    format_percent_from_decimal,
)

load_dotenv()


st.set_page_config(
    page_title="Investor", layout="wide", page_icon=":material/finance_mode:"
)

if "threshold_sector" not in st.session_state:
    st.session_state.threshold_sector = 20


FILTROS_RAPIDOS = {
    "Cualquiera": "1=1",
    # "Lage Cap" is NOT a typo — matches the raw API category value. Won't fix.
    "World": "categoria = 'Global Equity Large Cap' or categoria = 'Global Equity Lage Cap' or  categoriaMstar = 'RV Global Cap. Grande Blend'",
    "S&P 500": "categoria = 'US Equity Large Cap Blend' or categoriaMstar = 'RV USA Cap. Grande Blend'",
    "Emergentes": "zonaGeografica = 'Mercados Emergentes' OR categoria = 'Global Emerging Markets Equity' or categoriaMstar = 'RV Global Emergente'",
    "Japón": "categoria = 'Japan Equity' or categoriaMstar = 'RV Japón Cap. Grande'",
    "Small Caps": "categoria = 'Global Equity Mid/Small Cap' or categoriaMstar = 'RV Global Cap. Pequeña'",
    "Oro y Metales": "categoriaMstar = 'RV Sector Oro y Metales preciosos' OR categoria = 'Precious Metals Sector Equity'",
}


@st.cache_resource
def init_app_data():
    timestamp_products, productos_lista = get_productos()
    df_productos = get_df_productos(productos_lista)
    options = get_listas_opciones(df_productos, timestamp_products)
    return {
        "timestamp_products": timestamp_products,
        "productos_lista": productos_lista,
        "df_productos": df_productos,
        "options": options,
    }


data = init_app_data()
timestamp_products = data["timestamp_products"]
productos_lista = data["productos_lista"]
df_productos = data["df_productos"]
(
    DIVISAS,
    ZONAS,
    TIPOS_PRODUCTO,
    CATEGORIAS,
    CATEGORIAS_MYINVESTOR,
    CATEGORIAS_MSTAR,
    GESTORAS,
    SECTORES,
    TIPO_ACTIVO,
) = data["options"]

year = date.today().year

# Initialize FilterState early, defaults in class
filter_state = FilterState(year=year)

cols = st.columns(2)
cols[0].title("Productos en MyInvestor")
filter_state.filter_name = (
    cols[1]
    .text_input(
        "Filtrar por nombre or por ISIN (SQL ILIKE)",
        value="",
        placeholder="Ejemplo: world, FR0000978371...",
    )
    .strip()
)

cols = st.columns(4)
selected_filter = cols[0].selectbox(
    "Filtro rápido:", options=list(FILTROS_RAPIDOS.keys())
)
filter_state.selected_filter_sql = FILTROS_RAPIDOS[selected_filter]
filter_state.selected_divisa = cols[1].multiselect(
    "Filtro por divisa", options=list(DIVISAS), default=["EUR"]
)
filter_state.selected_producto = cols[2].multiselect(
    "Filtro por tipo de producto",
    options=list(TIPOS_PRODUCTO),
    default=["FONDOS_INDEXADOS"],
)
filter_state.selected_gestora = cols[3].multiselect(
    "Filtro por gestora:", options=list(GESTORAS)
)


@st.cache_data(show_spinner=False)
def run_query(_df_productos, query: str, data_version: str) -> pd.DataFrame:
    return duckdb.query(query).df()


with st.expander("Más filtros & Selección de columnas", expanded=False):
    with st.container():
        cols = st.columns(4)
        filter_state.selected_categoria = cols[0].multiselect(
            "Filtro por categoría", options=list(CATEGORIAS)
        )
        filter_state.selected_tipo_activo = cols[0].multiselect(
            "Filtro por tipo de activo", options=list(TIPO_ACTIVO)
        )
        filter_state.selected_categoria_myinvestor = cols[1].multiselect(
            "Filtro por categoría MyInvestor",
            options=list(CATEGORIAS_MYINVESTOR),
        )
        filter_state.selected_categoria_mstar = cols[2].multiselect(
            "Filtro por categoría Morningstar", options=list(CATEGORIAS_MSTAR)
        )
        filter_state.selected_zona = cols[3].multiselect(
            "Filtro por zona geográfica", options=list(ZONAS)
        )

    with st.container():
        cols = st.columns(4)
        filter_state.show_rentabilidad_anios = cols[0].toggle(
            "Mostrar rentabilidad ultimos 6 años", value=True
        )
        filter_state.show_rentabilidad_media_135 = cols[0].toggle(
            "Mostrar rentabilidad media a 1,3,5 años", value=True
        )
        filter_state.show_categories = cols[1].toggle("Mostrar categorias", value=False)
        filter_state.show_volatilidad = cols[2].toggle(
            "Mostrar datos Volatilidad", value=False
        )
        filter_state.show_dias_desplazamiento = cols[3].toggle(
            "Mostrar días desplazamiento suscripción y reembolso", value=False
        )

    with st.container():
        cols = st.columns([2, 1, 1])
        filter_state.selected_sector = cols[0].multiselect(
            "Filtro por sector (al menos uno debe cumplir el umbral)",
            options=SECTORES,
        )
        filter_state.threshold_sector = cols[1].slider(
            "Umbral mínimo del sector (%)",
            min_value=0,
            max_value=100,
            step=5,
            key="threshold_sector",
            disabled=not filter_state.selected_sector,
        )
        filter_state.show_sectores = cols[2].toggle(
            "Mostrar sector(es) seleccionados",
            value=False,
            disabled=not filter_state.selected_sector,
        )

    query = build_product_query(filter_state)

    with st.expander("Consulta SQL"):
        st.code(query)

df = run_query(df_productos, query, timestamp_products)
if df.empty:
    st.error("No hay productos que correspondan a esos filtros.")
    tabla = {"selection": {"rows": []}}
else:
    tabla = st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        key="productos_table",
        on_select="rerun",
        selection_mode="single-row",
    )

selected_rows = tabla.get("selection", {}).get("rows", [])


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def get_producto_by_isin(_productos, isin, data_version: str):
    return next((p for p in _productos if p["codigoIsin"] == isin), None)


selected_row_index = selected_rows[0] if selected_rows else None
if selected_row_index is not None and 0 <= selected_row_index < len(df):
    selected_isin = df.iloc[selected_row_index]["codigoIsin"]
elif df.shape[0] == 1:
    selected_isin = df.iloc[0]["codigoIsin"]
else:
    selected_isin = None

if selected_isin:
    producto = get_producto_by_isin(productos_lista, selected_isin, timestamp_products)
    if not producto:
        st.warning("No se encontraron los detalles del producto seleccionado.")
    else:
        with st.expander("Información del producto", expanded=True):
            render_general_info(producto)
            render_rentabilidad(producto, year)
            cols = st.columns(2)
            with cols[0]:
                render_general_info_tabla(producto)
            with cols[1]:
                render_comisiones(producto)

            with st.container(horizontal=True):
                with st.container():
                    render_sectores(producto)
                with st.container():
                    render_regiones(producto)

            render_composiciones(producto)

            with st.expander("Detalle completo del producto", expanded=False):
                st.json(producto)
else:
    st.write("Selecciona un producto para ver sus detalles.")

with st.expander("Asesor MIX (beta)", expanded=False):
    if df.empty:
        st.info("No hay productos disponibles para construir mix.")
    else:
        options_map = {
            f"{row['codigoIsin']} - {row['nombre']}": row["codigoIsin"]
            for _, row in df[["codigoIsin", "nombre"]].drop_duplicates().iterrows()
        }

        default_mix_isins = []
        selected_mix_labels = st.multiselect(
            "Selecciona ISIN para el mix",
            options=list(options_map.keys()),
            default=[
                label
                for label, isin in options_map.items()
                if isin in default_mix_isins
            ],
        )
        selected_mix_isins = [options_map[label] for label in selected_mix_labels]

        cols_mix = st.columns(3)
        horizon_years = cols_mix[0].number_input(
            "Horizonte (años)", min_value=1, max_value=30, value=5, step=1
        )
        min_weight_pct = cols_mix[1].slider(
            "Peso mínimo por fondo (%)",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
        )
        risk_aversion = cols_mix[2].slider(
            "Penalización por riesgo",
            min_value=0.0,
            max_value=1.0,
            value=0.35,
            step=0.05,
        )

        import altair as alt

        if selected_mix_isins:
            try:
                recommendation = recommend_mix(
                    productos_lista,
                    selected_mix_isins,
                    int(horizon_years),
                    min_weight=min_weight_pct / 100.0,
                    risk_aversion=float(risk_aversion),
                )

                simulation = build_simulation(recommendation, int(horizon_years))
                explanation_md = build_recommendation_explanation(recommendation)

                portfolio = recommendation["portfolio"]
                metric_cols = st.columns(4)
                metric_cols[0].metric(
                    "Rentabilidad neta esperada",
                    format_percent_from_decimal(portfolio["net_expected"]),
                )
                metric_cols[1].metric(
                    "TER agregado",
                    format_percent_from_decimal(portfolio["ter_drag"]),
                )
                metric_cols[2].metric(
                    "Volatilidad proxy",
                    format_percent_from_decimal(portfolio["volatility_proxy"]),
                )
                metric_cols[3].metric(
                    "Horizonte usado",
                    f"{recommendation['horizon_bucket']}Y",
                )

                st.subheader("Asignación recomendada")
                allocations_df = pd.DataFrame(recommendation["allocations"])
                allocations_view = allocations_df[
                    [
                        "isin",
                        "nombre",
                        "weight",
                        "expected_return",
                        "ter",
                        "volatility",
                        "raw_score",
                    ]
                ].rename(
                    columns={
                        "isin": "ISIN",
                        "nombre": "Nombre",
                        "weight": "Peso",
                        "expected_return": "Rentabilidad esperada",
                        "ter": "TER",
                        "volatility": "Volatilidad",
                        "raw_score": "Score",
                    }
                )
                for col in ["Peso", "Rentabilidad esperada", "TER", "Volatilidad"]:
                    allocations_view[col] = allocations_view[col].map(
                        format_percent_from_decimal
                    )
                st.dataframe(allocations_view, hide_index=True, width="stretch")

                st.subheader("Explicación de recomendación")
                st.markdown(explanation_md)

                st.subheader("Simulación de escenarios")
                sim_paths_df = pd.DataFrame(simulation["paths"])
                if not sim_paths_df.empty:
                    scenario_chart = (
                        alt.Chart(sim_paths_df)
                        .mark_line(point=True)
                        .encode(
                            x=alt.X("year:O", title="Año"),
                            y=alt.Y(
                                "cumulative_return:Q",
                                title="Rentabilidad acumulada",
                                axis=alt.Axis(format=".0%"),
                            ),
                            color=alt.Color("scenario:N", title="Escenario"),
                            tooltip=[
                                "scenario",
                                "year",
                                alt.Tooltip("annual_return:Q", format=".2%"),
                                alt.Tooltip("cumulative_return:Q", format=".2%"),
                            ],
                        )
                    )
                    st.altair_chart(scenario_chart, width="stretch")

                historical_proxy_df = pd.DataFrame(simulation["historical_proxy"])
                if not historical_proxy_df.empty:
                    st.caption("Trayectoria proxy histórica (años disponibles)")
                    historical_chart = (
                        alt.Chart(historical_proxy_df)
                        .mark_line(point=True, color="#1f77b4")
                        .encode(
                            x=alt.X("year_index:O", title="Indice anual histórico"),
                            y=alt.Y(
                                "cumulative_return:Q",
                                title="Rentabilidad acumulada",
                                axis=alt.Axis(format=".0%"),
                            ),
                            tooltip=[
                                "year_index",
                                alt.Tooltip("coverage_weight:Q", format=".0%"),
                                alt.Tooltip("annual_return:Q", format=".2%"),
                                alt.Tooltip("cumulative_return:Q", format=".2%"),
                            ],
                        )
                    )
                    st.altair_chart(historical_chart, width="stretch")

                if recommendation["excluded"]:
                    excluded_df = pd.DataFrame(recommendation["excluded"])
                    st.warning(
                        "Algunos productos fueron excluidos por datos incompletos."
                    )
                    st.dataframe(excluded_df, hide_index=True, width="stretch")

            except RecommendationError as err:
                st.error(f"No se pudo calcular recomendación: {err}")
        else:
            st.info("Selecciona uno o más ISIN para calcular mix recomendado.")

# Disclaimer
st.markdown(
    "<small>:red-badge[:material/warning: Aviso] Rentabilidades pasadas no garantizan rentabilidades futuras. Invertir en fondos conlleva riesgo de pérdida de capital.</small>",
    unsafe_allow_html=True,
)

if timestamp_products == LOCAL_FILE_TIMESTAMP:
    st.markdown(
        f"<small>:orange-badge[:material/warning: Aviso] El listado de productos es una *foto* del {timestamp_products}.</small>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"<small>:green-badge[:material/check: Actualizado] El listado de productos es una *foto actualizada* el {timestamp_products}.</small>",
        unsafe_allow_html=True,
    )

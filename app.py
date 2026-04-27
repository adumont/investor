import streamlit as st
import duckdb
import pandas as pd
import json
import altair as alt
from dotenv import load_dotenv
from os import getenv
import datetime

from vars import CACHE_TTL, LOCAL_FILE_TIMESTAMP

from productos import (
    get_productos,
    get_df_productos,
    get_listas_opciones,
)
from recommendador import recommend_mix, RecommendationError
from simulacion import build_simulation
from explicabilidad import build_recommendation_explanation

load_dotenv()


st.set_page_config(
    page_title="Investor", layout="wide", page_icon=":material/finance_mode:"
)

if "threshold_sector" not in st.session_state:
    st.session_state.threshold_sector = 20


# query = """
#     SELECT
#         codigoIsin,
#         nombre,
#         indicadorRiesgo,
#         unnest(listaSectores).nombre AS sector_nombre,
#         unnest(listaSectores).porcent AS sector_porcentaje
#     FROM df_productos
#     WHERE indicadorRiesgo <= 4
#     ORDER BY indicadorRiesgo ASC, nombre ASC, sector_porcentaje DESC
# """

FILTROS_RAPIDOS = {
    "Cualquiera": "1=1",
    "World": "categoria = 'Global Equity Large Cap' or categoria = 'Global Equity Lage Cap' or  categoriaMstar = 'RV Global Cap. Grande Blend'",
    "S&P 500": "categoria = 'US Equity Large Cap Blend' or categoriaMstar = 'RV USA Cap. Grande Blend'",
    "Emergentes": "zonaGeografica = 'Mercados Emergentes' OR categoria = 'Global Emerging Markets Equity' or categoriaMstar = 'RV Global Emergente'",
    "Japón": "categoria = 'Japan Equity' or categoriaMstar = 'RV Japón Cap. Grande'",
    "Small Caps": "categoria = 'Global Equity Mid/Small Cap' or categoriaMstar = 'RV Global Cap. Pequeña'",
    "Oro y Metales": "categoriaMstar = 'RV Sector Oro y Metales preciosos' OR categoria = 'Precious Metals Sector Equity'",
}

(timestamp_products, productos_lista) = get_productos()

df_productos = get_df_productos(productos_lista)

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
) = get_listas_opciones(df_productos)

cols = st.columns(2)
cols[0].title("Productos en MyInvestor")
filter_name = cols[1].text_input(
    "Filtrar por nombre or por ISIN (SQL ILIKE)",
    value="",
    placeholder="Ejemplo: world, FR0000978371...",
)
filter_name = filter_name.strip()
_filter_terms = [t.strip().replace("'", "''") for t in filter_name.split(",") if t.strip()]
if not _filter_terms:
    _filter_name_sql = "1=1"
else:
    _filter_name_sql = " OR ".join(
        f"codigoIsin ILIKE '%{t}%' OR nombre ILIKE '%{t}%'" for t in _filter_terms
    )

cols = st.columns(4)
selected_filter = cols[0].selectbox(
    "Filtro rápido:", options=list(FILTROS_RAPIDOS.keys())
)
selected_divisa = cols[1].multiselect(
    "Filtro por divisa", options=list(DIVISAS), default=["EUR"]
)
selected_producto = cols[2].multiselect(
    "Filtro por tipo de producto",
    options=list(TIPOS_PRODUCTO),
    default=["FONDOS_INDEXADOS"],
)
selected_gestora = cols[3].multiselect("Filtro por gestora:", options=list(GESTORAS))

year = datetime.date.today().year

with st.expander("Más filtros & Selección de columnas", expanded=False):
    with st.container():
        cols = st.columns(4)
        selected_categoria = cols[0].multiselect(
            "Filtro por categoría", options=list(CATEGORIAS)
        )
        selected_tipo_activo = cols[0].multiselect(
            "Filtro por tipo de activo", options=list(TIPO_ACTIVO)
        )
        selected_categoria_myinvestor = cols[1].multiselect(
            "Filtro por categoría MyInvestor",
            options=list(CATEGORIAS_MYINVESTOR),
        )
        selected_categoria_mstar = cols[2].multiselect(
            "Filtro por categoría Morningstar", options=list(CATEGORIAS_MSTAR)
        )
        selected_zona = cols[3].multiselect(
            "Filtro por zona geográfica", options=list(ZONAS)
        )

    with st.container():
        cols = st.columns(4)
        show_rentabilidad_anios = cols[0].toggle(
            "Mostrar rentabilidad ultimos 6 años", value=True
        )
        show_rentabilidad_media_135 = cols[0].toggle(
            "Mostrar rentabilidad media a 1,3,5 años", value=True
        )
        show_categories = cols[1].toggle("Mostrar categorias", value=False)
        show_volatilidad = cols[2].toggle("Mostrar datos Volatilidad", value=False)
        show_dias_desplazamiento = cols[3].toggle(
            "Mostrar días desplazamiento suscripción y reembolso", value=False
        )

    with st.container():
        cols = st.columns([2, 1, 1])
        selected_sector = cols[0].multiselect(
            "Filtro por sector (al menos uno debe cumplir el umbral)",
            options=SECTORES,
        )
        threshold_sector = cols[1].slider(
            "Umbral mínimo del sector (%)",
            min_value=0,
            max_value=100,
            step=5,
            key="threshold_sector",
            disabled=not selected_sector,
        )
        show_sectores = cols[2].toggle(
            "Mostrar sector(es) seleccionados",
            value=False,
            disabled=not selected_sector,
        )

def get_filtro_sql(field: str, options: list[str]):
    if not options or "Cualquiera" in options:
        return "1=1"
    return (
        field
        + " IN ("
        + ", ".join(
            [
                f"""'{opt.replace("'", "''")}'"""
                for opt in options
                if opt != "Cualquiera"
            ]
        )
        + ")"
    )


def get_filtro_sector_sql(sectores: list[str], threshold: float):
    if not sectores:
        return "1=1"
    sector_list = ", ".join(
        f"'{s.replace(chr(39), chr(39)+chr(39))}'" for s in sectores
    )
    return f"""codigoIsin IN (
        SELECT codigoIsin FROM df_productos, UNNEST(listaSectores) AS t(s)
        WHERE t.s.nombre IN ({sector_list}) AND t.s.porcent >= {threshold}
    )"""


def get_sector_columns_sql(sectores: list[str]):
    if not sectores:
        return ""
    parts = []
    for s in sectores:
        escaped = s.replace("'", "''")
        alias = s.replace("'", "")
        parts.append(
            f"    COALESCE(SUM(t.s.porcent) FILTER (WHERE t.s.nombre = '{escaped}'), 0) AS \"{alias} %\","
        )
    return "\n".join(parts)


_sector_cols = get_sector_columns_sql(selected_sector) if show_sectores else ""
_use_unnest = show_sectores and bool(selected_sector)

query = f"""
SELECT 
    codigoIsin,
    nombre,
    indicadorRiesgo as Risk,
    ter as TER,
    ytd as "{ year }",
    { "" if show_rentabilidad_anios else "-- " }rentabilidadPasadaUno as "{ year - 1 }",
    { "" if show_rentabilidad_anios else "-- " }rentabilidadPasadaDos as "{ year - 2 }",
    { "" if show_rentabilidad_anios else "-- " }rentabilidadPasadaTres as "{ year - 3 }",
    { "" if show_rentabilidad_anios else "-- " }rentabilidadPasadaCuatro as "{ year - 4 }",
    { "" if show_rentabilidad_anios else "-- " }rentabilidadPasadaCinco as "{ year - 5 }",
    { "" if show_rentabilidad_media_135 else "-- " }yearUno as "1Y",
    { "" if show_rentabilidad_media_135 else "-- " }yearTres as "3Y",
    { "" if show_rentabilidad_media_135 else "-- " }yearCinco as "5Y",
    { "" if show_volatilidad else "-- " }volatilidadYearUno as "Vol 1Y",
    { "" if show_volatilidad else "-- " }volatilidadYearTres as "Vol 3Y",
    { "" if show_volatilidad else "-- " }volatilidadYearCinco as "Vol 5Y",
    { "" if show_dias_desplazamiento else "-- " }diasDesplazamientoSuscripcion DiasS, diasDesplazamientoReembolso DiasR,
    { "" if show_categories else "-- " }categoria, categoriaMyInvestor, categoriaMstar,
    trackingErrorYearUno as TE_1Y,
    entidadGestora as Gestora,
    divisasDto.codigo AS divisa
    {("," + _sector_cols) if _sector_cols else ""}
FROM df_productos
    {"LEFT JOIN UNNEST(listaSectores) AS t(s) ON TRUE" if _use_unnest else ""}
WHERE
    ( {_filter_name_sql} ) -- filtro por nombre/ISIN
    AND ( {FILTROS_RAPIDOS[selected_filter]} ) -- filtro 
    AND ( {get_filtro_sql("divisa", selected_divisa)} ) -- filtro divisa
    AND ( {get_filtro_sql("zonaGeografica", selected_zona)} ) -- filtro zona geográfica
    AND ( {get_filtro_sql("tipoProductoEnum", selected_producto)} ) -- filtro tipo de producto
    AND ( {get_filtro_sql("categoria", selected_categoria)} ) -- filtro categoría
    AND ( {get_filtro_sql("categoriaMstar", selected_categoria_mstar)} ) -- filtro categoría Morningstar
    AND ( {get_filtro_sql("categoriaMyInvestor", selected_categoria_myinvestor)} ) -- filtro categoría MyInvestor
    AND ( {get_filtro_sql("entidadGestora", selected_gestora)} ) -- filtro gestora
    AND ( {get_filtro_sql("tipoActivo", selected_tipo_activo)} ) -- filtro tipo de activo
    AND ( {get_filtro_sector_sql(selected_sector, threshold_sector)} ) -- filtro sector
    AND status = 'OPEN'
{ "GROUP BY codigoIsin, nombre, indicadorRiesgo, ter, ytd, rentabilidadPasadaUno, rentabilidadPasadaDos, rentabilidadPasadaTres, rentabilidadPasadaCuatro, rentabilidadPasadaCinco, yearUno, yearTres, yearCinco, volatilidadYearUno, volatilidadYearTres, volatilidadYearCinco, diasDesplazamientoSuscripcion, diasDesplazamientoReembolso, categoria, categoriaMyInvestor, categoriaMstar, trackingErrorYearUno, entidadGestora, divisasDto" if _use_unnest else "" }
ORDER BY indicadorRiesgo ASC, ter ASC, codigoIsin ASC
"""

# query=f"""
# SELECT
#     codigoIsin,
#     df_productos.nombre,
#     indicadorRiesgo,
#     COALESCE(SUM(s.sector.porcent) FILTER (WHERE s.sector.nombre = 'Consumo Defensivo'), 0) AS pct_consumo_defensivo,
#     COALESCE(SUM(s.sector.porcent) FILTER (WHERE s.sector.nombre = 'Tecnología'), 0) AS pct_tecnologia
# FROM df_productos
# LEFT JOIN UNNEST(listaSectores) AS s(sector) ON TRUE
# WHERE indicadorRiesgo <= 4
# GROUP BY codigoIsin, df_productos.nombre, indicadorRiesgo
# ORDER BY indicadorRiesgo ASC, df_productos.nombre ASC;
# """

with st.expander("Consulta SQL"):
    st.code(query)

df = duckdb.query(query).df()
if df.empty:
    st.error("No hay productos que correspondan a esos filtros.")
    tabla = {"selection": {"rows": []}}
else:
    tabla = st.dataframe(
        df,
        # height=800,
        width="stretch",
        hide_index=True,
        key="productos_table",
        on_select="rerun",
        selection_mode="single-row",
    )

selected_rows = tabla.get("selection", {}).get("rows", [])


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def get_producto_by_isin(isin):
    return next((p for p in productos_lista if p["codigoIsin"] == isin), None)


def to_float(value):
    # remove % if exists and convert to float
    if isinstance(value, str) and value.endswith("%"):
        value = value[:-1]
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def render_comisiones(producto):
    if not producto or "listaComisiones" not in producto:
        return "No hay información de comisiones disponible."
    comisiones = producto["listaComisiones"]
    comisiones = sorted(
        comisiones, key=lambda x: to_float(x["porcentaje"]), reverse=True
    )
    st.subheader("Comisiones")
    comisiones_md = "| Comisión | Porcentaje |\n|---|---|\n"
    if producto.get("ter") is not None:
        comisiones_md += f"| **Total Expense Ratio (TER)** | **{producto['ter']}%** |\n"
    for com in comisiones:
        comisiones_md += f"| {com['nombre']} | {com['porcentaje']}% |\n"
    st.markdown(comisiones_md)
    # repeat link al KIID
    if producto.get("urlKiid"):
        st.markdown(
            f":material/link: [Key Investor Information Document]({producto['urlKiid']})",
            unsafe_allow_html=True,
        )


def render_regiones(producto):
    if not producto or "listaRegiones" not in producto:
        return
    regiones = producto["listaRegiones"]
    if not regiones or len(regiones) == 0:
        return

    regiones = sorted(regiones, key=lambda x: float(x["porcent"]), reverse=True)
    st.subheader("Regiones")
    regiones_md = "| Región | Porcentaje |\n|---|---|\n"
    for reg in regiones:
        regiones_md += f"| {reg['nombre']} | {reg['porcent']} |\n"
    st.markdown(regiones_md)


def render_composiciones(producto):
    if not producto or "listaComposiciones" not in producto:
        return
    composiciones = producto["listaComposiciones"]
    if not composiciones or len(composiciones) == 0:
        return

    composiciones = sorted(
        composiciones, key=lambda x: to_float(x["porcentaje"]), reverse=True
    )

    st.subheader("Composiciones")
    composiciones_df = pd.DataFrame(
        [
            {
                "ISIN": comp.get("codigoIsin"),
                "Nombre": comp.get("nombreFondo"),
                "Categoría": comp.get("categoria"),
                "Porcentaje": comp.get("porcentaje"),
            }
            for comp in composiciones
        ]
    )
    st.dataframe(
        composiciones_df,
        hide_index=True,
        width="stretch",
    )


def render_sectores(producto):
    if not producto or "listaSectores" not in producto:
        return
    sectores = producto["listaSectores"]
    if not sectores or len(sectores) == 0:
        return

    sectores = sorted(sectores, key=lambda x: float(x["porcent"]), reverse=True)
    st.subheader("Sectores")
    sectores_md = "| Sector | Porcentaje |\n|---|---|\n"
    for sec in sectores:
        sectores_md += f"| {sec['nombre']} | {sec['porcent']} |\n"
    st.markdown(sectores_md)


def get_general_info_markdown(producto):
    if not producto:
        return "No hay información disponible."


def format_bool(value):
    if value is True:
        return "Si"
    if value is False:
        return "No"
    return "N/D"


def format_text(value):
    if value is None or value == "":
        return "N/D"
    return str(value)


def has_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned not in {"", "."}
    return True


def render_general_info(producto):
    datos_fondo = producto.get("datosFondo") or {}

    with st.container(vertical_alignment="center", horizontal=True):
        st.subheader(
            f"{producto.get('nombre', 'Producto')} :orange-badge[{producto.get('codigoIsin', 'ISIN N/D')}] :violet-badge[{producto.get('tipoActivo', 'N/A')}]"
        )
        st.metric(
            "Indicador de riesgo", format_text(datos_fondo.get("indicadorRiesgo"))
        )

    descripcion = producto.get("descripcion")
    if has_value(descripcion):
        st.write(descripcion)

    datos_fondo = producto.get("datosFondo") or {}

    links = [
        (
            "Ficha tecnica",
            producto.get("urlFichaTecnica") or datos_fondo.get("urlFichaTecnica"),
        ),
        (
            "Datos fundamentales",
            producto.get("urlDatosFundamentales")
            or datos_fondo.get("urlDatosFundamentales"),
        ),
        ("Informe semestral", producto.get("urlInformeSemestral")),
        ("Memoria", producto.get("urlMemoria")),
        ("KIID", producto.get("urlKiid")),
        (
            "Morningstar",
            (
                f"https://www.morningstar.es/es/funds/snapshot/snapshot.aspx?id={producto.get('secIdFondoMorningstar')}"
                if producto.get("secIdFondoMorningstar")
                else None
            ),
        ),
    ]

    shown_links = [(label, url) for label, url in links if has_value(url)]
    if shown_links:
        st.markdown(
            ":material/link: Links: "
            + ", ".join(f"[{label}]({url})" for label, url in shown_links)
        )


def render_general_info_tabla(producto):
    datos_fondo = producto.get("datosFondo") or {}

    detalles = [
        ("Categoría", format_text(producto.get("categoria"))),
        ("Categoría MyInvestor", format_text(producto.get("categoriaMyInvestor"))),
        ("Categoría Morningstar", format_text(producto.get("categoriaMstar"))),
        ("Zona geográfica", format_text(producto.get("zonaGeografica"))),
        ("Tipo de producto", format_text(producto.get("tipoProductoEnum"))),
        ("Perfil del plan", format_text(datos_fondo.get("tipoPerfilPlanEnum"))),
        ("Entidad gestora", format_text(datos_fondo.get("entidadGestora"))),
        ("Entidad depositaria", format_text(datos_fondo.get("entidadDepositaria"))),
        ("Entidad promotora", format_text(datos_fondo.get("entidadPromotora"))),
        ("FP adscrito", format_text(datos_fondo.get("fpAdscrito"))),
        (
            "Días desplazamiento suscripción",
            format_text(producto.get("diasDesplazamientoSuscripcion")),
        ),
        (
            "Días desplazamiento reembolso",
            format_text(producto.get("diasDesplazamientoReembolso")),
        ),
        (
            "Hora límite suscripción mismo día",
            format_text(producto.get("horaLimiteSuscripcionMismoDia")),
        ),
        ("Tracking Error a 1 año", format_text(producto.get("trackingErrorYearUno"))),
    ]

    st.subheader("Datos generales")
    detalles_md = "| Campo | Valor |\n|---|---|\n"
    detalles_md += "\n".join(
        f"| {campo} | {valor} |"
        for campo, valor in detalles
        if has_value(valor) and valor != "N/D"
    )
    st.markdown(detalles_md)


# render rentabilidad años pasados en un altair bar chart
def render_rentabilidad(producto):
    cols = st.columns(2)

    rentabilidades = []
    for i, span in enumerate(
        ["ytd"]
        + [
            "rentabilidadPasada" + suf
            for suf in ["Uno", "Dos", "Tres", "Cuatro", "Cinco"]
        ]
    ):
        value = producto.get(span)
        if value is not None:
            rentabilidades.append((year - i, value))
    if rentabilidades:
        df_rentabilidades = pd.DataFrame(
            rentabilidades, columns=["Año", "Rentabilidad"]
        )
        chart = (
            alt.Chart(df_rentabilidades)
            .mark_bar()
            .encode(
                x=alt.X("Año:O", axis=alt.Axis(labelAngle=0)),
                y="Rentabilidad:Q",
                color=alt.condition(
                    alt.datum.Rentabilidad > 0,
                    alt.value("green"),  # Color for positive
                    alt.value("red"),  # Color for negative
                ),
                tooltip=["Año", "Rentabilidad"],
            )
            .properties(title="Rentabilidad histórica")
        )
        with cols[0]:
            st.altair_chart(chart, width="stretch")

    # now, same with YearUno, YearTres and YearCinco, but as YoY a 1, 3, y 5 años (Year over Year)
    yoy_rentabilidades = []
    for span, label in [
        ("yearUno", "1 año"),
        ("yearTres", "3 años"),
        ("yearCinco", "5 años"),
    ]:
        value = producto.get(span)
        if value is not None:
            yoy_rentabilidades.append((label, value))
    if yoy_rentabilidades:
        df_yoy = pd.DataFrame(yoy_rentabilidades, columns=["Periodo", "Rentabilidad"])
        chart_yoy = (
            alt.Chart(df_yoy)
            .mark_bar()
            .encode(
                x=alt.X("Periodo:O", axis=alt.Axis(labelAngle=0)),
                y="Rentabilidad:Q",
                color=alt.condition(
                    alt.datum.Rentabilidad > 0,
                    alt.value("green"),  # Color for positive
                    alt.value("red"),  # Color for negative
                ),
                tooltip=["Periodo", "Rentabilidad"],
            )
            .properties(title="Rentabilidad anual a 1, 3 y 5 años")
        )
        with cols[1]:
            st.altair_chart(chart_yoy, width="stretch")

    # Disclaimer
    st.markdown(
        "<small>:grey[Rentabilidades pasadas no garantizan rentabilidades futuras. Invertir en fondos conlleva riesgo de pérdida de capital.]</small>",
        unsafe_allow_html=True,
    )


def format_percent_from_decimal(value):
    return f"{value * 100:.2f}%"


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
                    st.warning("Algunos productos fueron excluidos por datos incompletos.")
                    st.dataframe(excluded_df, hide_index=True, width="stretch")

            except RecommendationError as err:
                st.error(f"No se pudo calcular recomendación: {err}")
        else:
            st.info("Selecciona uno o más ISIN para calcular mix recomendado.")


selected_row_index = selected_rows[0] if selected_rows else None
if selected_row_index is not None and 0 <= selected_row_index < len(df):
    selected_isin = df.iloc[selected_row_index]["codigoIsin"]
elif df.shape[0] == 1:
    selected_isin = df.iloc[0]["codigoIsin"]
else:
    selected_isin = None

if selected_isin:
    producto = get_producto_by_isin(selected_isin)
    if not producto:
        st.warning("No se encontraron los detalles del producto seleccionado.")
    else:
        nombre_producto = producto["nombre"]

        with st.expander(f"Información del producto", expanded=True):
            render_general_info(producto)
            render_rentabilidad(producto)
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

        # with st.expander(f"Información del producto", expanded=True):
        #     render_general_info(producto)
        #     with st.container(horizontal=True):
        #         with st.container():
        #             render_general_info_tabla(producto)
        #         with st.container():
        #             render_comisiones(producto)
        #         with st.container():
        #             render_sectores(producto)
        #     with st.expander("Detalle completo del producto", expanded=False):
        #         st.json(producto)

else:
    st.write("Selecciona un producto para ver sus detalles.")

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

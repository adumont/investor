import streamlit as st
import duckdb
import pandas as pd
import json
import altair as alt
from dotenv import load_dotenv
from os import getenv
import datetime

from vars import CACHE_TTL

from productos import (
    get_productos,
    get_df_productos,
    get_listas_opciones,
)

load_dotenv()

# example of 1 product
# {
#     "idFondo": 10401,
#     "codigoIsin": "IE000ZYRH0Q7",
#     "nombre": "iShares Developed World Index (IE) Acc EUR clase S",
#     "categoria": "Global Equity Large Cap",
#     "urlKiid": "https://api.fundinfo.com/document/38486977bba8e8e764d4dd9b8528564d_130936/PRP_ES_es_IE000ZYRH0Q7_YES_2025-09-05.pdf?apiKey=282b2922-c396-415c-9a88-a721851feedc",
#     "urlInformeSemestral": "https://api.fundinfo.com/document/0ec9d68eb9eb7700131841b8c579b828_4662010/SAR_ES_en_IE000ZYRH0Q7_YES_2024-11-30.pdf?apiKey=282b2922-c396-415c-9a88-a721851feedc",
#     "urlMemoria": "https://www.inversis.com/trans/inversis/SvlGenerarDocumentoPdf?srv=imprimirMemoriaFondo&codigoFondo=1163096&ext=.pdf&institucion=1854326",
# "ytd": 3.51,
# "yearUno": 28.45,
# "yearTres": 15.97,
# "yearCinco": 15.97,
# "volatilidad": 10.41,
# "volatilidadYearUno": 10.41,
# "volatilidadYearTres": 10.98,
# "volatilidadYearCinco": 10.98,
# "activosAcciones": 98.78,
# "activosObligaciones": 0,
# "activosEfectivo": 1.03,
# "activosOtro": 0.19,
# "impMinPrimeraSubs": "1.00 EUR",
# "impMinSubsSucesivas": "1.00 EUR",
# "categoriaMyInvestor": "Otros",
# "rentabilidadInicio": 8.31,
# "descatalogado": false,
# "mercado": "FEX",
#     "divisasDto": {
#         "codigo": "EUR",
#         "nombre": "EURO",
#         "nombreIngles": "Euro",
#         "simbolo": "€"
#     },
#     "ter": 0.06,
#     "tipoActivo": "Renta Variable",
#     "zonaGeografica": "Global",
#     "indicadorRiesgo": 5,
#     "listaComisiones": [
#         {
#             "nombre": "Gestión",
#             "porcentaje": "0.04"
#         },
#         {
#             "nombre": "Distribución (cobrada por la gestora)",
#             "porcentaje": "0.0"
#         },
#         {
#             "nombre": "Depósito",
#             "porcentaje": "0.0"
#         },
#         {
#             "nombre": "Costes operativos/transaccionales",
#             "porcentaje": "0.00010"
#         },
#         {
#             "nombre": "Suscripción",
#             "porcentaje": "0.0"
#         }
#     ],
#     "listaComposiciones": [],
#     "listaRegiones": [],
#     "listaSectores": [
#         {
#             "nombre": "Materiales Básicos",
#             "porcent": 3.57,
#             "img": null
#         },
#         {
#             "nombre": "Tecnología",
#             "porcent": 25.92,
#             "img": null
#         },
#         {
#             "nombre": "Servicios de Comunicación",
#             "porcent": 8.77,
#             "img": null
#         },
#         {
#             "nombre": "Consumo Cíclico",
#             "porcent": 9.43,
#             "img": null
#         },
#         {
#             "nombre": "Consumo Defensivo",
#             "porcent": 5.76,
#             "img": null
#         },
#         {
#             "nombre": "Salud",
#             "porcent": 9.88,
#             "img": null
#         },
#         {
#             "nombre": "Industria",
#             "porcent": 11.99,
#             "img": null
#         },
#         {
#             "nombre": "Energía",
#             "porcent": 3.96,
#             "img": null
#         },
#         {
#             "nombre": "Servicios Públicos",
#             "porcent": 2.78,
#             "img": null
#         },
#         {
#             "nombre": "Inmobiliaria",
#             "porcent": 1.93,
#             "img": null
#         },
#         {
#             "nombre": "Servicios Financieros",
#             "porcent": 16.01,
#             "img": null
#         }
#     ],
#     "datosFondo": {
#         "tipoPerfilPlanEnum": null,
#         "predeterminado": false,
#         "resaltado": false,
#         "entidadGestora": "BlackRock",
#         "entidadDepositaria": null,
#         "entidadPromotora": null,
#         "fpAdscrito": null,
#         "urlFichaTecnica": null,
#         "urlDatosFundamentales": null,
#         "indicadorRiesgo": 5
#     },
#     "tipoProductoEnum": "FONDOS_INDEXADOS",
#     "sinRetrocesion": false,
#     "horaLimiteSuscripcionMismoDia": "09:00",
#     "diasDesplazamientoSuscripcion": "4",
#     "diasDesplazamientoReembolso": "4",
#     "diasDesplazamientoVl": "1",
#     "fechaActualizacionRentabilidad": 1776493080000,
#     "complejo": false,
#     "numeroDecimalesParticipacion": 2,
#     "fondoDistribucion": false,
#     "socialmenteResponsable": false,
#     "modoOperativaPermitidaEnum": "IMPORTE_Y_PARTICIPACIONES",
#     "idFondoMorningstar": "FSUSA0BD2Z",
#     "secIdFondoMorningstar": "F00001SELX",
#     "categoriaMstar": "RV Global Cap. Grande Blend",
#     "entidadGestora": "BlackRock",
#     "fechaLanzamiento": 1274313600000,
#     "patrimonio": 24969069538,
#     "valorLiquidativo": 11.06,
#     "fechaValorLiquidativo": 1776297600000,
#     "status": "OPEN",
#     "impMinReembolso": "0.00 EUR",
#     "rentabilidadAcumuladaInicio": 10.6
# },


st.set_page_config(
    page_title="Investor", layout="wide", page_icon=":material/finance_mode:"
)

if "threshold_sector_saved" not in st.session_state:
    st.session_state.threshold_sector_saved = 20


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

FILTRO = {
    "Cualquiera": "1=1",
    "World": "( categoria = 'Global Equity Large Cap' or categoria = 'Global Equity Lage Cap' or  categoriaMstar = 'RV Global Cap. Grande Blend' )",
    "Emergentes": "( zonaGeografica = 'Mercados Emergentes' OR categoria = 'Global Emerging Markets Equity' or categoriaMstar = 'RV Global Emergente' )",
    "Small Caps": "categoria = 'Global Equity Mid/Small Cap' or categoriaMstar = 'RV Global Cap. Pequeña'",
    "Oro y Metales": "categoriaMstar = 'RV Sector Oro y Metales preciosos' OR categoria = 'Precious Metals Sector Equity'",
}

productos_lista = get_productos()

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
with cols[0]:
    st.title("Productos de Inversión en MyInvestor")
with cols[1]:
    filter_name = st.text_input(
        "Filtrar por nombre or por ISIN (SQL ILIKE)",
        value="",
        placeholder="Ejemplo: 'world', 'FR0000978371'...",
    )

cols = st.columns(4)
selected_filter = cols[0].selectbox("Selecciona un filtro", options=list(FILTRO.keys()))
selected_divisa = cols[1].multiselect(
    "Selecciona una divisa", options=list(DIVISAS), default=["EUR"]
)
selected_producto = cols[2].multiselect(
    "Selecciona un tipo de producto",
    options=list(TIPOS_PRODUCTO),
    default=["FONDOS_INDEXADOS"],
)
selected_gestora = cols[3].multiselect(
    "Selecciona una gestora", options=list(GESTORAS)
)

selected_sector = None

year = datetime.date.today().year

with st.expander("Filtrado avanzado & Selección de columnas", expanded=False):
    with st.container():
        cols = st.columns(4)
        selected_categoria = cols[0].multiselect(
            "Selecciona una categoría", options=list(CATEGORIAS)
        )
        selected_tipo_activo = cols[0].multiselect(
            "Selecciona un tipo de activo", options=list(TIPO_ACTIVO)
        )
        selected_categoria_myinvestor = cols[1].multiselect(
            "Selecciona una categoría MyInvestor",
            options=list(CATEGORIAS_MYINVESTOR),
        )
        selected_categoria_mstar = cols[2].multiselect(
            "Selecciona una categoría Morningstar", options=list(CATEGORIAS_MSTAR)
        )
        selected_zona = cols[3].multiselect(
            "Selecciona una zona geográfica", options=list(ZONAS)
        )

    with st.container():
        cols = st.columns(3)
        show_rentabilidad_anios = cols[0].toggle(
            "Mostrar rentabilidad ultimos 6 años", value=True
        )
        show_rentabilidad_media_135 = cols[0].toggle(
            "Mostrar rentabilidad media a 1,3,5 años", value=True
        )
        show_categories = cols[1].toggle("Mostrar categorias", value=False)
        show_dias_desplazamiento = cols[2].toggle(
            "Mostrar días desplazamiento suscripción y reembolso", value=False
        )


def get_filtro_sql(field: str, options: list[str]):
    if not options or "Cualquiera" in options:
        return "1=1"
    return (
        field
        + " IN ("
        + ", ".join([f"""'{opt.replace("'", "''")}'""" for opt in options if opt != "Cualquiera"])
        + ")"
    )


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
    { "" if show_rentabilidad_media_135 else "-- " }yearUno as "YoY 1Y",
    { "" if show_rentabilidad_media_135 else "-- " }yearTres as "YoY 3Y",
    { "" if show_rentabilidad_media_135 else "-- " }yearCinco as "YoY 5Y",
    { "" if show_dias_desplazamiento else "-- " }diasDesplazamientoSuscripcion DiasS, diasDesplazamientoReembolso DiasR,
    { "" if show_categories else "-- " }categoria, categoriaMyInvestor, categoriaMstar,
    entidadGestora as Gestora,
    divisasDto.codigo AS divisa,
    -- zonaGeografica,
    -- tipoProductoEnum
FROM df_productos
WHERE
    ( codigoIsin ILIKE '%{filter_name}%' OR -- filtro por ISIN
        nombre ILIKE '%{filter_name}%' ) -- filtro por nombre
    AND ( {FILTRO[selected_filter]} ) -- filtro 
    AND ( {get_filtro_sql("divisa", selected_divisa)} ) -- filtro divisa
    AND ( {get_filtro_sql("zonaGeografica", selected_zona)} ) -- filtro zona geográfica
    AND ( {get_filtro_sql("tipoProductoEnum", selected_producto)} ) -- filtro tipo de producto
    AND ( {get_filtro_sql("categoria", selected_categoria)} ) -- filtro categoría
    AND ( {get_filtro_sql("categoriaMstar", selected_categoria_mstar)} ) -- filtro categoría Morningstar
    AND ( {get_filtro_sql("categoriaMyInvestor", selected_categoria_myinvestor)} ) -- filtro categoría MyInvestor
    AND ( {get_filtro_sql("entidadGestora", selected_gestora)} ) -- filtro gestora
    AND ( {get_filtro_sql("tipoActivo", selected_tipo_activo)} ) -- filtro tipo de activo
    AND status = 'OPEN'
ORDER BY indicadorRiesgo ASC, ter ASC
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
tabla = st.dataframe(
    df,
    # height=800,
    use_container_width=True,
    hide_index=True,
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


def render_sectores(producto):
    if not producto or "listaSectores" not in producto:
        return "No hay información de sectores disponible."
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
            st.altair_chart(chart, use_container_width=True)

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
            st.altair_chart(chart_yoy, use_container_width=True)

    # Disclaimer
    st.markdown(
        "<small>:red-badge[:material/warning: Aviso] Rentabilidades pasadas no garantizan rentabilidades futuras. Invertir en fondos conlleva riesgo de pérdida de capital.</small>",
        unsafe_allow_html=True,
    )


if selected_rows:
    selected_isin = df.iloc[selected_rows[0]]["codigoIsin"]
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
            render_sectores(producto)
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
st.markdown(
    "<small>:orange-badge[:material/warning: Aviso] El listado de productos es una *foto* del 18/04/2006.</small>",
    unsafe_allow_html=True,
)

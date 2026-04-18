import streamlit as st
import duckdb
import pandas as pd
import json
from dotenv import load_dotenv
from os import getenv

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


st.set_page_config(page_title="Investor", layout="wide", page_icon=":material/explore:")

@st.cache_data(show_spinner="Descargando datos...", ttl=6*60*60)
def download_json_from_url(url):
    import requests

    response = requests.get(url)
    st.write(f"Descargando datos desde {url}...")

    return response.json()

# productos_lista = download_json_from_url(getenv("PRODUCT_JSON_URL"))
with open("myinvestor.json", "r", encoding="utf-8") as f:
    productos_lista = json.load(f)

# with st.expander("Productos JSON"):
#     st.json(productos_lista[0])

df_productos = pd.DataFrame(productos_lista)

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

CATEGORIAS = {
    "Cualquiera": "1=1",
    "Emergentes": "tipoActivo = 'Renta Variable' and zonaGeografica = 'Mercados Emergentes' and divisasDto.codigo = 'EUR' and tipoProductoEnum = 'FONDOS_INDEXADOS'",
    "World": """(nombre ilike '%world%' or nombre ilike '%global%' ) AND tipoActivo = 'Renta Variable' and zonaGeografica = 'Global' and divisasDto.codigo = 'EUR' and tipoProductoEnum = 'FONDOS_INDEXADOS'""",
    "Oro y Metales": "categoriaMstar = 'RV Sector Oro y Metales preciosos'"
}


# get list of divisas from df_productos
divisas_list = df_productos['divisasDto'].apply(lambda x: x['codigo']).unique()

DIVISAS = { "Cualquiera": "1=1"}
for divisa in df_productos['divisasDto'].apply(lambda x: x['codigo']).unique():
    DIVISAS[divisa] = f"divisasDto.codigo = '{divisa}'"

#Filtro de zona geográfica
ZONAS = { "Cualquiera": "1=1"}
for zona in df_productos['zonaGeografica'].unique():
    ZONAS[zona] = f"zonaGeografica = '{zona}'"

# Filtro Tipo de producto
TIPOS_PRODUCTO = { "Cualquiera": "1=1"}
for tipo in df_productos['tipoProductoEnum'].unique():
    TIPOS_PRODUCTO[tipo] = f"tipoProductoEnum = '{tipo}'"


cols = st.columns(2)
with cols[0]:
    st.title("Productos de Inversión en MyInvestor")
with cols[1]:
    filter_name = st.text_input("Filtrar por nombre (SQL ILIKE)", value="", placeholder="Ejemplo: 'world'")

cols = st.columns(4)
with cols[0]:
    selected_filter = st.selectbox("Selecciona una categoría", options=list(CATEGORIAS.keys()))
with cols[1]:
    selected_divisa = st.selectbox("Selecciona una divisa", options=list(DIVISAS.keys()))
with cols[2]:
    selected_producto = st.selectbox("Selecciona un tipo de producto", options=list(TIPOS_PRODUCTO.keys()))
with cols[3]:
    selected_zona = st.selectbox("Selecciona una zona geográfica", options=list(ZONAS.keys()))


query = f"""
    SELECT 
        codigoIsin,
        nombre,
        indicadorRiesgo,
        ter,
        ytd, yearUno, yearTres, yearCinco,
        diasDesplazamientoSuscripcion DiasS, diasDesplazamientoReembolso DiasR,
        entidadGestora as Gestora,
        divisasDto.codigo AS divisa,
        -- zonaGeografica,
        -- tipoProductoEnum
        horaLimiteSuscripcionMismoDia HoraLimite
    FROM df_productos
    WHERE
        nombre ILIKE '%{filter_name}%' -- filtro por nombre
        AND {CATEGORIAS[selected_filter]} -- filtro categoría 
        AND {DIVISAS[selected_divisa]} -- filtro divisa
        AND {ZONAS[selected_zona]} -- filtro zona geográfica
        AND {TIPOS_PRODUCTO[selected_producto]} -- filtro tipo de producto
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

df = duckdb.query(query).df()
with st.expander("Consulta SQL"):
    st.code(query)

tabla = st.dataframe(df, height=800)

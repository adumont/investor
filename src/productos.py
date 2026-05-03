from streamlit import cache_data
import json

from vars import CACHE_TTL


def download_json_from_url(url):
    import requests

    response = requests.get(url)
    return response.json()


def read_json_from_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


@cache_data(show_spinner="Descargando datos...", ttl=CACHE_TTL)
def get_productos():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    date_time = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y %H:%M (%Z)")
    try:
        productos = download_json_from_url(
            "https://api.myinvestor.es/myinvestor-server/rest/public/fondos/find-fondos?tipo=TODOS&token=a2e8e18ad26a079c576038f0ad4fa18ce0d9e415f5bf6f43f89cf3831a0e4685__"
        )
        print(
            f"Datos descargados correctamente, {len(productos)} productos, fecha y hora de descarga: {date_time}"
        )
        return (date_time, productos)
    except Exception as e:
        print(f"Error al descargar datos: {e} - leyendo desde archivo local...")

    from vars import LOCAL_FILE, LOCAL_FILE_TIMESTAMP

    return (LOCAL_FILE_TIMESTAMP, read_json_from_file(LOCAL_FILE))


def get_df_productos(productos):
    import pandas as pd

    return pd.DataFrame(productos)


@cache_data(show_spinner=False, ttl=CACHE_TTL)
def get_listas_opciones(_df_productos, data_version: str):

    DIVISAS = (
        _df_productos["divisasDto"]
        .apply(
            lambda x: (
                x.get("codigo") if isinstance(x, dict) and x.get("codigo") else None
            )
        )
        .dropna()
        .unique()
    )

    TIPOS_PRODUCTO = _df_productos["tipoProductoEnum"].dropna().unique()

    _STR_COLS = [
        "zonaGeografica",
        "tipoActivo",
        "categoria",
        "categoriaMyInvestor",
        "categoriaMstar",
        "entidadGestora",
    ]
    _unique_map = _df_productos[_STR_COLS].agg(
        lambda col: col.dropna().unique().tolist()
    )
    ZONAS = _unique_map["zonaGeografica"]
    TIPO_ACTIVO = _unique_map["tipoActivo"]
    CATEGORIAS = _unique_map["categoria"]
    CATEGORIAS_MYINVESTOR = _unique_map["categoriaMyInvestor"]
    CATEGORIAS_MSTAR = _unique_map["categoriaMstar"]
    GESTORAS = _unique_map["entidadGestora"]

    SECTORES = set()
    for sector_list in _df_productos["listaSectores"].dropna():
        if isinstance(sector_list, list):
            for s in sector_list:
                nombre = s.get("nombre")
                if nombre:
                    SECTORES.add(nombre)

    # map(lambda, tuple) applies casefold-sort to each element,
    # then tuple() rewraps results to preserve original order.
    return tuple(
        map(
            lambda x: sorted(x, key=lambda s: str(s).strip().casefold()),
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
            ),
        )
    )

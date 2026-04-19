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
    return read_json_from_file("myinvestor.json")


def get_df_productos(productos):
    import pandas as pd

    return pd.DataFrame(productos)


@cache_data(show_spinner=False, ttl=CACHE_TTL)
def get_listas_opciones(_df_productos):
    import pandas as pd

    DIVISAS = _df_productos["divisasDto"].apply(lambda x: x["codigo"]).unique()
    # remove "nan" from DIVISAS
    ZONAS = _df_productos["zonaGeografica"].apply(lambda x: str(x)).unique().tolist()
    ZONAS.remove("nan")
    
    TIPOS_PRODUCTO = _df_productos["tipoProductoEnum"].unique()

    CATEGORIAS = _df_productos["categoria"].apply(lambda x: str(x)).unique().tolist()
    CATEGORIAS.remove("nan")

    CATEGORIAS_MYINVESTOR = _df_productos["categoriaMyInvestor"].apply(lambda x: str(x)).unique().tolist()
    CATEGORIAS_MYINVESTOR.remove("nan")

    CATEGORIAS_MSTAR = _df_productos["categoriaMstar"].apply(lambda x: str(x)).unique().tolist()
    CATEGORIAS_MSTAR.remove("nan")

    GESTORAS = _df_productos["entidadGestora"].apply(lambda x: str(x)).unique().tolist()
    GESTORAS.remove("nan")

    SECTORES = []

    return (
        DIVISAS,
        ZONAS,
        TIPOS_PRODUCTO,
        CATEGORIAS,
        CATEGORIAS_MYINVESTOR,
        CATEGORIAS_MSTAR,
        GESTORAS,
        SECTORES,
    )

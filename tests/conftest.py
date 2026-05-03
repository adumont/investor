import json
from pathlib import Path

import pytest

DATA_PATH = Path(__file__).parent.parent / "data" / "myinvestor.json"


@pytest.fixture
def myinvestor_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_product():
    return {
        "codigoIsin": "ES0123456789",
        "nombre": "Test Fund",
        "yearUno": 10.5,
        "yearTres": 8.2,
        "yearCinco": 7.0,
        "volatilidadYearUno": 12.0,
        "volatilidadYearTres": 11.0,
        "volatilidadYearCinco": 10.0,
        "volatilidad": 12.0,
        "ter": 0.5,
        "indicadorRiesgo": 4,
        "categoriaMstar": "Global Equity Large Cap",
        "categoria": "Global Equity Large Cap",
        "zonaGeografica": "Global",
        "tipoActivo": "Renta Variable",
        "entidadGestora": "Test Manager",
        "divisasDto": {"codigo": "EUR"},
        "listaSectores": [],
        "status": "OPEN",
    }


@pytest.fixture
def sample_products(sample_product):
    return [sample_product]

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.productos import download_json_from_url, get_df_productos, read_json_from_file


class TestReadJsonFromFile:
    def test_valid_file(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('[{"a": 1}]', encoding="utf-8")
        data = read_json_from_file(str(f))
        assert data == [{"a": 1}]

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_json_from_file(str(tmp_path / "nonexistent.json"))

    def test_corrupt_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{invalid}", encoding="utf-8")
        with pytest.raises(ValueError):
            read_json_from_file(str(f))


class TestGetDfProductos:
    def test_returns_dataframe(self):
        products = [{"codigoIsin": "ES1", "nombre": "A"}]
        df = get_df_productos(products)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["codigoIsin"] == "ES1"


class TestGetListasOpciones:
    def test_extracts_options(self, myinvestor_data):
        from src.productos import _extract_options

        df = get_df_productos(myinvestor_data)
        result = _extract_options(df)
        assert len(result) == 9
        divisas, zonas, tipos, *rest = result
        assert "EUR" in divisas
        assert len(zonas) > 0

    def test_handles_null_divisas(self):
        from src.productos import _extract_options

        df = pd.DataFrame(
            {
                "divisasDto": [None, {"codigo": "EUR"}],
                "tipoProductoEnum": ["FONDOS_INDEXADOS", "FONDOS_INDEXADOS"],
                "zonaGeografica": [None, "Global"],
                "tipoActivo": [None, "Renta Variable"],
                "categoria": [None, "Cat"],
                "categoriaMyInvestor": [None, "Otros"],
                "categoriaMstar": [None, "Mstar"],
                "entidadGestora": [None, "Manager"],
                "listaSectores": [None, None],
            }
        )
        result = _extract_options(df)
        divisas = result[0]
        assert "EUR" in divisas
        assert len(divisas) == 1

    def test_sorted_output(self, myinvestor_data):
        from src.productos import _extract_options

        df = get_df_productos(myinvestor_data)
        result = _extract_options(df)
        for options in result:
            assert options == sorted(options, key=lambda s: str(s).strip().casefold())


class TestDownloadJsonFromUrl:
    @patch("src.productos.requests")
    def test_api_success(self, mock_requests):
        mock_response = MagicMock()
        mock_response.json.return_value = [{"a": 1}]
        mock_requests.get.return_value = mock_response

        result = download_json_from_url("http://fake")
        assert result == [{"a": 1}]

    @patch("src.productos.requests")
    def test_raises_on_error(self, mock_requests):
        mock_requests.get.side_effect = Exception("Network error")

        with pytest.raises(Exception):
            download_json_from_url("http://fake")


class TestGetProductos:
    @patch("src.productos.requests")
    def test_api_failure_fallback(self, mock_requests):
        from src.productos import get_productos

        # Clear cache to ensure fresh execution
        try:
            get_productos.clear()
        except Exception:
            pass

        # Make API fail
        mock_requests.get.side_effect = Exception("Network error")

        result = get_productos()
        assert result is not None
        assert len(result) == 2
        assert len(result[1]) > 0  # Should fallback to local file

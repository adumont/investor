from src.queries import (
    FilterState,
    build_name_filter_sql,
    build_product_query,
    get_filtro_sector_sql,
    get_filtro_sql,
    get_sector_columns_sql,
)


class TestGetFiltroSql:
    def test_empty_options(self):
        assert get_filtro_sql("divisa", []) == "1=1"

    def test_any_option(self):
        assert get_filtro_sql("divisa", ["Cualquiera"]) == "1=1"

    def test_single_option(self):
        result = get_filtro_sql("divisa", ["EUR"])
        assert result == "divisa IN ('EUR')"

    def test_multiple_options(self):
        result = get_filtro_sql("divisa", ["EUR", "USD"])
        assert "EUR" in result
        assert "USD" in result
        assert "IN" in result

    def test_sql_injection_escape(self):
        result = get_filtro_sql("divisa", ["'; DROP TABLE--"])
        assert "''" in result


class TestBuildNameFilterSql:
    def test_empty(self):
        assert build_name_filter_sql("") == "1=1"
        assert build_name_filter_sql("   ") == "1=1"

    def test_single_term(self):
        result = build_name_filter_sql("ES123")
        assert "ILIKE" in result
        assert "ES123" in result

    def test_multiple_terms(self):
        result = build_name_filter_sql("ES123, US456")
        assert "OR" in result

    def test_sql_escape(self):
        result = build_name_filter_sql("'; DROP--")
        assert "''" in result


class TestGetFiltroSectorSql:
    def test_empty(self):
        assert get_filtro_sector_sql([], 20) == "1=1"

    def test_with_sectors(self):
        result = get_filtro_sector_sql(["Tech"], 20)
        assert "UNNEST" in result
        assert "Tech" in result
        assert "20" in result


class TestGetSectorColumnsSql:
    def test_empty(self):
        assert get_sector_columns_sql([]) == ""

    def test_single_sector(self):
        result = get_sector_columns_sql(["Tech"])
        assert "Tech" in result
        assert "COALESCE" in result

    def test_escaping(self):
        result = get_sector_columns_sql(["It's"])
        assert "''" in result


class TestBuildProductQuery:
    def test_basic_query(self):
        f = FilterState()
        query = build_product_query(f)
        assert "SELECT" in query
        assert "FROM df_productos" in query
        assert "ORDER BY" in query

    def test_name_filter(self):
        f = FilterState(filter_name="ES123")
        query = build_product_query(f)
        assert "ES123" in query

    def test_sector_columns(self):
        f = FilterState(
            show_sectores=True, selected_sector=["Tech"], show_categories=True
        )
        query = build_product_query(f)
        assert "Tech" in query
        assert "UNNEST" in query

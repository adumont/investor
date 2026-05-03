from dataclasses import dataclass, field


@dataclass
class FilterState:
    """Consolidated filter/selections state from the UI."""
    year: int = 2026
    show_rentabilidad_anios: bool = True
    show_rentabilidad_media_135: bool = True
    show_volatilidad: bool = False
    show_dias_desplazamiento: bool = False
    show_categories: bool = False
    show_sectores: bool = False
    selected_sector: list[str] = field(default_factory=list)
    threshold_sector: int = 20
    filter_name: str = ""
    selected_filter_sql: str = "1=1"
    selected_divisa: list[str] = field(default_factory=lambda: ["EUR"])
    selected_zona: list[str] = field(default_factory=list)
    selected_producto: list[str] = field(default_factory=lambda: ["FONDOS_INDEXADOS"])
    selected_categoria: list[str] = field(default_factory=list)
    selected_categoria_mstar: list[str] = field(default_factory=list)
    selected_categoria_myinvestor: list[str] = field(default_factory=list)
    selected_gestora: list[str] = field(default_factory=list)
    selected_tipo_activo: list[str] = field(default_factory=list)


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


def build_name_filter_sql(filter_name: str) -> str:
    """Build SQL fragment for name/ISIN search."""
    terms = [t.strip().replace("'", "''") for t in filter_name.split(",") if t.strip()]
    if not terms:
        return "1=1"
    return " OR ".join(
        f"codigoIsin ILIKE '%{t}%' OR nombre ILIKE '%{t}%'" for t in terms
    )


def build_product_query(f: FilterState) -> str:
    """Build the main product SELECT query from FilterState."""
    _filter_name_sql = build_name_filter_sql(f.filter_name)
    _sector_cols = get_sector_columns_sql(f.selected_sector) if f.show_sectores else ""
    _use_unnest = f.show_sectores and bool(f.selected_sector)

    return f"""
    SELECT
        codigoIsin,
        nombre,
        indicadorRiesgo as Risk,
        ter as TER,
        ytd as "{ f.year }",
        { "" if f.show_rentabilidad_anios else "-- " }rentabilidadPasadaUno as "{ f.year - 1 }",
        { "" if f.show_rentabilidad_anios else "-- " }rentabilidadPasadaDos as "{ f.year - 2 }",
        { "" if f.show_rentabilidad_anios else "-- " }rentabilidadPasadaTres as "{ f.year - 3 }",
        { "" if f.show_rentabilidad_anios else "-- " }rentabilidadPasadaCuatro as "{ f.year - 4 }",
        { "" if f.show_rentabilidad_anios else "-- " }rentabilidadPasadaCinco as "{ f.year - 5 }",
        { "" if f.show_rentabilidad_media_135 else "-- " }yearUno as "1Y",
        { "" if f.show_rentabilidad_media_135 else "-- " }yearTres as "3Y",
        { "" if f.show_rentabilidad_media_135 else "-- " }yearCinco as "5Y",
        { "" if f.show_volatilidad else "-- " }volatilidadYearUno as "Vol 1Y",
        { "" if f.show_volatilidad else "-- " }volatilidadYearTres as "Vol 3Y",
        { "" if f.show_volatilidad else "-- " }volatilidadYearCinco as "Vol 5Y",
        { "" if f.show_dias_desplazamiento else "-- " }diasDesplazamientoSuscripcion DiasS, diasDesplazamientoReembolso DiasR,
        { "" if f.show_categories else "-- " }categoria, categoriaMyInvestor, categoriaMstar,
        trackingErrorYearUno as TE_1Y,
        entidadGestora as Gestora,
        divisasDto.codigo AS divisa
        {("," + _sector_cols) if _sector_cols else ""}
    FROM df_productos
        {"LEFT JOIN UNNEST(listaSectores) AS t(s) ON TRUE" if _use_unnest else ""}
    WHERE
        ( {_filter_name_sql} ) -- filtro por nombre/ISIN
        AND ( {f.selected_filter_sql} ) -- filtro rapido
        AND ( {get_filtro_sql("divisa", f.selected_divisa)} ) -- filtro divisa
        AND ( {get_filtro_sql("zonaGeografica", f.selected_zona)} ) -- filtro zona geografica
        AND ( {get_filtro_sql("tipoProductoEnum", f.selected_producto)} ) -- filtro tipo de producto
        AND ( {get_filtro_sql("categoria", f.selected_categoria)} ) -- filtro categoria
        AND ( {get_filtro_sql("categoriaMstar", f.selected_categoria_mstar)} ) -- filtro categoria Morningstar
        AND ( {get_filtro_sql("categoriaMyInvestor", f.selected_categoria_myinvestor)} ) -- filtro categoria MyInvestor
        AND ( {get_filtro_sql("entidadGestora", f.selected_gestora)} ) -- filtro gestora
        AND ( {get_filtro_sql("tipoActivo", f.selected_tipo_activo)} ) -- filtro tipo de activo
        AND ( {get_filtro_sector_sql(f.selected_sector, f.threshold_sector)} ) -- filtro sector
        AND status = 'OPEN'
    { "GROUP BY codigoIsin, nombre, indicadorRiesgo, ter, ytd, rentabilidadPasadaUno, rentabilidadPasadaDos, rentabilidadPasadaTres, rentabilidadPasadaCuatro, rentabilidadPasadaCinco, yearUno, yearTres, yearCinco, volatilidadYearUno, volatilidadYearTres, volatilidadYearCinco, diasDesplazamientoSuscripcion, diasDesplazamientoReembolso, categoria, categoriaMyInvestor, categoriaMstar, trackingErrorYearUno, entidadGestora, divisasDto" if _use_unnest else "" }
    ORDER BY ter ASC, indicadorRiesgo ASC, codigoIsin ASC
    """

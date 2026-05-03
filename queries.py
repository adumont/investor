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

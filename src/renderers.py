import streamlit as st
import pandas as pd
import altair as alt


def to_float(value):
    if isinstance(value, str) and value.endswith("%"):
        value = value[:-1]
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


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


def format_percent_from_decimal(value):
    return f"{value * 100:.2f}%"


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


def render_rentabilidad(producto, year: int):
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
                    alt.value("green"),
                    alt.value("red"),
                ),
                tooltip=["Año", "Rentabilidad"],
            )
            .properties(title="Rentabilidad histórica")
        )
        with cols[0]:
            st.altair_chart(chart, width="stretch")

    # Rentabilidad anual a 1, 3, 5 años + volatilidad overlay
    yoy_data = []
    for (ret_span, vol_span), label in [
        (("yearUno", "volatilidadYearUno"), "1 año"),
        (("yearTres", "volatilidadYearTres"), "3 años"),
        (("yearCinco", "volatilidadYearCinco"), "5 años"),
    ]:
        yoy_data.append((label, producto.get(ret_span), producto.get(vol_span)))
    df_yoy = pd.DataFrame(yoy_data, columns=["Periodo", "Rentabilidad", "Volatilidad"])
    df_yoy = df_yoy.dropna(subset=["Rentabilidad", "Volatilidad"], how="all")
    if not df_yoy.empty:
        base = alt.Chart(df_yoy).encode(
            x=alt.X("Periodo:O", axis=alt.Axis(labelAngle=0))
        )
        bars = base.mark_bar().encode(
            y=alt.Y("Rentabilidad:Q", title="%"),
            color=alt.condition(
                alt.datum.Rentabilidad > 0,
                alt.value("green"),
                alt.value("red"),
            ),
        )
        line = base.mark_line(point=True, color="orange", strokeWidth=2).encode(
            y=alt.Y("Volatilidad:Q", title="%"),
        )
        chart_yoy = (
            alt.layer(bars, line)
            .encode(
                tooltip=[
                    alt.Tooltip("Periodo:N"),
                    alt.Tooltip("Rentabilidad:Q", format=".2f", title="Rentab %"),
                    alt.Tooltip("Volatilidad:Q", format=".2f", title="Vol %"),
                ]
            )
            .properties(title="Rentabilidad anual y Volatilidad a 1, 3, 5 años")
        )
        with cols[1]:
            st.altair_chart(chart_yoy, width="stretch")

    # Disclaimer
    st.markdown(
        "<small>:grey[Rentabilidades pasadas no garantizan rentabilidades futuras. Invertir en fondos conlleva riesgo de pérdida de capital.]</small>",
        unsafe_allow_html=True,
    )

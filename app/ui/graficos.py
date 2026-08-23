"""Gráficas del panel, con la identidad visual de la app (fondo carbón + dorado).

Todas se construyen con Altair y comparten el mismo tema (`_base`), para que ninguna
desentone. Pensadas para leerse en celular: altura corta, sin leyendas que roben ancho,
etiquetas grandes y pocos elementos.

Regla que se sigue en todo el archivo: las gráficas sólo DIBUJAN. Los números ya vienen
calculados por quien llama (el panel), nunca se filtra ni se cuenta aquí -- así no hay
dos sitios distintos decidiendo, por ejemplo, qué cita cuenta como corte realizado.
"""
from __future__ import annotations

import altair as alt
import pandas as pd

from app.ui.tema import (
    BLANCO_CALIDO,
    DORADO,
    DORADO_CLARO,
    GRIS_CALIDO,
    LINEA,
    SUPERFICIE_ALTA,
)

FUENTE = "Oswald, Arial Narrow, sans-serif"


def _base(chart: alt.Chart, alto: int) -> alt.Chart:
    """Fondo transparente y tipografía de la app. El fondo va transparente a propósito:
    así la gráfica se ve dentro de la tarjeta sin un rectángulo de otro color encima."""
    return chart.properties(height=alto, background="transparent").configure_view(
        strokeWidth=0
    ).configure_axis(
        labelFont=FUENTE,
        titleFont=FUENTE,
        labelColor=GRIS_CALIDO,
        titleColor=GRIS_CALIDO,
        labelFontSize=11,
        titleFontSize=11,
        gridColor=LINEA,
        gridOpacity=0.5,
        domainColor=LINEA,
        tickColor=LINEA,
    ).configure_legend(
        labelFont=FUENTE, titleFont=FUENTE, labelColor=GRIS_CALIDO, titleColor=GRIS_CALIDO
    )


def anillo(realizados: int, restantes: int, alto: int = 168) -> alt.LayerChart:
    """Anillo de progreso del día: cuánto de la jornada ya se atendió.

    `restantes` son los espacios que todavía se pueden llenar. Si el día ya se acabó
    (ambos en cero) igual se dibuja el aro vacío, para que la tarjeta no quede en blanco.
    """
    total = realizados + restantes
    datos = pd.DataFrame(
        {
            "categoria": ["Atendidas", "Disponibles"],
            "valor": [realizados, max(restantes, 0)] if total else [0, 1],
            "orden": [0, 1],
        }
    )

    aro = (
        alt.Chart(datos)
        .mark_arc(innerRadius=56, outerRadius=76, cornerRadius=2, stroke=None)
        .encode(
            theta=alt.Theta("valor:Q", stack=True),
            order=alt.Order("orden:Q"),
            color=alt.Color(
                "categoria:N",
                scale=alt.Scale(
                    domain=["Atendidas", "Disponibles"],
                    range=[DORADO, SUPERFICIE_ALTA],
                ),
                legend=None,
            ),
            tooltip=[alt.Tooltip("categoria:N", title=""), alt.Tooltip("valor:Q", title="Citas")],
        )
    )

    centro = (
        alt.Chart(pd.DataFrame({"t": [str(realizados)]}))
        .mark_text(
            font=FUENTE, fontSize=44, fontWeight=600, color=DORADO_CLARO, dy=-6
        )
        .encode(text="t:N")
    )
    pie = (
        alt.Chart(pd.DataFrame({"t": ["CORTES HOY"]}))
        .mark_text(font=FUENTE, fontSize=10, color=GRIS_CALIDO, dy=22)
        .encode(text="t:N")
    )

    return _base(alt.layer(aro, centro, pie), alto)


def barras_cortes(por_dia: pd.DataFrame, alto: int = 190) -> alt.LayerChart:
    """Cortes realizados por día. `por_dia` trae columnas `etiqueta` (texto del eje,
    ya en español) y `cortes`. El día con más cortes se resalta en dorado claro."""
    if por_dia.empty:
        por_dia = pd.DataFrame({"etiqueta": [], "cortes": []})

    maximo = por_dia["cortes"].max() if not por_dia.empty else 0

    barras = (
        alt.Chart(por_dia)
        .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2, width=alt.RelativeBandSize(0.55))
        .encode(
            x=alt.X("etiqueta:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("cortes:Q", title=None, axis=alt.Axis(tickMinStep=1, grid=True)),
            color=alt.condition(
                alt.datum.cortes >= maximo if maximo else alt.datum.cortes < 0,
                alt.value(DORADO_CLARO),
                alt.value(DORADO),
            ),
            tooltip=[
                alt.Tooltip("etiqueta:N", title="Día"),
                alt.Tooltip("cortes:Q", title="Cortes"),
            ],
        )
    )
    cifras = (
        alt.Chart(por_dia)
        .mark_text(font=FUENTE, fontSize=11, color=BLANCO_CALIDO, dy=-8)
        .encode(
            x=alt.X("etiqueta:N", sort=None),
            y=alt.Y("cortes:Q"),
            text=alt.condition(alt.datum.cortes > 0, alt.Text("cortes:Q"), alt.value("")),
        )
    )
    return _base(alt.layer(barras, cifras), alto)


def barras_servicio(sin_barba: int, con_barba: int, alto: int = 96) -> alt.LayerChart:
    """Sin barba vs con barba, en una sola barra horizontal apilada. Ocupa muy poco
    alto -- clave en celular, donde una gráfica de torta obligaría a hacer scroll."""
    total = sin_barba + con_barba
    if not total:
        datos = pd.DataFrame({"tipo": ["Sin datos"], "valor": [1], "pct": [""]})
        barra = (
            alt.Chart(datos)
            .mark_bar(height=26, cornerRadius=2)
            .encode(x=alt.X("valor:Q", title=None, axis=None), color=alt.value(SUPERFICIE_ALTA))
        )
        return _base(alt.layer(barra), alto)

    datos = pd.DataFrame(
        {
            "tipo": ["Sin barba", "Con barba"],
            "valor": [sin_barba, con_barba],
            "orden": [0, 1],
        }
    )
    datos["pct"] = (datos["valor"] / total * 100).round().astype(int).astype(str) + "%"

    barra = (
        alt.Chart(datos)
        .mark_bar(height=30, cornerRadius=2)
        .encode(
            x=alt.X("valor:Q", stack="normalize", title=None, axis=None),
            order=alt.Order("orden:Q"),
            color=alt.Color(
                "tipo:N",
                scale=alt.Scale(domain=["Sin barba", "Con barba"], range=[DORADO, "#4A5058"]),
                legend=alt.Legend(orient="bottom", title=None, direction="horizontal"),
            ),
            tooltip=[
                alt.Tooltip("tipo:N", title=""),
                alt.Tooltip("valor:Q", title="Cortes"),
                alt.Tooltip("pct:N", title="Del total"),
            ],
        )
    )
    textos = (
        alt.Chart(datos)
        .mark_text(font=FUENTE, fontSize=13, fontWeight=600, color="#14100A")
        .encode(
            x=alt.X("valor:Q", stack="normalize", bandPosition=0.5),
            order=alt.Order("orden:Q"),
            text=alt.condition(alt.datum.valor > 0, alt.Text("pct:N"), alt.value("")),
            color=alt.condition(
                alt.datum.tipo == "Sin barba", alt.value("#14100A"), alt.value(BLANCO_CALIDO)
            ),
        )
    )
    return _base(alt.layer(barra, textos), alto)


def barras_libres_vs_ocupadas(
    confirmadas: int, atendidas: int, libres: int, alto: int = 165
) -> alt.LayerChart:
    """Cómo va el día de un vistazo: lo hecho, lo que falta y lo que queda libre.

    Se separan "atendidas" de "confirmadas" en vez de juntarlas en una sola barra
    porque son cosas distintas para el barbero: una ya está cobrada, la otra todavía
    puede caerse.
    """
    datos = pd.DataFrame({
        "estado": ["Atendidas", "Por atender", "Libres"],
        "cantidad": [atendidas, confirmadas, libres],
        "orden": [0, 1, 2],
    })

    barras = (
        alt.Chart(datos)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3,
                  width=alt.RelativeBandSize(0.5))
        .encode(
            x=alt.X("estado:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("cantidad:Q", title=None, axis=alt.Axis(tickMinStep=1)),
            color=alt.Color(
                "estado:N",
                scale=alt.Scale(
                    domain=["Atendidas", "Por atender", "Libres"],
                    range=[DORADO_CLARO, DORADO, SUPERFICIE_ALTA],
                ),
                legend=None,
            ),
            tooltip=[alt.Tooltip("estado:N", title=""), alt.Tooltip("cantidad:Q", title="Citas")],
        )
    )
    cifras = (
        alt.Chart(datos)
        .mark_text(font=FUENTE, fontSize=13, fontWeight=600, color=BLANCO_CALIDO, dy=-9)
        .encode(
            x=alt.X("estado:N", sort=None),
            y=alt.Y("cantidad:Q"),
            text=alt.Text("cantidad:Q"),
        )
    )
    return _base(alt.layer(barras, cifras), alto)


def medidor(porcentaje: float, etiqueta: str, alto: int = 158) -> alt.LayerChart:
    """Anillo con un porcentaje grande en el centro. Para efectividad y ocupación."""
    porcentaje = max(0.0, min(100.0, porcentaje))
    datos = pd.DataFrame({
        "parte": ["Logrado", "Falta"],
        "valor": [porcentaje, 100 - porcentaje],
        "orden": [0, 1],
    })

    aro = (
        alt.Chart(datos)
        .mark_arc(innerRadius=54, outerRadius=72, cornerRadius=2)
        .encode(
            theta=alt.Theta("valor:Q", stack=True),
            order=alt.Order("orden:Q"),
            color=alt.Color(
                "parte:N",
                scale=alt.Scale(domain=["Logrado", "Falta"],
                                range=[DORADO, SUPERFICIE_ALTA]),
                legend=None,
            ),
            tooltip=alt.value(None),
        )
    )
    centro = (
        alt.Chart(pd.DataFrame({"t": [f"{porcentaje:.0f}%"]}))
        .mark_text(font=FUENTE, fontSize=38, fontWeight=600, color=DORADO_CLARO, dy=-4)
        .encode(text="t:N")
    )
    pie = (
        alt.Chart(pd.DataFrame({"t": [etiqueta.upper()]}))
        .mark_text(font=FUENTE, fontSize=9.5, color=GRIS_CALIDO, dy=22)
        .encode(text="t:N")
    )
    return _base(alt.layer(aro, centro, pie), alto)


def linea_por_dia(datos: pd.DataFrame, campo: str, titulo: str,
                  alto: int = 190) -> alt.LayerChart:
    """Línea con el comportamiento día a día. `datos` trae `etiqueta` y el campo pedido.

    El día más alto se marca con un punto grande: es la respuesta a "¿qué día rinde
    más?", que es para lo que se mira esta gráfica.
    """
    if datos.empty:
        datos = pd.DataFrame({"etiqueta": [], campo: []})

    maximo = datos[campo].max() if not datos.empty else 0

    degradado = alt.Gradient(
        gradient="linear",
        stops=[
            alt.GradientStop(color="rgba(201,162,39,0.02)", offset=0),
            alt.GradientStop(color="rgba(201,162,39,0.35)", offset=1),
        ],
        x1=1, x2=1, y1=1, y2=0,
    )
    area = (
        alt.Chart(datos)
        .mark_area(line={"color": DORADO_CLARO, "strokeWidth": 2.5}, color=degradado)
        .encode(
            x=alt.X("etiqueta:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{campo}:Q", title=None, axis=alt.Axis(tickMinStep=1, grid=True)),
            tooltip=[alt.Tooltip("etiqueta:N", title="Día"),
                     alt.Tooltip(f"{campo}:Q", title=titulo)],
        )
    )
    puntos = (
        alt.Chart(datos)
        .mark_point(filled=True, color=DORADO_CLARO)
        .encode(
            x=alt.X("etiqueta:N", sort=None),
            y=alt.Y(f"{campo}:Q"),
            size=alt.condition(
                alt.datum[campo] >= maximo if maximo else alt.datum[campo] < 0,
                alt.value(170), alt.value(55),
            ),
        )
    )
    cifras = (
        alt.Chart(datos)
        .mark_text(font=FUENTE, fontSize=11, color=BLANCO_CALIDO, dy=-14)
        .encode(
            x=alt.X("etiqueta:N", sort=None),
            y=alt.Y(f"{campo}:Q"),
            text=alt.condition(alt.datum[campo] > 0, alt.Text(f"{campo}:Q"), alt.value("")),
        )
    )
    return _base(alt.layer(area, puntos, cifras), alto)


def barras_horizontales(datos: pd.DataFrame, campo_etiqueta: str, campo_valor: str,
                        alto: int = 190) -> alt.LayerChart:
    """Ranking (top de clientes). Horizontal porque los nombres no caben de otra forma
    en la pantalla de un celular."""
    if datos.empty:
        return _base(alt.Chart(pd.DataFrame({"x": [0]})).mark_point(opacity=0), alto)

    barras = (
        alt.Chart(datos)
        .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3, height=22)
        .encode(
            y=alt.Y(f"{campo_etiqueta}:N", sort=None, title=None),
            x=alt.X(f"{campo_valor}:Q", title=None, axis=alt.Axis(tickMinStep=1)),
            color=alt.value(DORADO),
            tooltip=[alt.Tooltip(f"{campo_etiqueta}:N", title=""),
                     alt.Tooltip(f"{campo_valor}:Q", title="Cortes")],
        )
    )
    cifras = (
        alt.Chart(datos)
        .mark_text(font=FUENTE, fontSize=12, color=BLANCO_CALIDO, dx=11)
        .encode(
            y=alt.Y(f"{campo_etiqueta}:N", sort=None),
            x=alt.X(f"{campo_valor}:Q"),
            text=alt.Text(f"{campo_valor}:Q"),
        )
    )
    return _base(alt.layer(barras, cifras), alto)


def area_ingresos(por_dia: pd.DataFrame, alto: int = 150) -> alt.LayerChart:
    """Ingresos por día, en área con degradado. `por_dia`: columnas `etiqueta` e
    `ingresos`."""
    if por_dia.empty:
        por_dia = pd.DataFrame({"etiqueta": [], "ingresos": []})

    degradado = alt.Gradient(
        gradient="linear",
        stops=[
            alt.GradientStop(color="rgba(201,162,39,0.02)", offset=0),
            alt.GradientStop(color="rgba(201,162,39,0.42)", offset=1),
        ],
        x1=1, x2=1, y1=1, y2=0,
    )

    area = (
        alt.Chart(por_dia)
        .mark_area(line={"color": DORADO_CLARO, "strokeWidth": 2}, color=degradado)
        .encode(
            x=alt.X("etiqueta:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("ingresos:Q", title=None, axis=alt.Axis(format="~s", grid=True)),
            tooltip=[
                alt.Tooltip("etiqueta:N", title="Día"),
                alt.Tooltip("ingresos:Q", title="Ingresos", format=",.0f"),
            ],
        )
    )
    puntos = (
        alt.Chart(por_dia)
        .mark_point(size=52, filled=True, color=DORADO_CLARO)
        .encode(x=alt.X("etiqueta:N", sort=None), y=alt.Y("ingresos:Q"))
    )
    return _base(alt.layer(area, puntos), alto)

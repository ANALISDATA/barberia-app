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

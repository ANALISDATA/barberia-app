"""Historial: quién viene, cuándo se vende más y cómo va el negocio en el tiempo.

Filtra por día, semana o mes. A diferencia de los otros dos tableros -- que responden
"cómo voy ahora" -- este responde "cómo me ha ido", que es otra pregunta y por eso está
en su propia página.
"""
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from app import catalogo, db
from app.indicadores import (
    clientes_nuevos,
    mejor_dia,
    por_dia,
    resumir,
    semana_de,
    top_clientes,
)
from app.ui import graficos, menu, tema
from config import NOMBRES_DIA, ZONA_HORARIA, fecha_larga

PERIODOS = ["Hoy", "Esta semana", "Este mes", "Todo"]


def _pesos(valor: int) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def render():
    tema.aplicar()

    if not st.session_state.get("admin_autenticado"):
        st.warning("Necesitas iniciar sesión para ver el panel.")
        st.link_button("Ir a iniciar sesión", "/admin", width="stretch")
        return

    menu.pintar("historial")

    if not db.disponible():
        st.warning("No hay conexión con Supabase.")
        return

    hoy = datetime.now(ZONA_HORARIA).date()

    tema.saludo("Historial", "Cómo te ha ido")

    periodo = st.segmented_control(
        "Periodo", options=PERIODOS, default="Este mes",
        key="periodo_historial", label_visibility="collapsed", width="stretch",
    ) or "Este mes"

    desde, hasta, titulo = _rango_del_periodo(periodo, hoy)
    st.caption(f"Mostrando: **{titulo}**")

    citas = db.obtener_citas_con_cliente(desde, hasta)
    r = resumir(citas)

    if not r.atendidas:
        tema.aviso_vacio("Todavía no hay cortes atendidos en este periodo.")
        tema.pie_de_pagina(db.obtener_negocio())
        return

    _resumen(r, desde, hasta, periodo)
    _top_clientes(citas, desde)
    _mejores_dias(citas, desde, hasta, periodo)
    _servicios(r)

    tema.pie_de_pagina(db.obtener_negocio())


def _rango_del_periodo(periodo, hoy):
    if periodo == "Hoy":
        return hoy, hoy, fecha_larga(hoy)
    if periodo == "Esta semana":
        lunes, domingo = semana_de(hoy)
        return lunes, domingo, f"semana del {lunes.strftime('%d/%m')} al {domingo.strftime('%d/%m')}"
    if periodo == "Este mes":
        primero = hoy.replace(day=1)
        return primero, hoy, f"del 1 al {hoy.day} de este mes"
    # Todo: desde bien atrás. La barbería no tiene años de historia, con esto sobra.
    return hoy - timedelta(days=730), hoy, "todo el historial"


def _resumen(r, desde, hasta, periodo):
    tema.seccion("Lo que llevas", eyebrow=periodo, compacta=True)

    tema.grid_metricas([
        ("Cortes", str(r.atendidas), "oro"),
        ("Ingresos", _pesos(r.ingresos), "oro"),
        ("Promedio por corte", _pesos(r.ticket_promedio), ""),
        ("Efectividad", f"{r.efectividad:.0f}%", ""),
        ("Canceladas", str(r.canceladas), "" if r.canceladas else "apagada"),
        ("No asistieron", str(r.no_asistieron), "" if r.no_asistieron else "apagada"),
    ])


def _top_clientes(citas, desde):
    tema.seccion("Tus mejores clientes", eyebrow="Top 5", compacta=True)

    top = top_clientes(citas, cuantos=5)
    if not top:
        tema.aviso_vacio("Sin clientes atendidos en este periodo.")
        return

    tabla = pd.DataFrame({
        "cliente": [c.nombre for c in top],
        "cortes": [c.cortes for c in top],
    })
    with tema.panel("Quién viene más"):
        st.altair_chart(
            graficos.barras_horizontales(tabla, "cliente", "cortes"), width="stretch"
        )

    for c in top:
        ultima = c.ultima_visita.strftime("%d/%m") if c.ultima_visita else "—"
        servicio = catalogo.nombres_servicios().get(c.ultimo_servicio, c.ultimo_servicio)
        tema.fila_cita(
            str(c.cortes),
            c.nombre,
            f"{c.telefono} · última: {ultima} · {servicio} · {_pesos(c.gastado)}",
        )

    nuevos = clientes_nuevos(citas, desde)
    if nuevos:
        st.caption(f"**{nuevos}** cliente(s) vinieron por primera vez en este periodo.")


def _mejores_dias(citas, desde, hasta, periodo):
    tema.seccion("Cuándo se vende más", eyebrow="Por día", compacta=True)

    mejor = mejor_dia(citas, desde, hasta)
    if mejor:
        dia, resumen_dia = mejor
        st.markdown(
            f'<div class="tarjeta-dorada" style="text-align:center;">'
            f'<div class="etiqueta">Tu mejor día</div>'
            f'<div class="valor-grande" style="font-size:34px;">'
            f'{NOMBRES_DIA[dia.weekday()]} {dia.strftime("%d/%m")}</div>'
            f'<div class="etiqueta" style="margin-top:6px;">'
            f'{resumen_dia.atendidas} cortes · {_pesos(resumen_dia.ingresos)}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )

    # Qué día de la SEMANA rinde más en promedio: dice qué día conviene tener refuerzo
    # o cuál se puede usar para descansar. Es distinto del mejor día suelto.
    acumulado = {i: {"cortes": 0, "ingresos": 0, "veces": 0} for i in range(7)}
    for dia, resumen_dia in por_dia(citas, desde, hasta):
        d = acumulado[dia.weekday()]
        d["cortes"] += resumen_dia.atendidas
        d["ingresos"] += resumen_dia.ingresos
        d["veces"] += 1

    tabla = pd.DataFrame({
        "etiqueta": [NOMBRES_DIA[i][:3] for i in range(7)],
        "cortes": [acumulado[i]["cortes"] for i in range(7)],
    })
    if tabla["cortes"].sum():
        with tema.panel("Cortes por día de la semana"):
            st.altair_chart(
                graficos.linea_por_dia(tabla, "cortes", "Cortes"), width="stretch"
            )
        mejor_semanal = max(range(7), key=lambda i: acumulado[i]["cortes"])
        peor = min(
            (i for i in range(7) if acumulado[i]["veces"]),
            key=lambda i: acumulado[i]["cortes"],
        )
        st.caption(
            f"El día que más rinde es el **{NOMBRES_DIA[mejor_semanal].lower()}** "
            f"({acumulado[mejor_semanal]['cortes']} cortes en total). El más flojo, el "
            f"**{NOMBRES_DIA[peor].lower()}** ({acumulado[peor]['cortes']})."
        )


def _servicios(r):
    tema.seccion("Qué te piden más", eyebrow="Tipo de corte", compacta=True)
    with tema.panel("Sin barba vs con barba"):
        st.altair_chart(
            graficos.barras_servicio(r.sin_barba, r.con_barba), width="stretch"
        )


render()

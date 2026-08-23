"""Tablero del comportamiento diario: cómo va HOY.

Página aparte y no mezclada con la agenda: en un celular, meter la agenda y todos los
indicadores en la misma pantalla obliga a un scroll larguísimo para encontrar un dato.
Aquí sólo van números del día.
"""
from datetime import datetime, time

import streamlit as st

from app import catalogo, db, horarios, margen
from app.disponibilidad import analizar_jornada
from app.indicadores import resumir
from app.ui import graficos, menu, tema
from config import ZONA_HORARIA, fecha_larga


def _pesos(valor: int) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def render():
    tema.aplicar()

    if not st.session_state.get("admin_autenticado"):
        st.warning("Necesitas iniciar sesión para ver el panel.")
        st.link_button("Ir a iniciar sesión", "/admin", width="stretch")
        return

    menu.pintar("dia")

    if not db.disponible():
        st.warning("No hay conexión con Supabase.")
        return

    ahora = datetime.now(ZONA_HORARIA)
    hoy = ahora.date()

    horario = db.obtener_horario_semanal()
    descansos = db.obtener_descansos()
    excepciones = db.obtener_excepciones(hoy, hoy)
    duracion = catalogo.duracion_mas_larga()
    citas = db.obtener_citas_del_dia(hoy)

    r = resumir(citas)

    ocupadas = [
        (time.fromisoformat(c["start_time"]), time.fromisoformat(c["end_time"]))
        for c in citas
        if c["status"] != "cancelada"
    ]
    libres = horarios.libres(
        hoy, horario, descansos, excepciones, ocupadas, ahora=ahora,
        duracion=duracion, tolerancia=margen.minutos(),
    )
    bloques, _ = analizar_jornada(hoy, horario, descansos, excepciones, duracion)
    espacios_del_dia = len(bloques)

    tema.saludo("Hoy", fecha_larga(hoy))

    if not espacios_del_dia:
        tema.aviso_vacio("Hoy la barbería no abre.")
        return

    # ---- Lo primero: la plata ----
    st.markdown(
        f'<div class="tarjeta-dorada" style="text-align:center;">'
        f'<div class="etiqueta">Llevas hoy</div>'
        f'<div class="valor-grande" style="font-size:48px;">{_pesos(r.ingresos)}</div>'
        f'<div class="etiqueta" style="margin-top:6px;">'
        f'{r.atendidas} corte{"s" if r.atendidas != 1 else ""} realizado'
        f'{"s" if r.atendidas != 1 else ""}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # ---- Cómo va la agenda ----
    tema.seccion("La agenda de hoy", eyebrow=f"{espacios_del_dia} cortes caben", compacta=True)
    with tema.panel("Ocupado y libre"):
        st.altair_chart(
            graficos.barras_libres_vs_ocupadas(r.confirmadas, r.atendidas, len(libres)),
            width="stretch",
        )

    tema.grid_metricas([
        ("Por atender", str(r.confirmadas), "oro" if r.confirmadas else ""),
        ("Libres ahora", str(len(libres)), ""),
        ("Canceladas", str(r.canceladas), "" if r.canceladas else "apagada"),
        ("No asistieron", str(r.no_asistieron), "" if r.no_asistieron else "apagada"),
    ])

    # ---- Los dos porcentajes ----
    tema.seccion("Qué tan lleno y qué tan cumplido", eyebrow="Porcentajes", compacta=True)

    ocupacion = r.ocupacion_sobre(espacios_del_dia)
    col_a, col_b = st.columns(2)
    with col_a:
        with tema.panel("Agenda ocupada"):
            st.altair_chart(graficos.medidor(ocupacion, "de tu día"), width="stretch")
    with col_b:
        with tema.panel("Efectividad"):
            st.altair_chart(graficos.medidor(r.efectividad, "ya atendidas"), width="stretch")

    st.caption(
        f"**Agenda ocupada:** de los {espacios_del_dia} cortes que caben hoy, tienes "
        f"{r.agendadas} con cita ({ocupacion:.0f}%)."
    )
    st.caption(
        f"**Efectividad:** de esas {r.agendadas}, ya atendiste {r.atendidas} "
        f"({r.efectividad:.0f}%)."
        + (f" {r.no_asistieron} no llegaron." if r.no_asistieron else "")
    )

    # ---- Detalle del dinero ----
    if r.atendidas:
        tema.seccion("El dinero de hoy", eyebrow="Sólo citas atendidas", compacta=True)
        tema.grid_metricas([
            ("Total", _pesos(r.ingresos), "oro"),
            ("Promedio por corte", _pesos(r.ticket_promedio), ""),
            ("Sin barba", str(r.sin_barba), ""),
            ("Con barba", str(r.con_barba), ""),
        ])

    tema.pie_de_pagina(db.obtener_negocio())


render()

"""Comportamiento de la SEMANA, contado como una historia.

La semana va de lunes a domingo. El domingo es el día libre del barbero: es cuando
revisa cómo le fue y cierra sus cuentas. Por eso sólo se ve la semana en curso -- para
pasar a la siguiente hay que cerrar la actual, que guarda cómo quedó.

El orden de la página es deliberado: primero el titular (cuánto se hizo), después el
detalle, después qué día rindió más, y al final el cierre. Se lee de arriba abajo como
un resumen, no como una tabla de datos sueltos.
"""
from datetime import datetime

import pandas as pd
import streamlit as st

from app import catalogo, db, horarios, margen
from app.indicadores import mejor_dia, por_dia, resumir, semana_de
from app.ui import graficos, menu, tema
from config import NOMBRES_DIA, ZONA_HORARIA


def _pesos(valor: int) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def _rango(lunes, domingo) -> str:
    return f"{lunes.strftime('%d/%m')} — {domingo.strftime('%d/%m')}"


def render():
    tema.aplicar()

    if not st.session_state.get("admin_autenticado"):
        st.warning("Necesitas iniciar sesión para ver el panel.")
        st.link_button("Ir a iniciar sesión", "/admin", width="stretch")
        return

    menu.pintar("semana")

    if not db.disponible():
        st.warning("No hay conexión con Supabase.")
        return

    hoy = datetime.now(ZONA_HORARIA).date()
    lunes, domingo = semana_de(hoy)

    citas = db.obtener_citas_rango(lunes, domingo)
    r = resumir(citas)
    dias = por_dia(citas, lunes, domingo)

    tema.saludo("Esta semana", _rango(lunes, domingo))

    _titular(r, hoy, lunes)
    _detalle(r, lunes, domingo, dias)
    _grafica_por_dia(dias, citas, lunes, domingo)
    _cierre(lunes, domingo, r, hoy)

    tema.pie_de_pagina(db.obtener_negocio())


def _titular(r, hoy, lunes):
    """Lo primero y más grande: cuánto llevas. Todo lo demás explica este número."""
    dias_corridos = (hoy - lunes).days + 1
    st.markdown(
        f'<div class="tarjeta-dorada" style="text-align:center;">'
        f'<div class="etiqueta">Llevas esta semana</div>'
        f'<div class="valor-grande" style="font-size:48px;">{_pesos(r.ingresos)}</div>'
        f'<div class="etiqueta" style="margin-top:6px;">'
        f'{r.atendidas} corte{"s" if r.atendidas != 1 else ""} en {dias_corridos} '
        f'día{"s" if dias_corridos != 1 else ""}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    if r.atendidas:
        promedio = r.atendidas / dias_corridos
        st.caption(
            f"Vas a un ritmo de **{promedio:.1f} cortes por día** y "
            f"**{_pesos(r.ticket_promedio)}** por corte."
        )


def _detalle(r, lunes, domingo, dias):
    tema.seccion("Cómo va la semana", eyebrow="Números", compacta=True)

    # Cuántos cortes cabían en los días que ya pasaron: es contra eso que tiene sentido
    # medir qué tan llena estuvo la agenda.
    horario = db.obtener_horario_semanal()
    descansos = db.obtener_descansos()
    excepciones = db.obtener_excepciones(lunes, domingo)
    duracion = catalogo.duracion_mas_larga()
    hoy = datetime.now(ZONA_HORARIA).date()
    espacios = 0
    for dia, _ in dias:
        if dia > hoy:
            continue
        espacios += horarios.capacidad(
            dia, horario, descansos, excepciones, duracion, margen.minutos()
        )

    ocupacion = r.ocupacion_sobre(espacios)

    col_a, col_b = st.columns(2)
    with col_a:
        with tema.panel("Agenda ocupada"):
            st.altair_chart(graficos.medidor(ocupacion, "de la semana"), width="stretch")
    with col_b:
        with tema.panel("Efectividad"):
            st.altair_chart(graficos.medidor(r.efectividad, "ya atendidas"), width="stretch")

    st.caption(
        f"De los **{espacios} cortes** que cabían en los días que ya pasaron, se "
        f"agendaron **{r.agendadas}**. De esos, ya atendiste **{r.atendidas}**."
    )

    tema.grid_metricas([
        ("Cortes", str(r.atendidas), "oro"),
        ("Ingresos", _pesos(r.ingresos), "oro"),
        ("Por atender", str(r.confirmadas), ""),
        ("Canceladas", str(r.canceladas), "" if r.canceladas else "apagada"),
        ("No asistieron", str(r.no_asistieron), "" if r.no_asistieron else "apagada"),
        ("Sin barba / Con barba", f"{r.sin_barba} / {r.con_barba}", ""),
    ])


def _grafica_por_dia(dias, citas, lunes, domingo):
    tema.seccion("Qué día rinde más", eyebrow="Día por día", compacta=True)

    tabla = pd.DataFrame({
        "etiqueta": [NOMBRES_DIA[d.weekday()][:3] for d, _ in dias],
        "cortes": [x.atendidas for _, x in dias],
        "ingresos": [x.ingresos for _, x in dias],
    })

    with tema.panel("Cortes por día"):
        st.altair_chart(
            graficos.linea_por_dia(tabla[["etiqueta", "cortes"]], "cortes", "Cortes"),
            width="stretch",
        )

    mejor = mejor_dia(citas, lunes, domingo)
    if mejor:
        dia, resumen_dia = mejor
        st.caption(
            f"Tu mejor día fue el **{NOMBRES_DIA[dia.weekday()].lower()} "
            f"{dia.strftime('%d/%m')}** con **{resumen_dia.atendidas} cortes** y "
            f"**{_pesos(resumen_dia.ingresos)}**."
        )
        flojos = [d for d, x in dias if x.atendidas == 0 and d <= datetime.now(ZONA_HORARIA).date()]
        if flojos:
            nombres = ", ".join(NOMBRES_DIA[d.weekday()].lower() for d in flojos)
            st.caption(f"Sin ningún corte: {nombres}.")
    else:
        st.caption("Todavía no hay cortes atendidos esta semana.")

    with tema.panel("Ingresos por día"):
        st.altair_chart(
            graficos.area_ingresos(tabla[["etiqueta", "ingresos"]]), width="stretch"
        )


def _cierre(lunes, domingo, r, hoy):
    tema.seccion("Cerrar la semana", eyebrow="Domingo", compacta=True)

    # Sin la tabla no se puede cerrar, pero el resto de la página sí sirve: se avisa y
    # se sigue, en vez de tumbar la página entera por un paso de instalación pendiente.
    if not db.hay_tabla_cierres():
        st.info(
            "Para poder cerrar semanas falta un paso de una sola vez: crear la tabla "
            "en Supabase con el archivo `supabase/002_cierres_semana.sql`."
        )
        return

    if db.semana_esta_cerrada(lunes):
        st.success("Esta semana ya está cerrada.")
        _historial_de_cierres()
        return

    faltan = (domingo - hoy).days
    if faltan > 0:
        st.info(
            f"La semana se cierra el domingo {domingo.strftime('%d/%m')}. "
            f"Faltan {faltan} día{'s' if faltan != 1 else ''}."
        )
        st.caption(
            "Puedes cerrarla antes si quieres, pero lo que quede sin marcar como "
            "atendido no contará."
        )

    pendientes = r.confirmadas
    if pendientes:
        st.warning(
            f"Tienes **{pendientes} cita(s) sin marcar** como atendida o no asistió. "
            "Si cierras ahora, no van a contar en el cierre."
        )

    if st.button("Cerrar la semana y pasar a la siguiente", type="primary", width="stretch"):
        try:
            db.cerrar_semana(lunes, domingo, {
                "cortes": r.atendidas,
                "ingresos": r.ingresos,
                "citas_totales": r.agendadas,
                "canceladas": r.canceladas,
                "no_asistieron": r.no_asistieron,
                "sin_barba": r.sin_barba,
                "con_barba": r.con_barba,
            })
        except db.SemanaYaCerrada:
            st.error("Esa semana ya estaba cerrada.")
            return
        except Exception as err:
            # El caso típico: falta correr supabase/002_cierres_semana.sql.
            st.error(
                "No se pudo guardar el cierre. Si es la primera vez, falta crear la "
                "tabla en Supabase (archivo `supabase/002_cierres_semana.sql`)."
            )
            st.caption(f"Detalle técnico: {err}")
            return
        st.success(f"Semana {_rango(lunes, domingo)} cerrada.")
        st.rerun()

    _historial_de_cierres()


def _historial_de_cierres():
    try:
        cierres = db.obtener_cierres()
    except Exception:
        return
    if not cierres:
        return

    with st.expander(f"Ver las {len(cierres)} semanas cerradas"):
        for c in cierres:
            inicio = c["semana_inicio"][8:10] + "/" + c["semana_inicio"][5:7]
            fin = c["semana_fin"][8:10] + "/" + c["semana_fin"][5:7]
            tema.fila_cita(
                f"{inicio}",
                f"Semana {inicio} — {fin}",
                f'{c["cortes"]} cortes · {_pesos(c["ingresos"])}',
            )


render()

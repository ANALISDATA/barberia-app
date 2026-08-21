"""Configuración del negocio: horario, descansos, duración de la cita y precios.

Todo lo que antes había que cambiar entrando a Supabase se hace desde aquí.

Cada bloque guarda por separado (su propio botón) en vez de tener un único "Guardar"
al final: así se puede tocar el horario del martes sin miedo a arrastrar sin querer un
cambio a medio hacer en los precios.
"""
from datetime import time

import streamlit as st

from app import db
from app.ui import tema
from config import NOMBRES_DIA, NOMBRES_SERVICIO

# Duraciones ofrecidas. Se listan en vez de dejar un campo libre para que no se cuelen
# valores absurdos (0 minutos, 7 horas) que romperían la agenda sin explicación.
DURACIONES = [15, 20, 30, 40, 45, 50, 60, 75, 90]

HORAS = [time(h, m) for h in range(5, 24) for m in (0, 15, 30, 45)]


def _fmt(t: time) -> str:
    return t.strftime("%I:%M %p").lstrip("0").replace("AM", "a.m.").replace("PM", "p.m.")


def render():
    tema.aplicar()

    if not st.session_state.get("admin_autenticado"):
        st.warning("Entra al panel primero.")
        st.link_button("Ir al panel", "/admin", width="stretch")
        return

    if not db.disponible():
        st.warning("No hay conexión con Supabase.")
        return

    tema.saludo("Configuración", "Ajusta tu barbería a tu medida")

    _bloque_duracion()
    _bloque_precios()
    _bloque_horario()
    _bloque_negocio()

    st.divider()
    # Igual que en el panel: navegación interna para no perder la sesión al recargar.
    if st.button("← Volver al panel", width="stretch"):
        from app.navegacion import admin_inicio

        st.switch_page(admin_inicio)
    tema.pie_de_pagina(db.obtener_negocio())


def _bloque_duracion():
    tema.seccion("Duración de la cita", eyebrow="Cada cuánto atiendes", compacta=True)

    actual = db.obtener_duracion_cita()
    indice = DURACIONES.index(actual) if actual in DURACIONES else DURACIONES.index(45)

    minutos = st.selectbox(
        "Minutos por cita",
        options=DURACIONES,
        index=indice,
        format_func=lambda m: f"{m} minutos",
    )
    st.caption(
        "Con este valor se arma toda la agenda. Si lo cambias, las horas disponibles "
        "se recalculan solas; las citas ya reservadas no se tocan."
    )
    if st.button("Guardar duración", type="primary", width="stretch"):
        db.guardar_duracion_cita(int(minutos))
        st.success(f"Listo: las citas ahora duran {minutos} minutos.")
        st.rerun()


def _bloque_precios():
    tema.seccion("Precios", eyebrow="Valor de referencia", compacta=True)

    servicios = {s["type"]: s for s in db.obtener_servicios()}
    nuevos = {}
    for tipo, servicio in servicios.items():
        nuevos[tipo] = st.number_input(
            NOMBRES_SERVICIO.get(tipo, tipo),
            min_value=0,
            step=1000,
            value=int(servicio["price"]),
            key=f"precio_{tipo}",
        )
    st.caption(
        "Es el valor con el que se guarda cada cita nueva. Como no le cobras lo mismo "
        "a todo el mundo, puedes ajustar cita por cita desde el consolidado del panel."
    )
    if st.button("Guardar precios", type="primary", width="stretch"):
        for tipo, precio in nuevos.items():
            db.guardar_precio_servicio(tipo, int(precio))
        st.success("Precios actualizados.")
        st.rerun()


def _bloque_horario():
    tema.seccion("Horario y descansos", eyebrow="Día por día", compacta=True)

    horario = db.obtener_horario_semanal()
    descansos = db.obtener_descansos()

    for dia in range(7):
        abierto = horario.get(dia) is not None
        inicio, fin = horario.get(dia) or (time(7, 0), time(20, 0))
        lista_descansos = descansos.get(dia, [])

        resumen = (
            f"{_fmt(inicio)} – {_fmt(fin)}"
            + (f" · {len(lista_descansos)} descanso(s)" if lista_descansos else "")
            if abierto
            else "Cerrado"
        )
        with st.expander(f"{NOMBRES_DIA[dia]} — {resumen}"):
            _editor_dia(dia, abierto, inicio, fin, lista_descansos)


def _editor_dia(dia, abierto, inicio, fin, lista_descansos):
    activo = st.toggle("Abierto este día", value=abierto, key=f"abre_{dia}")

    col_a, col_b = st.columns(2)
    nuevo_inicio = col_a.selectbox(
        "Abre a las", HORAS, index=HORAS.index(inicio) if inicio in HORAS else 8,
        format_func=_fmt, key=f"ini_{dia}", disabled=not activo,
    )
    nuevo_fin = col_b.selectbox(
        "Cierra a las", HORAS, index=HORAS.index(fin) if fin in HORAS else 60,
        format_func=_fmt, key=f"fin_{dia}", disabled=not activo,
    )

    st.markdown("**Descansos**")
    st.caption("Almuerzo, una vuelta, lo que necesites. Puedes poner varios.")

    # Cuántas filas de descanso mostrar. Vive en session_state para que el botón
    # "Agregar descanso" pueda añadir una fila sin perder lo ya escrito.
    clave_n = f"n_desc_{dia}"
    if clave_n not in st.session_state:
        st.session_state[clave_n] = max(len(lista_descansos), 1)

    nuevos_descansos = []
    for i in range(st.session_state[clave_n]):
        actual = lista_descansos[i] if i < len(lista_descansos) else None
        c1, c2 = st.columns(2)
        d_ini = c1.selectbox(
            f"Desde ({i + 1})", [None] + HORAS,
            index=(HORAS.index(actual[0]) + 1) if actual else 0,
            format_func=lambda t: "—" if t is None else _fmt(t),
            key=f"di_{dia}_{i}", disabled=not activo,
        )
        d_fin = c2.selectbox(
            f"Hasta ({i + 1})", [None] + HORAS,
            index=(HORAS.index(actual[1]) + 1) if actual else 0,
            format_func=lambda t: "—" if t is None else _fmt(t),
            key=f"df_{dia}_{i}", disabled=not activo,
        )
        if d_ini and d_fin:
            nuevos_descansos.append((d_ini, d_fin))

    if st.button("＋ Agregar otro descanso", key=f"add_{dia}", width="stretch"):
        st.session_state[clave_n] += 1
        st.rerun()

    if st.button(f"Guardar {NOMBRES_DIA[dia].lower()}", type="primary",
                 key=f"save_{dia}", width="stretch"):
        if activo and nuevo_inicio >= nuevo_fin:
            st.error("La hora de cierre tiene que ser posterior a la de apertura.")
            return
        for d_ini, d_fin in nuevos_descansos:
            if d_ini >= d_fin:
                st.error(f"El descanso {_fmt(d_ini)} – {_fmt(d_fin)} está al revés.")
                return
            if activo and (d_ini < nuevo_inicio or d_fin > nuevo_fin):
                st.error(
                    f"El descanso {_fmt(d_ini)} – {_fmt(d_fin)} se sale del horario "
                    "de ese día."
                )
                return

        db.guardar_horario_dia(dia, nuevo_inicio, nuevo_fin, activo)
        db.guardar_descansos_dia(dia, nuevos_descansos)
        st.session_state.pop(clave_n, None)
        st.success(f"{NOMBRES_DIA[dia]} actualizado.")
        st.rerun()


def _bloque_negocio():
    tema.seccion("Datos del negocio", eyebrow="Lo que ve el cliente", compacta=True)

    negocio = db.obtener_negocio()
    nombre = st.text_input("Nombre", value=negocio.get("name") or "")
    descripcion = st.text_area(
        "Frase de la portada", value=negocio.get("description") or "", height=80
    )
    direccion = st.text_input("Dirección", value=negocio.get("address") or "")
    st.caption("La dirección es la que abre Waze, escríbela como la buscarías ahí.")
    telefono = st.text_input("Teléfono / WhatsApp", value=negocio.get("phone") or "")

    col_a, col_b = st.columns(2)
    llegar = col_a.number_input(
        "Llegar antes (minutos)", min_value=0, max_value=60,
        value=int(negocio.get("arrive_minutes_before") or 10),
    )
    cancelar = col_b.number_input(
        "Cancelar con (horas)", min_value=0, max_value=48,
        value=int(negocio.get("cancellation_hours") or 3),
    )

    if st.button("Guardar datos", type="primary", width="stretch"):
        db.guardar_datos_negocio({
            "name": nombre.strip(),
            "description": descripcion.strip(),
            "address": direccion.strip(),
            "phone": telefono.strip(),
            "arrive_minutes_before": int(llegar),
            "cancellation_hours": int(cancelar),
        })
        st.success("Datos actualizados.")
        st.rerun()


render()

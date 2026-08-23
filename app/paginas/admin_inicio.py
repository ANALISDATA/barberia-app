"""AGENDA del administrador: a quién atiendo y qué huecos me quedan.

Esta página es sólo operativa. Los indicadores viven en sus propias páginas (Hoy,
Semana, Historial) porque en un celular tenerlo todo junto obliga a un scroll larguísimo
para encontrar un dato, y casi nunca se necesita la agenda y las estadísticas a la vez.

Regla que se repite en todo el archivo: los cortes realizados y los ingresos SÓLO cuentan
citas en estado 'atendida'. Confirmada, cancelada y no_asistio nunca suman.
"""
from datetime import datetime, time, timedelta

import streamlit as st

from app import db
from app.disponibilidad import (
    analizar_jornada,
    descansos_efectivos,
    horarios_disponibles,
    proximo_espacio,
)
from app.ui import menu, tema
from config import NOMBRES_DIA, NOMBRES_SERVICIO, ZONA_HORARIA, fecha_larga


def _pesos(valor: int) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def _hora_bonita(t) -> str:
    return t.strftime("%I:%M %p").lstrip("0").replace("AM", "a.m.").replace("PM", "p.m.")


def render():
    tema.aplicar()

    # Segunda cerradura. La primera es que esta página ni siquiera se registra para
    # quien no ha iniciado sesión (ver Aplicacion.py), así que entrar a /panel sin
    # clave da "Page not found" -- comprobado en el navegador. Pero esa protección
    # depende de una sola línea: si un día alguien cambia esa lista sin darse cuenta,
    # el panel quedaría abierto sin que nada avise. Esta comprobación lo impide.
    if not st.session_state.get("admin_autenticado"):
        st.warning("Necesitas iniciar sesión para ver el panel.")
        st.link_button("Ir a iniciar sesión", "/admin", width="stretch")
        return

    menu.pintar("panel")

    if not db.disponible():
        st.warning(
            "Todavía no hay conexión con Supabase. Corre **Conectar_Supabase.py** "
            "para dejarla lista."
        )
        return

    ahora = datetime.now(ZONA_HORARIA)
    hoy = ahora.date()

    horario_semanal = db.obtener_horario_semanal()
    descansos = db.obtener_descansos()
    excepciones = db.obtener_excepciones(hoy, hoy)
    citas_hoy = db.obtener_citas_del_dia(hoy)
    duracion = db.obtener_duracion_cita()

    ocupadas = [
        (time.fromisoformat(c["start_time"]), time.fromisoformat(c["end_time"]))
        for c in citas_hoy
        if c["status"] != "cancelada"
    ]
    libres = horarios_disponibles(
        hoy, horario_semanal, descansos, excepciones, ocupadas,
        ahora=ahora, duracion=duracion,
    )
    siguiente = proximo_espacio(
        hoy, horario_semanal, descansos, excepciones, ocupadas,
        ahora=ahora, duracion=duracion,
    )

    saludo = (
        "Buenos días" if ahora.hour < 12 else
        "Buenas tardes" if ahora.hour < 19 else "Buenas noches"
    )
    tema.saludo(f"{saludo} 👋", fecha_larga(hoy))

    # Esta página es SÓLO la agenda. Los indicadores viven en sus propias páginas
    # (Hoy, Semana, Historial): en un celular, tenerlo todo junto obliga a un scroll
    # larguísimo para encontrar un dato.
    _bloque_proximo_espacio(siguiente, libres, duracion)
    _bloque_agenda(hoy, ahora, horario_semanal, descansos, excepciones, duracion)

    st.divider()
    if st.button("Cerrar sesión", width="stretch"):
        st.session_state["admin_autenticado"] = False
        st.rerun()
    tema.pie_de_pagina(db.obtener_negocio())


# ---------------------------------------------------------------------------
# Bloques del panel
# ---------------------------------------------------------------------------

def _bloque_proximo_espacio(siguiente, libres, duracion):
    tema.seccion("Próximo espacio", eyebrow="Disponible ahora", compacta=True)

    if not siguiente:
        tema.aviso_vacio("No quedan espacios libres hoy.")
        return

    st.markdown(
        f'<div class="tarjeta-dorada" style="text-align:center;">'
        f'<div class="etiqueta">Libre · {duracion} minutos</div>'
        f'<div class="valor-grande" style="font-size:46px;">{_hora_bonita(siguiente.inicio)}</div>'
        f'<div class="etiqueta" style="margin-top:8px;">'
        f'{len(libres)} espacio{"s" if len(libres) != 1 else ""} libre{"s" if len(libres) != 1 else ""} hoy</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    # Manda a la tabla de disponibles con el formulario de ESA hora ya abierto, en vez
    # de a un formulario suelto al final de la página.
    from datetime import date as _date

    if st.button("＋ Crear cita en este espacio", type="primary", width="stretch"):
        st.session_state["vista_agenda"] = "disponibles"
        st.session_state["agendando_en"] = f"{_date.today()}_{siguiente.inicio}"
        st.rerun()


def _bloque_agenda(hoy, ahora, horario_semanal, descansos, excepciones, duracion):
    """Agenda del día en DOS tablas separadas: lo reservado y lo que queda libre.

    Van separadas a propósito (y no en una sola lista mezclada) porque casi nunca se
    necesitan las dos a la vez: o se está mirando a quién hay que atender, o se está
    buscando un hueco para meter a alguien que acaba de llegar. Se elige con un toque
    y se puede cambiar de día sin salir de la sección.
    """
    tema.seccion("Agenda", eyebrow="Elige el día", compacta=True)
    fecha = _selector_de_dia(hoy)

    bloques, huecos = analizar_jornada(
        fecha, horario_semanal, descansos, excepciones, duracion
    )
    if not bloques:
        tema.aviso_vacio("Ese día la barbería no abre.")
        return

    citas = db.obtener_citas_del_dia(fecha)
    reservadas = [c for c in citas if c["status"] != "cancelada"]
    ocupadas = [
        (time.fromisoformat(c["start_time"]), time.fromisoformat(c["end_time"]))
        for c in reservadas
    ]
    # El filtro por hora actual sólo aplica a hoy: en un día futuro todas las horas
    # siguen siendo válidas por más tarde que sea ahora mismo.
    libres = horarios_disponibles(
        fecha, horario_semanal, descansos, excepciones, ocupadas,
        ahora=ahora if fecha == hoy else None, duracion=duracion,
    )

    st.caption(f"Ese día caben {len(bloques)} cortes en total.")
    vista = _selector_de_vista(len(reservadas), len(libres))

    if vista == "reservadas":
        _tabla_reservadas(reservadas, fecha, hoy)
    else:
        _tabla_disponibles(libres, fecha, hoy, duracion)

    muertos = descansos_efectivos(fecha, horario_semanal, descansos, excepciones, duracion)
    for inicio_m, fin_m in muertos:
        tema.fila_descanso(
            f"{inicio_m.strftime('%H:%M')} – {fin_m.strftime('%H:%M')}", "Descanso"
        )

    sobrante = sum(h.minutos for h in huecos if not h.es_descanso)
    if sobrante:
        st.caption(
            f"Tu horario deja {sobrante} minutos que no alcanzan para otro corte de "
            f"{duracion}. Se suman al descanso para que no queden sueltos a mitad del día."
        )

    _consolidado_del_dia(reservadas, fecha)


def _selector_de_dia(hoy):
    """Días de la semana actual, de lunes a domingo. Arranca en el día de hoy."""
    lunes = hoy - timedelta(days=hoy.weekday())
    dias = [lunes + timedelta(days=i) for i in range(7)]

    etiquetas = {d: f"{NOMBRES_DIA[d.weekday()][:3]} {d.day}" for d in dias}
    elegido = st.segmented_control(
        "Día",
        options=dias,
        format_func=lambda d: etiquetas[d],
        default=hoy if hoy in dias else dias[0],
        key="agenda_dia",
        label_visibility="collapsed",
    )
    # segmented_control devuelve None si el usuario deselecciona: se vuelve a hoy en
    # vez de quedar sin ningún día, que dejaría la sección en blanco sin explicación.
    return elegido or hoy


def _selector_de_vista(n_reservadas, n_libres):
    """Dos botones grandes con su cifra. El que está activo se ve en dorado."""
    if "vista_agenda" not in st.session_state:
        st.session_state["vista_agenda"] = "disponibles"

    actual = st.session_state["vista_agenda"]
    col_r, col_d = st.columns(2)
    if col_r.button(
        f"Reservadas · {n_reservadas}",
        width="stretch",
        type="primary" if actual == "reservadas" else "secondary",
    ):
        st.session_state["vista_agenda"] = "reservadas"
        st.rerun()
    if col_d.button(
        f"Disponibles · {n_libres}",
        width="stretch",
        type="primary" if actual == "disponibles" else "secondary",
    ):
        st.session_state["vista_agenda"] = "disponibles"
        st.rerun()
    return st.session_state["vista_agenda"]


def _tabla_reservadas(reservadas, fecha, hoy):
    if not reservadas:
        tema.aviso_vacio("No hay citas reservadas ese día.")
        return

    for c in sorted(reservadas, key=lambda x: x["start_time"]):
        hora = time.fromisoformat(c["start_time"])
        nombre = (c.get("customers") or {}).get("name", "—")
        telefono = (c.get("customers") or {}).get("phone", "")
        servicio = NOMBRES_SERVICIO.get(c["service_type"], c["service_type"])

        tema.fila_cita(
            hora.strftime("%H:%M"),
            nombre,
            f'{servicio} · {telefono} · {_pesos(c["price_at_booking"])}',
            tema.pildora_estado(c["status"]),
        )
        # Las acciones sólo tienen sentido mientras la cita siga pendiente.
        if c["status"] == "confirmada":
            col_a, col_b, col_c = st.columns(3)
            if col_a.button("Atendida", key=f"at_{c['id']}", width="stretch"):
                db.cambiar_estado_cita(c["id"], "atendida")
                st.rerun()
            if col_b.button("No asistió", key=f"na_{c['id']}", width="stretch"):
                db.cambiar_estado_cita(c["id"], "no_asistio")
                st.rerun()
            if col_c.button("Cancelar", key=f"ca_{c['id']}", width="stretch"):
                db.cambiar_estado_cita(
                    c["id"], "cancelada", motivo="Cancelada por el administrador"
                )
                st.rerun()


def _consolidado_del_dia(reservadas, fecha):
    """Tabla para cuadrar los ingresos: se ajusta cita por cita lo que de verdad se
    cobró. Existe porque el barbero no le cobra lo mismo a todo el mundo -- el precio
    del servicio es sólo el punto de partida.

    Sólo entran las citas ATENDIDAS: son las únicas que suman a los ingresos, así que
    son las únicas cuyo valor tiene sentido cuadrar.
    """
    atendidas = [c for c in reservadas if c["status"] == "atendida"]
    if not atendidas:
        return

    tema.seccion("Consolidado del día", eyebrow="Ajusta lo que cobraste", compacta=True)

    with st.form(f"consolidado_{fecha}"):
        nuevos = {}
        for c in sorted(atendidas, key=lambda x: x["start_time"]):
            hora = time.fromisoformat(c["start_time"]).strftime("%H:%M")
            nombre = (c.get("customers") or {}).get("name", "—")
            servicio = NOMBRES_SERVICIO.get(c["service_type"], c["service_type"])
            nuevos[c["id"]] = st.number_input(
                f"{hora} · {nombre} · {servicio}",
                min_value=0,
                step=1000,
                value=int(c["price_at_booking"]),
                key=f"cons_{c['id']}",
            )
        guardar = st.form_submit_button(
            "Guardar valores del día", type="primary", width="stretch"
        )

    total = sum(int(v) for v in nuevos.values())
    st.caption(f"Total del día con estos valores: {_pesos(total)}")

    if guardar:
        cambiadas = 0
        for cita in atendidas:
            nuevo = int(nuevos[cita["id"]])
            if nuevo != int(cita["price_at_booking"]):
                db.actualizar_precio_cita(cita["id"], nuevo)
                cambiadas += 1
        st.success(
            f"{cambiadas} cita(s) actualizada(s)." if cambiadas else "No hubo cambios."
        )
        st.rerun()


def _tabla_disponibles(libres, fecha, hoy, duracion):
    """Las horas libres. Al tocar una se abre AHÍ MISMO el formulario para agendar.

    Antes el formulario salía al final de la página: había que tocar la hora, bajar a
    buscarlo y comprobar que traía la hora correcta. Ahora se abre justo bajo la hora
    que se tocó, que es donde uno está mirando.
    """
    if not libres:
        tema.aviso_vacio(
            "No quedan horas libres ese día."
            if fecha == hoy
            else "Ese día está lleno."
        )
        return

    abierta = st.session_state.get("agendando_en")

    for franja in libres:
        clave = f"{fecha}_{franja.inicio}"
        tema.fila_cita(
            franja.inicio.strftime("%H:%M"),
            "Libre",
            f"hasta las {franja.fin.strftime('%H:%M')} · {duracion} minutos",
            libre=True,
        )
        if abierta == clave:
            _formulario_en_linea(fecha, franja.inicio, duracion, clave)
        elif st.button("＋ Agendar en esta hora", key=f"ag_{clave}", width="stretch"):
            st.session_state["agendando_en"] = clave
            st.rerun()


def _formulario_en_linea(fecha, hora, duracion, clave):
    """Formulario corto pegado a la hora elegida: nombre, teléfono y servicio."""
    servicios = {s["type"]: s for s in db.obtener_servicios()}
    negocio = db.obtener_negocio()

    with st.form(f"form_rapido_{clave}"):
        st.markdown(
            f'<div class="etiqueta">Agendar a las {hora.strftime("%H:%M")}</div>',
            unsafe_allow_html=True,
        )
        nombre = st.text_input("Nombre", key=f"n_{clave}", placeholder="Nombre del cliente")
        telefono = st.text_input("Teléfono", key=f"t_{clave}", placeholder="Número de contacto")
        tipo = st.radio(
            "Servicio",
            options=list(servicios.keys()),
            format_func=lambda t: NOMBRES_SERVICIO.get(t, t),
            horizontal=True,
            key=f"s_{clave}",
        )
        col1, col2 = st.columns(2)
        crear = col1.form_submit_button("Agendar", type="primary", width="stretch")
        cerrar = col2.form_submit_button("Cancelar", width="stretch")

    if cerrar:
        st.session_state.pop("agendando_en", None)
        st.rerun()

    if not crear:
        return

    if not nombre.strip() or not telefono.strip():
        st.error("Escribe el nombre y el teléfono.")
        return

    servicio = servicios[tipo]
    precio = (
        negocio["general_price"]
        if negocio.get("pricing_mode") == "general" and negocio.get("general_price")
        else servicio["price"]
    )
    try:
        db.crear_cita(
            nombre=nombre.strip(),
            telefono=telefono.strip(),
            fecha=fecha,
            hora_inicio=hora,
            hora_fin=(datetime.combine(fecha, hora) + timedelta(minutes=duracion)).time(),
            tipo_servicio=tipo,
            service_id=servicio["id"],
            precio=precio,
        )
    except db.HorarioYaReservado:
        st.error("Ese horario acaba de ocuparse. Elige otro.")
        st.session_state.pop("agendando_en", None)
        return

    st.session_state.pop("agendando_en", None)
    st.success(f"Cita creada a las {hora.strftime('%H:%M')} para {nombre.strip()}.")
    st.rerun()


render()

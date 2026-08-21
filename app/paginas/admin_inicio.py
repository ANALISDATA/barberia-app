"""Panel del administrador: lo que necesito para trabajar hoy, en el orden que lo necesito.

Orden deliberado (de arriba a abajo): próximo espacio libre -> próximas citas -> cómo va
el día -> semana -> mes. Lo operativo primero, las estadísticas después: al abrir la app
en el celular entre corte y corte, lo urgente tiene que estar sin hacer scroll.

Regla que se repite en todo el archivo: los cortes realizados y los ingresos SÓLO cuentan
citas en estado 'atendida'. Confirmada, cancelada y no_asistio nunca suman.
"""
from datetime import datetime, time, timedelta

import pandas as pd
import streamlit as st

from app import db
from app.disponibilidad import (
    analizar_jornada,
    descansos_efectivos,
    horarios_disponibles,
    proximo_espacio,
)
from app.ui import graficos, tema
from config import NOMBRES_DIA, NOMBRES_SERVICIO, ZONA_HORARIA, fecha_larga


def _pesos(valor: int) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def _hora_bonita(t) -> str:
    return t.strftime("%I:%M %p").lstrip("0").replace("AM", "a.m.").replace("PM", "p.m.")


def _atendidas(citas: list[dict]) -> list[dict]:
    return [c for c in citas if c["status"] == "atendida"]


def render():
    tema.aplicar()

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

    _bloque_proximo_espacio(siguiente, libres, duracion)
    _bloque_agenda(hoy, ahora, horario_semanal, descansos, excepciones, duracion)
    _bloque_hoy(citas_hoy, libres)
    _bloque_semana(hoy)
    _bloque_mes(hoy)

    if st.session_state.get("mostrar_nueva_cita"):
        _formulario_nueva_cita(hoy, libres, duracion)


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
    if st.button("＋ Crear cita en este espacio", type="primary", width="stretch"):
        st.session_state["nueva_cita_hora_sugerida"] = siguiente.inicio
        st.session_state["mostrar_nueva_cita"] = True
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
            f'{servicio} · {_pesos(c["price_at_booking"])} · {telefono}',
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


def _tabla_disponibles(libres, fecha, hoy, duracion):
    if not libres:
        tema.aviso_vacio(
            "No quedan horas libres ese día."
            if fecha == hoy
            else "Ese día está lleno."
        )
        return

    for franja in libres:
        tema.fila_cita(
            franja.inicio.strftime("%H:%M"),
            "Libre",
            f"hasta las {franja.fin.strftime('%H:%M')} · {duracion} minutos",
            libre=True,
        )
        # Sólo se puede agendar en el día de hoy desde aquí: el formulario rápido está
        # pensado para el cliente que llega a la barbería en ese momento.
        if fecha == hoy:
            if st.button(
                "＋ Agendar en esta hora", key=f"ag_{franja.inicio}", width="stretch"
            ):
                st.session_state["nueva_cita_hora_sugerida"] = franja.inicio
                st.session_state["mostrar_nueva_cita"] = True
                st.rerun()


def _bloque_hoy(citas_hoy, libres):
    tema.seccion("Cómo va el día", eyebrow="Hoy", compacta=True)

    atendidas = _atendidas(citas_hoy)
    confirmadas = [c for c in citas_hoy if c["status"] == "confirmada"]
    canceladas = [c for c in citas_hoy if c["status"] == "cancelada"]
    ausentes = [c for c in citas_hoy if c["status"] == "no_asistio"]
    ingresos = sum(c["price_at_booking"] for c in atendidas)

    with tema.panel("Jornada"):
        st.altair_chart(graficos.anillo(len(atendidas), len(libres)), width="stretch")

    tema.grid_metricas([
        ("Ingresos de hoy", _pesos(ingresos), "oro"),
        ("Confirmadas", str(len(confirmadas)), ""),
        ("Disponibles", str(len(libres)), ""),
        ("Canceladas", str(len(canceladas)), "" if canceladas else "apagada"),
        ("No asistieron", str(len(ausentes)), "" if ausentes else "apagada"),
    ])


def _bloque_semana(hoy):
    lunes = hoy - timedelta(days=hoy.weekday())
    domingo = lunes + timedelta(days=6)
    citas = db.obtener_citas_rango(lunes, domingo)
    atendidas = _atendidas(citas)

    tema.seccion("Esta semana", eyebrow=f"{lunes.strftime('%d/%m')} — {domingo.strftime('%d/%m')}", compacta=True)

    # Una fila por día de la semana, incluso los días sin cortes: si se omitieran, la
    # gráfica mentiría (un lunes flojo se vería igual que un lunes cerrado).
    filas = []
    for i in range(7):
        dia = lunes + timedelta(days=i)
        del_dia = [c for c in atendidas if c["date"] == dia.isoformat()]
        filas.append({
            "etiqueta": NOMBRES_DIA[i][:3],
            "cortes": len(del_dia),
            "ingresos": sum(c["price_at_booking"] for c in del_dia),
        })
    por_dia = pd.DataFrame(filas)

    with tema.panel("Cortes realizados"):
        st.altair_chart(graficos.barras_cortes(por_dia[["etiqueta", "cortes"]]), width="stretch")

    with tema.panel("Ingresos por día"):
        st.altair_chart(graficos.area_ingresos(por_dia[["etiqueta", "ingresos"]]), width="stretch")

    tema.grid_metricas([
        ("Cortes", str(len(atendidas)), "oro"),
        ("Ingresos", _pesos(sum(c["price_at_booking"] for c in atendidas)), "oro"),
        ("Citas totales", str(len(citas)), ""),
        ("Canceladas", str(len([c for c in citas if c["status"] == "cancelada"])), ""),
        ("No asistieron", str(len([c for c in citas if c["status"] == "no_asistio"])), ""),
    ])


def _bloque_mes(hoy):
    primero = hoy.replace(day=1)
    citas = db.obtener_citas_rango(primero, hoy)
    atendidas = _atendidas(citas)

    sin_barba = len([c for c in atendidas if c["service_type"] == "sin_barba"])
    con_barba = len([c for c in atendidas if c["service_type"] == "con_barba"])
    ingresos = sum(c["price_at_booking"] for c in atendidas)
    dias_corridos = hoy.day
    promedio = len(atendidas) / dias_corridos if dias_corridos else 0

    tema.seccion("Este mes", eyebrow=f"Del 1 al {hoy.day}", compacta=True)

    with tema.panel("Tipo de corte"):
        st.altair_chart(graficos.barras_servicio(sin_barba, con_barba), width="stretch")

    tema.grid_metricas([
        ("Ingresos del mes", _pesos(ingresos), "oro"),
        ("Cortes", str(len(atendidas)), "oro"),
        ("Promedio diario", f"{promedio:.1f}", ""),
        ("Sin barba", str(sin_barba), ""),
        ("Con barba", str(con_barba), ""),
    ])


def _formulario_nueva_cita(hoy, libres, duracion):
    tema.seccion("Nueva cita", eyebrow="Cliente presencial", compacta=True)

    if not libres:
        tema.aviso_vacio("No quedan espacios libres hoy.")
        if st.button("Cerrar", width="stretch"):
            st.session_state["mostrar_nueva_cita"] = False
            st.rerun()
        return

    servicios = {s["type"]: s for s in db.obtener_servicios()}
    negocio = db.obtener_negocio()

    sugerida = st.session_state.get("nueva_cita_hora_sugerida")
    horas = [f.inicio for f in libres]
    indice = horas.index(sugerida) if sugerida in horas else 0

    with st.form("form_nueva_cita"):
        nombre = st.text_input("Nombre del cliente")
        telefono = st.text_input("Teléfono")
        tipo = st.radio(
            "Servicio",
            options=list(servicios.keys()),
            format_func=lambda t: NOMBRES_SERVICIO.get(t, t),
            horizontal=True,
        )
        hora = st.selectbox("Hora", options=horas, index=indice, format_func=_hora_bonita)
        col1, col2 = st.columns(2)
        crear = col1.form_submit_button("Crear cita", type="primary", width="stretch")
        cerrar = col2.form_submit_button("Cancelar", width="stretch")

    if cerrar:
        st.session_state["mostrar_nueva_cita"] = False
        st.rerun()

    if not crear:
        return

    if not nombre.strip() or not telefono.strip():
        st.error("Escribe el nombre y el teléfono del cliente.")
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
            fecha=hoy,
            hora_inicio=hora,
            hora_fin=(datetime.combine(hoy, hora) + timedelta(minutes=duracion)).time(),
            tipo_servicio=tipo,
            service_id=servicio["id"],
            precio=precio,
        )
    except db.HorarioYaReservado:
        st.error("Ese horario ya se ocupó. Elige otro.")
        return

    st.session_state["mostrar_nueva_cita"] = False
    st.success("Cita creada.")
    st.rerun()


render()

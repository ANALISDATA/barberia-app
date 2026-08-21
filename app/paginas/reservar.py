"""Página pública: el cliente reserva su cita en pocos pasos, sin crear cuenta.

Pensada para celular primero: una sola columna, botones grandes, y sólo se muestra el
paso siguiente cuando el anterior está resuelto (elegir día y servicio -> ver horas ->
dejar datos). Así el cliente nunca ve un formulario largo de golpe.
"""
from datetime import date, datetime, timedelta

import streamlit as st

from app import db
from app.disponibilidad import horarios_disponibles
from app.ui import tema
from config import NOMBRES_SERVICIO, ZONA_HORARIA, fecha_larga


def _pesos(valor: int) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def _hora_bonita(t) -> str:
    return t.strftime("%I:%M %p").lstrip("0").replace("AM", "a.m.").replace("PM", "p.m.")


def _hora_compacta(t) -> str:
    """Versión corta para los botones de la rejilla de horas: en celular caben tres por
    fila, y '7:45 a.m.' se parte en dos líneas mientras que '7:45 am' no."""
    return t.strftime("%I:%M %p").lstrip("0").replace("AM", "am").replace("PM", "pm")


def _sin_conexion():
    st.markdown(
        '<div class="hero"><div class="hero-inner">'
        '<h1 class="hero-nombre">Ya volvemos</h1>'
        '<p class="hero-tagline">Estamos alistando la agenda. Inténtalo en unos minutos.</p>'
        "</div></div>",
        unsafe_allow_html=True,
    )


def _reiniciar():
    for clave in ["reserva_fecha", "reserva_hora", "reserva_confirmada"]:
        st.session_state.pop(clave, None)


def render():
    tema.aplicar()

    if not db.disponible():
        _sin_conexion()
        return

    negocio = db.obtener_negocio()

    if st.session_state.get("reserva_confirmada"):
        _paso_exito(negocio)
        return

    servicios = {s["type"]: s for s in db.obtener_servicios()}
    horario_semanal = db.obtener_horario_semanal()
    duracion = db.obtener_duracion_cita()

    tema.hero_publico(
        negocio,
        resumen_horario=tema.resumen_horario_texto(horario_semanal),
        url_waze=tema.url_waze(negocio.get("address", "")),
    )

    tema.seccion("Reserva tu cita", eyebrow="Elige día y servicio", ancla="reservar")

    hoy = datetime.now(ZONA_HORARIA).date()
    fecha = st.date_input(
        "¿Qué día quieres venir?",
        value=hoy,
        min_value=hoy,
        max_value=hoy + timedelta(days=45),
        format="DD/MM/YYYY",
    )
    tipo = st.radio(
        "¿Qué servicio deseas?",
        options=list(servicios.keys()),
        format_func=lambda t: NOMBRES_SERVICIO.get(t, t),
        horizontal=True,
    )

    precio = _precio_de(negocio, servicios[tipo])
    st.markdown(
        f'<div class="etiqueta" style="text-align:center;margin:6px 0 2px;">Valor del servicio</div>'
        f'<div class="valor-medio" style="text-align:center;margin-bottom:10px;">{_pesos(precio)}</div>',
        unsafe_allow_html=True,
    )

    descansos = db.obtener_descansos()
    excepciones = db.obtener_excepciones(fecha, fecha)
    citas_activas = db.obtener_citas_activas(fecha)
    ahora = datetime.now(ZONA_HORARIA)

    libres = horarios_disponibles(
        fecha, horario_semanal, descansos, excepciones, citas_activas,
        ahora=ahora, duracion=duracion,
    )

    tema.seccion("Horas disponibles", eyebrow=fecha_larga(fecha))

    if not libres:
        tema.aviso_vacio(
            "No quedan horas disponibles ese día.<br>Prueba con otra fecha."
        )
        return

    # Si cambia el día, la hora elegida antes deja de tener sentido.
    if st.session_state.get("reserva_fecha") != fecha:
        st.session_state["reserva_hora"] = None
    st.session_state["reserva_fecha"] = fecha

    # 3 columnas: en celular quedan botones cómodos de tocar sin que el texto se parta.
    columnas = st.columns(3)
    for i, franja in enumerate(libres):
        seleccionada = st.session_state.get("reserva_hora") == franja.inicio
        with columnas[i % 3]:
            if st.button(
                _hora_compacta(franja.inicio),
                key=f"hora_{franja.inicio}",
                type="primary" if seleccionada else "secondary",
                width="stretch",
            ):
                st.session_state["reserva_hora"] = franja.inicio
                st.rerun()

    hora_elegida = st.session_state.get("reserva_hora")
    if not hora_elegida:
        return

    tema.seccion("Tus datos", eyebrow=f"{fecha_larga(fecha)} · {_hora_bonita(hora_elegida)}")

    with st.form("form_datos_cliente"):
        nombre = st.text_input("Tu nombre")
        telefono = st.text_input("Tu teléfono")
        enviado = st.form_submit_button("Confirmar mi cita", type="primary", width="stretch")

    if not enviado:
        return

    if not nombre.strip() or not telefono.strip():
        st.error("Escribe tu nombre y tu teléfono para confirmar.")
        return

    servicio = servicios[tipo]
    try:
        cita = db.crear_cita(
            nombre=nombre.strip(),
            telefono=telefono.strip(),
            fecha=fecha,
            hora_inicio=hora_elegida,
            hora_fin=(datetime.combine(fecha, hora_elegida) + timedelta(minutes=duracion)).time(),
            tipo_servicio=tipo,
            service_id=servicio["id"],
            precio=precio,
        )
    except db.HorarioYaReservado:
        st.error(
            "Lo sentimos, este horario acaba de ser reservado. "
            "Por favor selecciona otro horario."
        )
        st.session_state["reserva_hora"] = None
        st.rerun()
        return

    st.session_state["reserva_confirmada"] = cita
    st.rerun()


def _precio_de(negocio: dict, servicio: dict) -> int:
    """Precio individual del servicio, o el general si el negocio lo tiene activado."""
    if negocio.get("pricing_mode") == "general" and negocio.get("general_price"):
        return negocio["general_price"]
    return servicio["price"]


def _paso_exito(negocio: dict):
    cita = st.session_state["reserva_confirmada"]
    fecha = date.fromisoformat(cita["date"])
    hora = datetime.strptime(cita["start_time"][:5], "%H:%M").time()

    st.markdown(
        f'<div class="hero"><div class="hero-inner" style="padding-bottom:34px;">'
        f'<div class="hero-cinta"><i></i>Cita confirmada<i class="der"></i></div>'
        f'<h1 class="hero-nombre" style="font-size:clamp(34px,8vw,60px)!important;">'
        f'¡Nos vemos!</h1>'
        f'<p class="hero-tagline">{negocio.get("name", "")} te espera.</p>'
        f"</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="ticket">'
        f'<div class="dia">{fecha_larga(fecha)}</div>'
        f'<div class="hora-grande">{_hora_bonita(hora)}</div>'
        f'<div class="detalle">{NOMBRES_SERVICIO.get(cita["service_type"], "")} · '
        f'{_pesos(cita["price_at_booking"])}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    llegar = negocio.get("arrive_minutes_before", 10)
    cancelar = negocio.get("cancellation_hours", 3)
    st.info(f"Recuerda llegar {llegar} minutos antes de tu cita.")
    st.caption(
        f"Si no puedes asistir, avísanos con mínimo {cancelar} horas de anticipación."
    )

    if negocio.get("address"):
        st.link_button(
            "Cómo llegar",
            tema.url_waze(negocio["address"]),
            width="stretch",
        )

    if st.button("Reservar otra cita", width="stretch"):
        _reiniciar()
        st.rerun()


render()

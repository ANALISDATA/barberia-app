"""Página pública: el cliente reserva su cita en unos pocos pasos, sin crear cuenta."""
from datetime import date, datetime, timedelta

import streamlit as st

from app import db
from app.disponibilidad import horarios_disponibles
from app.ui import tema
from config import NOMBRES_SERVICIO, ZONA_HORARIA


def _sin_conexion():
    st.markdown(
        '<div class="exito-publico"><h1>💈 Estamos alistando la agenda</h1>'
        "<p>Vuelve a intentarlo en unos minutos.</p></div>",
        unsafe_allow_html=True,
    )
    st.caption("(Administrador: falta conectar Supabase — corre Conectar_Supabase.py)")


def _reiniciar():
    for clave in ["reserva_fecha", "reserva_servicio", "reserva_hora", "reserva_confirmada"]:
        st.session_state.pop(clave, None)


def render():
    tema.aplicar()

    if not db.disponible():
        _sin_conexion()
        return

    negocio = db.obtener_negocio()
    servicios = {s["type"]: s for s in db.obtener_servicios()}

    if st.session_state.get("reserva_confirmada"):
        _paso_exito(negocio)
        return

    horario_semanal = db.obtener_horario_semanal()
    resumen_horario = tema.resumen_horario_texto(horario_semanal)
    tema.hero_publico(negocio, resumen_horario)

    st.markdown('<div id="elige-el-dia"></div>', unsafe_allow_html=True)
    st.markdown("##### Elige tu cita")

    col_fecha, col_servicio = st.columns(2)
    with col_fecha:
        hoy = datetime.now(ZONA_HORARIA).date()
        fecha = st.date_input(
            "Elige el día", value=hoy, min_value=hoy, max_value=hoy + timedelta(days=45),
            format="DD/MM/YYYY",
        )
    with col_servicio:
        tipo = st.radio(
            "¿Qué servicio deseas?",
            options=list(servicios.keys()),
            format_func=lambda t: NOMBRES_SERVICIO.get(t, t),
            horizontal=True,
        )

    descansos = db.obtener_descansos()
    excepciones = db.obtener_excepciones(fecha, fecha)
    citas_activas = db.obtener_citas_activas(fecha)
    ahora = datetime.now(ZONA_HORARIA)

    libres = horarios_disponibles(
        fecha, horario_semanal, descansos, excepciones, citas_activas, ahora=ahora
    )

    st.markdown("##### Horas disponibles")
    if not libres:
        st.info("No quedan horas disponibles ese día. Prueba con otra fecha.")
        return

    if "reserva_hora" not in st.session_state or st.session_state.get("reserva_fecha") != fecha:
        st.session_state["reserva_hora"] = None
    st.session_state["reserva_fecha"] = fecha

    columnas = st.columns(4)
    for i, franja in enumerate(libres):
        etiqueta = franja.inicio.strftime("%I:%M %p").lstrip("0")
        seleccionada = st.session_state.get("reserva_hora") == franja.inicio
        with columnas[i % 4]:
            if st.button(etiqueta, key=f"hora_{franja.inicio}", type="primary" if seleccionada else "secondary", width="stretch"):
                st.session_state["reserva_hora"] = franja.inicio

    hora_elegida = st.session_state.get("reserva_hora")
    if not hora_elegida:
        return

    st.divider()
    st.markdown("##### Tus datos")
    with st.form("form_datos_cliente"):
        nombre = st.text_input("Nombre")
        telefono = st.text_input("Número de teléfono")
        enviado = st.form_submit_button("Confirmar cita", type="primary", width="stretch")

    if not enviado:
        return
    if not nombre.strip() or not telefono.strip():
        st.error("Completa nombre y teléfono para confirmar.")
        return

    servicio = servicios[tipo]
    precio = servicio["price"] if negocio["pricing_mode"] == "individual" else negocio["general_price"]

    try:
        cita = db.crear_cita(
            nombre=nombre.strip(),
            telefono=telefono.strip(),
            fecha=fecha,
            hora_inicio=hora_elegida,
            hora_fin=(datetime.combine(fecha, hora_elegida) + timedelta(minutes=45)).time(),
            tipo_servicio=tipo,
            service_id=servicio["id"],
            precio=precio,
        )
    except db.HorarioYaReservado:
        st.error("Lo sentimos, este horario acaba de ser reservado. Por favor selecciona otro horario.")
        st.session_state["reserva_hora"] = None
        st.rerun()
        return

    st.session_state["reserva_confirmada"] = cita
    st.session_state["reserva_negocio"] = negocio
    st.rerun()


def _paso_exito(negocio: dict):
    cita = st.session_state["reserva_confirmada"]
    fecha = date.fromisoformat(cita["date"])
    hora = cita["start_time"][:5]
    st.markdown(
        '<div class="exito-publico"><h1>✔ ¡Cita confirmada!</h1></div>', unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="tarjeta-dorada" style="text-align:center;">'
        f'<div class="etiqueta">{fecha.strftime("%d/%m/%Y")}</div>'
        f'<div class="valor-grande">{hora}</div>'
        f'<div class="etiqueta">{NOMBRES_SERVICIO.get(cita["service_type"], "")} · '
        f'${cita["price_at_booking"]:,.0f}'.replace(",", ".") + "</div></div>",
        unsafe_allow_html=True,
    )
    st.info(f"Recuerda llegar {negocio.get('arrive_minutes_before', 10)} minutos antes de tu cita.")
    st.caption(
        f"Si no puedes asistir, recuerda avisar con mínimo {negocio.get('cancellation_hours', 3)} "
        "horas de anticipación."
    )
    if st.button("Reservar otra cita"):
        _reiniciar()
        st.rerun()


render()

"""Panel del administrador -- lo primero que se ve al entrar: hoy, de un vistazo."""
from datetime import datetime, time, timedelta

import streamlit as st

from app import db
from app.disponibilidad import horarios_disponibles, proximo_espacio
from app.ui import tema
from config import NOMBRES_SERVICIO, ZONA_HORARIA


def _pesos(valor: int) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


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
    citas_activas_horas = [
        (time.fromisoformat(c["start_time"]), time.fromisoformat(c["end_time"]))
        for c in citas_hoy
        if c["status"] != "cancelada"
    ]

    libres = horarios_disponibles(hoy, horario_semanal, descansos, excepciones, citas_activas_horas, ahora=ahora)
    siguiente = proximo_espacio(hoy, horario_semanal, descansos, excepciones, citas_activas_horas, ahora=ahora)

    saludo = "Buenos días" if ahora.hour < 12 else ("Buenas tardes" if ahora.hour < 19 else "Buenas noches")
    st.markdown(f"### {saludo} 👋")
    st.caption(hoy.strftime("%A %d de %B, %Y").capitalize())

    st.markdown("##### Próximo espacio")
    if siguiente:
        col1, col2 = st.columns([2, 1])
        with col1:
            tema.tarjeta_metrica("Disponible", siguiente.inicio.strftime("%I:%M %p").lstrip("0") + " · 45 min", dorada=True)
        with col2:
            if st.button("+ Crear cita en este espacio", width="stretch"):
                st.session_state["nueva_cita_hora_sugerida"] = siguiente.inicio
                st.session_state["mostrar_nueva_cita"] = True
    else:
        st.markdown('<div class="tarjeta">No quedan espacios libres hoy.</div>', unsafe_allow_html=True)

    st.markdown("##### Próximas citas")
    proximas = [c for c in citas_hoy if c["status"] == "confirmada" and c["start_time"] >= ahora.strftime("%H:%M:%S")]
    if not proximas:
        st.caption("No hay más citas confirmadas por hoy.")
    for c in proximas[:6]:
        nombre = (c.get("customers") or {}).get("name", "—")
        servicio = NOMBRES_SERVICIO.get(c["service_type"], c["service_type"])
        st.markdown(
            f'<div class="tarjeta">{c["start_time"][:5]} — {nombre} — {servicio}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("##### Resumen de hoy")
    atendidas = [c for c in citas_hoy if c["status"] == "atendida"]
    confirmadas = [c for c in citas_hoy if c["status"] == "confirmada"]
    canceladas = [c for c in citas_hoy if c["status"] == "cancelada"]
    no_asistio = [c for c in citas_hoy if c["status"] == "no_asistio"]
    ingresos_hoy = sum(c["price_at_booking"] for c in atendidas)

    cols = st.columns(3)
    with cols[0]:
        tema.tarjeta_metrica("Cortes realizados", str(len(atendidas)))
    with cols[1]:
        tema.tarjeta_metrica("Confirmadas", str(len(confirmadas)))
    with cols[2]:
        tema.tarjeta_metrica("Disponibles", str(len(libres)))
    cols2 = st.columns(3)
    with cols2[0]:
        tema.tarjeta_metrica("Canceladas", str(len(canceladas)))
    with cols2[1]:
        tema.tarjeta_metrica("No asistieron", str(len(no_asistio)))
    with cols2[2]:
        tema.tarjeta_metrica("Ingresos", _pesos(ingresos_hoy))

    with st.expander("Ver todas las citas de hoy"):
        for c in citas_hoy:
            nombre = (c.get("customers") or {}).get("name", "—")
            servicio = NOMBRES_SERVICIO.get(c["service_type"], c["service_type"])
            col_a, col_b, col_c = st.columns([3, 2, 2])
            with col_a:
                st.markdown(
                    f'{c["start_time"][:5]} — {nombre} — {servicio} — {_pesos(c["price_at_booking"])} '
                    + tema.pildora_estado(c["status"]),
                    unsafe_allow_html=True,
                )
            with col_b:
                if c["status"] == "confirmada" and st.button("Marcar atendida", key=f"atendida_{c['id']}"):
                    db.cambiar_estado_cita(c["id"], "atendida")
                    st.rerun()
            with col_c:
                if c["status"] == "confirmada" and st.button("Cancelar", key=f"cancelar_{c['id']}"):
                    db.cambiar_estado_cita(c["id"], "cancelada", motivo="Cancelada por el administrador")
                    st.rerun()

    if st.session_state.get("mostrar_nueva_cita"):
        _formulario_nueva_cita(hoy, horario_semanal, descansos, excepciones, citas_activas_horas, ahora)


def _formulario_nueva_cita(hoy, horario_semanal, descansos, excepciones, citas_activas_horas, ahora):
    st.divider()
    st.markdown("##### + Nueva cita (cliente presencial)")

    servicios = {s["type"]: s for s in db.obtener_servicios()}
    negocio = db.obtener_negocio()
    libres = horarios_disponibles(hoy, horario_semanal, descansos, excepciones, citas_activas_horas, ahora=ahora)

    if not libres:
        st.warning("No quedan espacios libres hoy.")
        if st.button("Cerrar"):
            st.session_state["mostrar_nueva_cita"] = False
            st.rerun()
        return

    sugerida = st.session_state.get("nueva_cita_hora_sugerida")
    opciones_hora = [f.inicio for f in libres]
    indice_defecto = opciones_hora.index(sugerida) if sugerida in opciones_hora else 0

    with st.form("form_nueva_cita"):
        nombre = st.text_input("Nombre")
        telefono = st.text_input("Teléfono")
        tipo = st.radio(
            "Servicio", options=list(servicios.keys()),
            format_func=lambda t: NOMBRES_SERVICIO.get(t, t), horizontal=True,
        )
        hora = st.selectbox(
            "Hora", options=opciones_hora, index=indice_defecto,
            format_func=lambda t: t.strftime("%I:%M %p").lstrip("0"),
        )
        col1, col2 = st.columns(2)
        crear = col1.form_submit_button("Crear cita", type="primary")
        cerrar = col2.form_submit_button("Cancelar")

    if cerrar:
        st.session_state["mostrar_nueva_cita"] = False
        st.rerun()

    if crear:
        if not nombre.strip() or not telefono.strip():
            st.error("Completa nombre y teléfono.")
            return
        servicio = servicios[tipo]
        precio = servicio["price"] if negocio["pricing_mode"] == "individual" else negocio["general_price"]
        try:
            db.crear_cita(
                nombre=nombre.strip(), telefono=telefono.strip(), fecha=hoy,
                hora_inicio=hora,
                hora_fin=(datetime.combine(hoy, hora) + timedelta(minutes=45)).time(),
                tipo_servicio=tipo, service_id=servicio["id"], precio=precio,
            )
        except db.HorarioYaReservado:
            st.error("Ese horario ya se ocupó. Elige otro.")
            return
        st.session_state["mostrar_nueva_cita"] = False
        st.success("Cita creada.")
        st.rerun()


render()

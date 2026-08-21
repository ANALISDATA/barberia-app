"""Página de reserva: el cliente pide su cita en pocos pasos, sin crear cuenta.

Vive en su propia página (`/cita`), separada de la portada: así el botón "Pide aquí tu
cita" lleva de verdad a algún lado, y la portada no queda tan larga que haya que bajar
para ver la dirección.

Pensada para celular primero: una sola columna, botones grandes, y sólo se muestra el
paso siguiente cuando el anterior está resuelto (elegir día y servicio -> ver horas ->
dejar datos). Así el cliente nunca ve un formulario largo de golpe.
"""
from datetime import date, datetime, time, timedelta

import streamlit as st

from app import db
from app.disponibilidad import horarios_disponibles
from app.ui import tema, volver
from config import NOMBRES_SERVICIO, ZONA_HORARIA, fecha_larga

PASOS = ["Día", "Servicio", "Hora", "Datos"]


def _pesos(valor: int) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def _hora_bonita(t) -> str:
    return t.strftime("%I:%M %p").lstrip("0").replace("AM", "a.m.").replace("PM", "p.m.")


def _hora_compacta(t) -> str:
    """Versión corta para los botones de la rejilla de horas: en celular caben tres por
    fila, y '7:45 a.m.' se parte en dos líneas mientras que '7:45 am' no."""
    return t.strftime("%I:%M %p").lstrip("0").replace("AM", "am").replace("PM", "pm")


def _sin_conexion():
    tema.hero_simple(
        titulo="Ya volvemos",
        frase="Estamos alistando la agenda. Inténtalo en unos minutos.",
    )


def _rejilla_de_horas(libres):
    """Las horas, separadas en mañana y tarde.

    Se agrupan porque una tira de 14 horas seguidas obliga a leerlas todas para
    encontrar la que sirve; con los dos bloques, el cliente salta directo al que le
    conviene. Van de a tres por fila: en celular son botones cómodos de tocar con el
    pulgar sin que el texto se parta en dos líneas.
    """
    manana = [f for f in libres if f.inicio < time(12, 0)]
    tarde = [f for f in libres if f.inicio >= time(12, 0)]

    for titulo, grupo in (("Mañana", manana), ("Tarde", tarde)):
        if not grupo:
            continue
        tema.franja_titulo(titulo)
        columnas = st.columns(3)
        for i, franja in enumerate(grupo):
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

    tema.hero_simple(
        titulo="Pide tu cita",
        cinta=negocio.get("name", ""),
        frase="Elige el día, el servicio y la hora. Toma menos de un minuto.",
    )
    volver.encima_del_hero()

    hoy = datetime.now(ZONA_HORARIA).date()

    # La barra de pasos se dibuja UNA sola vez, arriba. Repetirla antes de cada bloque
    # (como estaba) llenaba la pantalla de barras iguales y alejaba el contenido.
    # El día y el servicio siempre tienen un valor por defecto, así que el progreso
    # real depende de si ya se eligió la hora.
    paso_actual = 3 if st.session_state.get("reserva_hora") else 2
    tema.pasos(PASOS, paso_actual)

    # ---------- Paso 1: el día ----------
    tema.seccion("¿Cuándo vienes?", eyebrow="Paso 1 de 4", compacta=False)
    fecha = st.date_input(
        "Elige el día",
        value=hoy,
        min_value=hoy,
        max_value=hoy + timedelta(days=45),
        format="DD/MM/YYYY",
        label_visibility="collapsed",
    )
    st.caption(f"📅 {fecha_larga(fecha)}")

    # ---------- Paso 2: el servicio ----------
    tema.seccion("¿Qué te hacemos?", eyebrow="Paso 2 de 4", compacta=False)
    tipo = st.segmented_control(
        "Servicio",
        options=list(servicios.keys()),
        format_func=lambda t: NOMBRES_SERVICIO.get(t, t),
        default=list(servicios.keys())[0],
        key="reserva_servicio",
        label_visibility="collapsed",
        width="stretch",
    )
    # segmented_control devuelve None si se deselecciona: se vuelve al primero para no
    # quedar sin servicio elegido y con la pantalla en blanco sin explicación.
    tipo = tipo or list(servicios.keys())[0]

    # El precio NO se le muestra al cliente: el barbero no le cobra lo mismo a todo el
    # mundo. Se sigue guardando en la cita (precio historico) porque de ahi salen los
    # ingresos del panel, pero es informacion interna.
    precio = _precio_de(negocio, servicios[tipo])

    descansos = db.obtener_descansos()
    excepciones = db.obtener_excepciones(fecha, fecha)
    citas_activas = db.obtener_citas_activas(fecha)
    ahora = datetime.now(ZONA_HORARIA)

    libres = horarios_disponibles(
        fecha, horario_semanal, descansos, excepciones, citas_activas,
        ahora=ahora, duracion=duracion,
    )

    # ---------- Paso 3: la hora ----------
    tema.seccion("¿A qué hora?", eyebrow="Paso 3 de 4", compacta=False)
    tema.resumen_seleccion([
        ("Día", fecha.strftime("%d/%m")),
        ("Servicio", NOMBRES_SERVICIO.get(tipo, tipo)),
        ("Duración", f"{duracion} min"),
    ])

    if not libres:
        tema.aviso_vacio(
            "No quedan horas disponibles ese día.<br>Prueba con otra fecha."
        )
        tema.pie_de_pagina(negocio)
        return

    # Si cambia el día, la hora elegida antes deja de tener sentido.
    if st.session_state.get("reserva_fecha") != fecha:
        st.session_state["reserva_hora"] = None
    st.session_state["reserva_fecha"] = fecha

    _rejilla_de_horas(libres)

    hora_elegida = st.session_state.get("reserva_hora")
    if not hora_elegida:
        st.caption("Toca una hora para continuar.")
        tema.pie_de_pagina(negocio)
        return

    # ---------- Paso 4: los datos ----------
    tema.seccion("¿Quién viene?", eyebrow="Paso 4 de 4", compacta=False)
    tema.resumen_seleccion([
        ("Día", fecha.strftime("%d/%m")),
        ("Hora", _hora_compacta(hora_elegida)),
        ("Servicio", NOMBRES_SERVICIO.get(tipo, tipo)),
    ])

    with st.form("form_datos_cliente"):
        nombre = st.text_input("Tu nombre", placeholder="Como te llamas")
        telefono = st.text_input("Tu teléfono", placeholder="Para avisarte de tu cita")
        enviado = st.form_submit_button(
            "Confirmar mi cita", type="primary", width="stretch"
        )

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
        f'<div class="hero">{volver.html()}'
        f'<div class="hero-inner" style="padding-bottom:34px;">'
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
        f'<div class="detalle">{NOMBRES_SERVICIO.get(cita["service_type"], "")}</div>'
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
    tema.pie_de_pagina(negocio)


render()

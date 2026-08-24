"""Clientes que llevan tiempo sin volver, listos para invitarlos por WhatsApp.

Un toque abre WhatsApp con el mensaje ya escrito; el barbero sólo pulsa enviar. No se
envían solos a propósito -- ver la explicación en `app/recordatorios.py`.
"""
from datetime import datetime

import streamlit as st

from app import catalogo, db, recordatorios
from app.ui import menu, tema
from app.ui.tema import resumen_horario_texto
from config import ZONA_HORARIA

ENLACE_APP = "https://esteban-barber.streamlit.app"


def _pesos(valor: int) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def render():
    tema.aplicar()

    if not st.session_state.get("admin_autenticado"):
        st.warning("Necesitas iniciar sesión para ver el panel.")
        st.link_button("Ir a iniciar sesión", "/admin", width="stretch")
        return

    menu.pintar("recordar")

    if not db.disponible():
        st.warning("No hay conexión con Supabase.")
        return

    hoy = datetime.now(ZONA_HORARIA).date()
    tema.saludo("Invitar a volver", "Clientes que llevan tiempo sin venir")

    if not recordatorios.hay_columna_recordatorio():
        st.info(
            "Falta un paso de una sola vez para poder llevar la cuenta de a quién ya le "
            "escribiste: correr en Supabase el archivo `supabase/005_recordatorios.sql`. "
            "Sin eso la lista funciona, pero te volvería a mostrar mañana a los mismos "
            "de hoy."
        )

    # Arranca en 8 porque hay clientes que se motilan todos los sábados: a los 10 días
    # ya llevan dos semanas de atraso. La clave hace que el panel se acuerde de lo que
    # elegiste mientras la sesión siga abierta, para no tener que moverlo cada vez.
    dias = st.select_slider(
        "Mostrar a quienes llevan sin venir",
        options=[8, 10, 15, 20, 30, 45, 60],
        value=recordatorios.DIAS_POR_DEFECTO,
        format_func=lambda d: f"{d} días o más",
        key="recordar_dias",
    )

    dormidos = recordatorios.buscar(hoy, dias)
    negocio = db.obtener_negocio()
    nombres = catalogo.nombres_servicios()
    # El horario se arma con el mismo texto que ve el cliente en la portada, para que
    # no haya dos versiones del horario circulando.
    horario = resumen_horario_texto(db.obtener_horario_semanal()).replace("<br>", " · ")

    if not dormidos:
        tema.aviso_vacio(
            f"Ningún cliente lleva {dias} días o más sin venir.<br>"
            "Vas al día con tu gente."
        )
        tema.pie_de_pagina(negocio)
        return

    st.caption(
        f"**{len(dormidos)} cliente(s)** para invitar. No aparecen los que ya tienen "
        "cita reservada ni a los que les escribiste hace poco."
    )

    for c in dormidos:
        servicio = nombres.get(c.ultimo_servicio, c.ultimo_servicio)
        avisado = (
            f" · le escribiste el {c.ultimo_recordatorio.strftime('%d/%m')}"
            if c.ultimo_recordatorio else ""
        )
        tema.fila_cita(
            f"{c.dias_sin_venir(hoy)}d",
            c.nombre,
            f"{c.telefono} · {c.veces} corte(s) · última: "
            f"{c.ultima_visita.strftime('%d/%m')} · {servicio}{avisado}",
        )

        texto = recordatorios.mensaje(
            c, negocio, ENLACE_APP, horario=horario, servicio=servicio
        )
        url = recordatorios.url_whatsapp(c, texto)

        if not url:
            st.caption("Sin teléfono guardado: no se le puede escribir.")
            continue

        col_a, col_b = st.columns([3, 2])
        with col_a:
            st.link_button("💬  Abrir el chat", url, width="stretch", type="primary")
        with col_b:
            if st.button("Ya le escribí", key=f"ok_{c.cliente_id}", width="stretch"):
                recordatorios.marcar_escrito(c.cliente_id, hoy)
                st.rerun()

        # El bloque copiable se queda como red de seguridad. Los emojis ya llegan bien
        # por el enlace (se usa api.whatsapp.com, ver `recordatorios.url_whatsapp`),
        # pero si algún día una versión de WhatsApp los vuelve a dañar, copiar y pegar
        # no pasa por ningún enlace y siempre funciona.
        with st.expander("Copiar el mensaje (por si acaso)"):
            st.code(texto, language=None)
            st.caption(
                "Toca el ícono de copiar de la esquina, abre el chat y pégalo."
            )

    st.caption(
        "Al pulsar **Escribirle** se abre WhatsApp con el mensaje ya escrito: sólo le "
        "das enviar. Después toca **Ya le escribí** para que no te lo vuelva a mostrar."
    )
    tema.pie_de_pagina(negocio)


render()

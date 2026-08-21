"""Portada pública: la primera pantalla que ve quien abre el enlace.

Aquí NO se reserva. Sólo se presenta la barbería (nombre, dónde queda, teléfono,
horario y un vistazo a los productos) y se ofrecen las dos acciones posibles: pedir
cita -- que lleva a su propia página -- o ver el catálogo completo.

Se separó así a propósito: cuando el formulario de reserva vivía en esta misma página,
bastaba con bajar un poco para toparse con él y el botón "Pide aquí tu cita" no pintaba
nada. Además la portada quedaba tan larga que en computador no se alcanzaba a ver la
dirección sin hacer scroll.
"""
import streamlit as st

from app import db
from app.productos import PRODUCTOS
from app.ui import tema


def _sin_conexion():
    tema.hero_simple(
        titulo="Ya volvemos",
        frase="Estamos alistando la agenda. Inténtalo en unos minutos.",
    )


def render():
    tema.aplicar()

    if not db.disponible():
        _sin_conexion()
        return

    negocio = db.obtener_negocio()
    horario_semanal = db.obtener_horario_semanal()

    tema.hero_publico(
        negocio,
        resumen_horario=tema.resumen_horario_texto(horario_semanal),
        url_waze=tema.url_waze(negocio.get("address", "")),
    )

    tema.seccion("Nuestros productos", eyebrow="Para el cuidado en casa")
    tema.tira_productos(PRODUCTOS)
    st.link_button("Ver el catálogo completo", "/productos", width="stretch")
    tema.pie_de_pagina(negocio)


render()

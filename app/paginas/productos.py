"""Catálogo público de productos.

El cliente ve la foto, el nombre y el precio de cada producto, y con un toque abre
WhatsApp con el mensaje ya escrito preguntando por ese producto en concreto -- no tiene
que buscar el número ni explicar qué quiere.
"""
import streamlit as st

from app import db
from app.productos import PRODUCTOS
from app.ui import tema


def _pesos(valor: int) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def render():
    tema.aplicar()

    negocio = db.obtener_negocio() if db.disponible() else {}
    telefono = negocio.get("phone", "")

    tema.hero_simple(
        titulo="Productos",
        cinta="Para el cuidado en casa",
        frase="Ceras, pomadas y tratamiento. Pregunta por el que quieras y te lo apartamos.",
    )

    for producto in PRODUCTOS:
        tema.tarjeta_producto(
            nombre=producto["nombre"],
            precio=_pesos(producto["precio"]),
            descripcion=producto["descripcion"],
            imagen=f"assets/productos/{producto['imagen']}",
            url_whatsapp=tema.url_whatsapp(telefono, producto["nombre"]),
        )

    st.markdown(
        '<div class="cierre-catalogo">¿Buscas algo más?<br>'
        "Escríbenos y te ayudamos.</div>",
        unsafe_allow_html=True,
    )
    if telefono:
        st.link_button(
            "Escribir por WhatsApp",
            tema.url_whatsapp(telefono),
            width="stretch",
            type="primary",
        )

    # Enlace normal en vez de st.page_link: page_link exige que la página esté
    # registrada por st.navigation, y revienta si este archivo se ejecuta suelto
    # (como hacen las pruebas). Una URL simple funciona en los dos casos.
    st.link_button("← Volver al inicio", "/", width="stretch")
    tema.pie_de_pagina(negocio)


render()

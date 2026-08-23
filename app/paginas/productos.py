"""Catálogo público de productos.

El cliente ve la foto, el nombre y el precio de cada producto, y con un toque abre
WhatsApp con el mensaje ya escrito preguntando por ese producto en concreto -- no tiene
que buscar el número ni explicar qué quiere.

De dónde salen los productos: de la base de datos, que es lo que el barbero edita desde
Ajustes. Si esa tabla todavía no existe (falta correr la migración 003), se cae a la
lista fija de `app/productos.py`, que es como estaba antes -- así el catálogo nunca
aparece vacío por un paso de instalación pendiente.
"""
import streamlit as st

from app import catalogo, db
from app.productos import PRODUCTOS as PRODUCTOS_FIJOS
from app.ui import tema, volver


def _pesos(valor: int) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def _lista_de_productos() -> list[dict]:
    """Normaliza las dos fuentes a la misma forma: nombre, precio, descripción e
    imagen ya lista para incrustar."""
    de_la_base = catalogo.productos()
    if de_la_base:
        return [
            {
                "nombre": p["nombre"],
                "precio": p["precio"],
                "descripcion": p.get("descripcion") or "",
                "imagen_src": (
                    f"data:image/jpeg;base64,{p['imagen_base64']}"
                    if p.get("imagen_base64") else ""
                ),
            }
            for p in de_la_base
        ]

    return [
        {
            "nombre": p["nombre"],
            "precio": p["precio"],
            "descripcion": p["descripcion"],
            "imagen_archivo": f"assets/productos/{p['imagen']}",
        }
        for p in PRODUCTOS_FIJOS
    ]


def render():
    tema.aplicar()

    negocio = db.obtener_negocio() if db.disponible() else {}
    telefono = negocio.get("phone", "")

    tema.hero_simple(
        titulo="Productos",
        cinta="Para el cuidado en casa",
        frase="Ceras, pomadas y tratamiento. Pregunta por el que quieras y te lo apartamos.",
    )
    volver.encima_del_hero()

    lista = _lista_de_productos()
    if not lista:
        tema.aviso_vacio("Todavía no hay productos publicados.")
        tema.pie_de_pagina(negocio)
        return

    for producto in lista:
        tema.tarjeta_producto(
            nombre=producto["nombre"],
            precio=_pesos(producto["precio"]),
            descripcion=producto["descripcion"],
            imagen=producto.get("imagen_archivo", ""),
            url_whatsapp=tema.url_whatsapp(telefono, producto["nombre"]),
            imagen_src=producto.get("imagen_src", ""),
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

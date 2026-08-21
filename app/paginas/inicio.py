"""Portada pública: la primera pantalla que ve quien abre el enlace.

Aquí NO se reserva ni se listan los productos. Sólo se presenta la barbería (nombre,
dónde queda, teléfono y horario) y se ofrecen las dos acciones posibles, cada una con
su botón y su propia página: pedir cita o ver el catálogo.

Se separó así a propósito: cuando el formulario de reserva y el catálogo vivían en esta
misma página, bastaba con bajar un poco para toparse con ellos y los botones no
pintaban nada. Además la portada quedaba tan larga que en computador no se alcanzaba a
ver la dirección sin hacer scroll.
"""
from app import db
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

    # Los productos NO se listan aquí a propósito: para eso está el botón "Ver nuestros
    # productos" del hero. Si el catálogo también apareciera abajo, el botón sobraría
    # -- el mismo motivo por el que la reserva se movió a su propia página.
    tema.pie_de_pagina(negocio)


render()

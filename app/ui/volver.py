"""Botón "volver", en su propio módulo y con sus propios estilos.

POR QUÉ NO ESTÁ EN `tema.py`, que sería su sitio natural:

Streamlit Cloud recarga los archivos de PÁGINA cuando cambia el código, pero deja en
memoria los módulos que ya estaban importados (`app/ui/tema.py`, `app/navegacion.py`...).
Resultado: la página nueva llama a una función vieja. Eso tumbó la app dos veces:

  * `ImportError: cannot import name 'admin_config'` -- Aplicacion.py ya pedía el nombre
    nuevo, pero navegacion.py seguía siendo el de antes en memoria.
  * `TypeError` en `hero_simple(volver_a=...)` -- la página ya pasaba el parámetro nuevo
    y tema.py todavía no lo aceptaba.

Un módulo NUEVO no tiene ese problema: como nunca se había importado, no hay versión
vieja en memoria y se carga tal cual. Por eso este botón vive aparte y trae sus propios
estilos en vez de depender del CSS de tema.py, que también podría estar cacheado.

Regla para el futuro: si hay que cambiar la firma de una función de tema.py o de
navegacion.py, hay que reiniciar la app desde Streamlit Cloud después de subir el
cambio, o la app se cae hasta que alguien lo haga.
"""
import streamlit as st

_ESTILO = (
    "position:absolute;top:12px;left:12px;z-index:5;"
    "display:inline-flex;align-items:center;gap:7px;"
    "font-family:'Oswald',sans-serif;font-size:11.5px;"
    "letter-spacing:0.14em;text-transform:uppercase;"
    "color:#E8CE7A;text-decoration:none;"
    "background:rgba(10,11,13,0.55);"
    "border:1px solid rgba(201,162,39,0.4);border-radius:999px;"
    "padding:8px 15px 8px 12px;backdrop-filter:blur(3px);"
)


def html(destino: str = "/", texto: str = "Inicio") -> str:
    """El botón como HTML, para meterlo dentro del hero (que es `position:relative`)."""
    return f'<a href="{destino}" target="_self" style="{_ESTILO}">‹ {texto}</a>'


def encima_del_hero(destino: str = "/", texto: str = "Inicio"):
    """Dibuja el botón por su cuenta, para páginas que no lo meten dentro del hero."""
    st.markdown(
        f'<div style="position:relative;height:0;">{html(destino, texto)}</div>',
        unsafe_allow_html=True,
    )

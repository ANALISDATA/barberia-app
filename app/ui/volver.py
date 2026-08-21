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

# `position: fixed` y no `absolute`: el botón se dibuja DESPUÉS del hero en el orden de
# la página, así que con `absolute` se colocaba justo debajo del hero -- encima de la
# barra de pasos en celular, y en un sitio distinto en computador. Con `fixed` se ancla
# siempre a la esquina de arriba a la izquierda de la pantalla, igual en los dos, y
# sigue ahí al bajar, que es cuando más falta hace.
_ESTILO = (
    "position:fixed;top:10px;left:10px;z-index:9999;"
    "display:inline-flex;align-items:center;gap:7px;"
    "font-family:'Oswald','Arial Narrow',sans-serif;font-size:11.5px;"
    "letter-spacing:0.14em;text-transform:uppercase;"
    "color:#E8CE7A;text-decoration:none;"
    "background:rgba(10,11,13,0.82);"
    "border:1px solid rgba(201,162,39,0.5);border-radius:999px;"
    "padding:9px 16px 9px 13px;"
    "box-shadow:0 4px 14px rgba(0,0,0,0.45);"
)


def html(destino: str = "/", texto: str = "Inicio") -> str:
    """El botón como HTML suelto, por si hay que incrustarlo en otro bloque."""
    return f'<a href="{destino}" target="_self" style="{_ESTILO}">‹ {texto}</a>'


def encima_del_hero(destino: str = "/", texto: str = "Inicio"):
    """Dibuja el botón. Se llama justo después del hero; al ir con posición fija, da
    igual en qué punto de la página se dibuje: siempre sale en la misma esquina."""
    st.markdown(html(destino, texto), unsafe_allow_html=True)

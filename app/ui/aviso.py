"""Avisos que SOBREVIVEN al repintado de la página.

EL PROBLEMA QUE RESUELVE (23/08/2026): al guardar algo, el panel hacía esto:

    st.success("Guardado.")
    st.rerun()

...y el mensaje no se veía nunca. `st.rerun()` borra la pantalla y la vuelve a pintar
desde cero de inmediato, así que el aviso desaparecía en el mismo instante en que se
escribía. El barbero pulsaba "Guardar valores del día", no pasaba nada visible y creía
que el botón estaba roto -- cuando en realidad ya había guardado.

Y el `st.rerun()` hace falta: sin él la página seguiría mostrando los valores viejos,
los que se leyeron de la base de datos ANTES de guardar.

La solución es dejar el mensaje escrito en un papelito (`session_state`, que sí
sobrevive al repintado), repintar, y al empezar la pintada nueva leer el papelito y
mostrarlo. Se lee UNA sola vez: al leerlo se borra, para que no quede pegado en la
pantalla el resto de la sesión.

Módulo NUEVO a propósito -- ver la regla del proyecto en CLAUDE.md.

Cómo se usa:

    aviso.mostrar()                       # arriba de la página, una vez
    ...
    aviso.guardado("Producto actualizado.")   # en vez de st.success + st.rerun
"""
import streamlit as st

_CLAVE = "_aviso_pendiente"


def mostrar() -> None:
    """Pinta el aviso que haya quedado del guardado anterior. Va arriba de la página:
    al repintar, el navegador vuelve al principio, que es donde el barbero está
    mirando."""
    pendiente = st.session_state.pop(_CLAVE, None)
    if not pendiente:
        return

    tipo, texto = pendiente
    {"ok": st.success, "info": st.info, "ojo": st.warning, "error": st.error}.get(
        tipo, st.success
    )(texto)


def _dejar(tipo: str, texto: str) -> None:
    st.session_state[_CLAVE] = (tipo, texto)
    st.rerun()


def guardado(texto: str = "Listo, se guardó.") -> None:
    """Guarda el aviso y repinta la página. No devuelve: `st.rerun()` corta aquí."""
    _dejar("ok", texto)


def informar(texto: str) -> None:
    _dejar("info", texto)


def problema(texto: str) -> None:
    _dejar("error", texto)

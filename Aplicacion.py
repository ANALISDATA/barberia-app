"""Punto de entrada. Enruta entre la página pública de reservas y el panel del administrador.

Se llama `Aplicacion.py` y no `app.py` a propósito, para no chocar con el paquete `app/`
(mismo criterio que `EXTRACCION OP/Aplicacion.py`). Arranca con `▶ ABRIR LA APP.bat`.
"""
import streamlit as st

from app.navegacion import (
    admin_config,
    admin_inicio,
    admin_login,
    cita,
    inicio,
    productos,
)

st.set_page_config(page_title="Barbería", page_icon="💈", layout="centered")

# admin_login (/admin) y admin_inicio (/panel) tienen URLs distintas a proposito.
# Probado en vivo: Streamlit no deja que dos paginas compartan un url_path, ni
# siquiera turnandose segun el estado de sesion -- revienta con "a different page is
# registered for this URL". Por eso admin_login.py cambia de pagina con
# st.switch_page() explicito al loguearse (ver ese archivo), en vez de confiar en que
# la URL "/admin" vaya a coincidir sola con la pagina correcta despues del rerun.

# El cliente que reserva nunca debe ver un enlace al panel del administrador -- por
# eso la navegacion de arriba se oculta del todo (position="hidden") y no se pone
# ningun st.page_link visible para el publico. El administrador entra directo a
# /admin (se lo guarda en favoritos), no navegando desde la pagina de reservas.
# No hay menu lateral a proposito. Lo hubo, con "Inicio" y "Cerrar sesion", pero la
# flecha que lo abre vive dentro de la barra superior de Streamlit, que se oculta para
# que no tape el logo -- y quedaba imposible de pulsar (comprobado en el navegador).
# Ademas su enlace "Inicio" apuntaba a la pagina donde ya estabas. "Cerrar sesion"
# ahora esta al final del panel, a la vista.
if st.session_state.get("admin_autenticado"):
    paginas = [inicio, cita, productos, admin_inicio, admin_config]
else:
    paginas = [inicio, cita, productos, admin_login]

navegacion = st.navigation(paginas, position="hidden")
navegacion.run()

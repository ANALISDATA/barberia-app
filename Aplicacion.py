"""Punto de entrada. Enruta entre la página pública de reservas y el panel del administrador.

Se llama `Aplicacion.py` y no `app.py` a propósito, para no chocar con el paquete `app/`
(mismo criterio que `EXTRACCION OP/Aplicacion.py`). Arranca con `▶ ABRIR LA APP.bat`.
"""
import streamlit as st

st.set_page_config(page_title="Barbería", page_icon="💈", layout="centered")

reservar = st.Page(
    "app/paginas/reservar.py", title="Reservar", icon="💈", default=True, url_path="",
)
admin_login = st.Page(
    "app/paginas/admin_login.py", title="Panel", icon="🔒", url_path="admin",
)
admin_inicio = st.Page(
    "app/paginas/admin_inicio.py", title="Inicio", icon="🏠", url_path="panel",
)

# El cliente que reserva nunca debe ver un enlace al panel del administrador -- por
# eso la navegacion de arriba se oculta del todo (position="hidden") y no se pone
# ningun st.page_link visible para el publico. El administrador entra directo a
# /admin (se lo guarda en favoritos), no navegando desde la pagina de reservas.
if st.session_state.get("admin_autenticado"):
    with st.sidebar:
        st.caption("Sesión de administrador")
        st.page_link(admin_inicio, label="Inicio")
        if st.button("Cerrar sesión"):
            st.session_state["admin_autenticado"] = False
            st.rerun()
    paginas = [reservar, admin_inicio]
else:
    paginas = [reservar, admin_login]

navegacion = st.navigation(paginas, position="hidden")
navegacion.run()

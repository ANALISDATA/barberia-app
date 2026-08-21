"""Punto de entrada. Enruta entre la página pública de reservas y el panel del administrador.

Se llama `Aplicacion.py` y no `app.py` a propósito, para no chocar con el paquete `app/`
(mismo criterio que `EXTRACCION OP/Aplicacion.py`). Arranca con `▶ ABRIR LA APP.bat`.
"""
import streamlit as st

st.set_page_config(page_title="Barbería", page_icon="💈", layout="centered")

reservar = st.Page("app/paginas/reservar.py", title="Reservar", icon="💈", default=True)
admin_login = st.Page("app/paginas/admin_login.py", title="Panel del administrador", icon="🔒")
admin_inicio = st.Page("app/paginas/admin_inicio.py", title="Inicio", icon="🏠")

if st.session_state.get("admin_autenticado"):
    with st.sidebar:
        st.caption("Sesión de administrador")
        if st.button("Cerrar sesión"):
            st.session_state["admin_autenticado"] = False
            st.rerun()
    paginas = [reservar, admin_inicio]
else:
    paginas = [reservar, admin_login]

navegacion = st.navigation(paginas, position="hidden")

with st.sidebar:
    st.page_link(reservar, label="Reservar")
    if st.session_state.get("admin_autenticado"):
        st.page_link(admin_inicio, label="Panel — Inicio")
    else:
        st.page_link(admin_login, label="Panel del administrador")

navegacion.run()

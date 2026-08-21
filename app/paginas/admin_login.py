"""Acceso al panel del administrador -- una sola contraseña, un solo dueño."""
import streamlit as st

from app.ui import tema


def render():
    tema.aplicar()
    st.markdown("### 🔒 Iniciar sesión")

    try:
        clave_correcta = st.secrets.get("admin_password")
    except Exception:
        clave_correcta = None

    if not clave_correcta:
        st.error(
            "Falta configurar `admin_password` en .streamlit/secrets.toml — "
            "sin eso nadie puede entrar al panel."
        )
        return

    with st.form("form_login"):
        clave = st.text_input("Contraseña", type="password")
        enviado = st.form_submit_button("Entrar", type="primary")

    if enviado:
        if clave == clave_correcta:
            st.session_state["admin_autenticado"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")


render()

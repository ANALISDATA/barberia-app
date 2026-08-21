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
            # No basta con st.rerun(): la URL sigue siendo /admin (la de esta pagina),
            # y esa URL no es la del panel (/panel) -- hay que cambiar de pagina a
            # proposito para que el navegador quede en la correcta. st.switch_page()
            # necesita el objeto de pagina real, no un string de ruta (ver
            # app/navegacion.py). El import va aqui adentro (no arriba del archivo) a
            # proposito: st.Page() resuelve rutas relativas al script principal real
            # (Aplicacion.py), y truena si se importa mientras esta pagina se corre
            # aislada (como hacen las pruebas en tests/test_paginas_sin_conexion.py).
            from app.navegacion import admin_inicio

            st.switch_page(admin_inicio)
        else:
            st.error("Contraseña incorrecta.")


render()

"""Acceso al panel del administrador -- una sola contraseña, un solo dueño.

Los estilos van aquí dentro y no en `tema.py` a propósito: `tema.py` es un módulo
compartido y Streamlit Cloud lo sirve cacheado, así que tocarlo tumba la app hasta que
alguien la reinicia (ver CLAUDE.md). Una página siempre se recarga.
"""
import base64
from pathlib import Path

import streamlit as st

from app import db
from app.ui import tema

RUTA_LOGO = "assets/logo.png"

_CSS = """
<style>
/* Portada del login: ocupa la pantalla y centra la tarjeta. */
.login-fondo {
    position: fixed;
    inset: 0;
    z-index: 0;
    background:
        radial-gradient(ellipse 760px 520px at 50% 12%, rgba(201,162,39,0.15) 0%, transparent 62%),
        linear-gradient(178deg, #101215 0%, #0A0B0D 55%, #08090B 100%);
}
.login-fondo::before {
    content: '';
    position: absolute; inset: 0;
    background: repeating-linear-gradient(118deg,
        rgba(232,206,122,0.030) 0px, rgba(232,206,122,0.030) 1px,
        transparent 1px, transparent 26px);
}

.login-marca {
    position: relative;
    z-index: 1;
    text-align: center;
    padding: 22px 0 6px;
}
.login-marca img {
    width: clamp(130px, 34vw, 190px);
    height: auto;
    filter: drop-shadow(0 8px 30px rgba(201,162,39,0.42));
}
.login-nombre {
    font-family: 'Oswald','Arial Narrow',sans-serif;
    font-weight: 700;
    font-size: clamp(22px, 6vw, 34px);
    letter-spacing: 0.02em;
    text-transform: uppercase;
    margin: 10px 0 4px;
    background: linear-gradient(177deg, #FFF6D8 0%, #E8CE7A 38%, #C9A227 62%, #9C7C1B 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 2px 0 #6E5510) drop-shadow(0 5px 12px rgba(0,0,0,0.55));
}
.login-cinta {
    display: flex; align-items: center; justify-content: center; gap: 12px;
    font-family: 'Oswald',sans-serif;
    font-size: 10.5px; letter-spacing: 0.38em; text-indent: 0.38em;
    text-transform: uppercase; color: #8B8579;
    margin-bottom: 4px;
}
.login-cinta i {
    display: block; height: 1px; width: clamp(26px, 10vw, 60px);
    background: linear-gradient(90deg, transparent, #C9A227);
}
.login-cinta i.der { background: linear-gradient(90deg, #C9A227, transparent); }

/* El candado y el aviso, pegados al formulario. */
.login-aviso {
    position: relative; z-index: 1;
    text-align: center;
    font-size: 13px; color: #8B8579;
    margin: 16px 0 6px;
}

/* La tarjeta del formulario: es el st.form de Streamlit, se le da cuerpo. */
div[data-testid="stForm"] {
    position: relative;
    z-index: 1;
    background: rgba(25,28,33,0.92) !important;
    border: 1px solid rgba(201,162,39,0.35) !important;
    border-radius: 6px !important;
    padding: 22px 20px 18px !important;
    box-shadow: 0 18px 50px rgba(0,0,0,0.55) !important;
    backdrop-filter: blur(4px);
}

/* El resto del contenido tiene que quedar por encima del fondo fijo. */
.block-container { position: relative; z-index: 1; }

.login-pie {
    position: relative; z-index: 1;
    text-align: center;
    font-family: 'Oswald',sans-serif;
    font-size: 9.5px; letter-spacing: 0.3em; text-transform: uppercase;
    color: #5F6169;
    margin-top: 26px;
}
</style>
"""


def _logo() -> str:
    try:
        datos = base64.b64encode(Path(RUTA_LOGO).read_bytes()).decode()
        return f'<img src="data:image/png;base64,{datos}" alt="Logo">'
    except FileNotFoundError:
        return ""


def render():
    tema.aplicar()
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown('<div class="login-fondo"></div>', unsafe_allow_html=True)

    negocio = db.obtener_negocio() if db.disponible() else {}
    nombre = negocio.get("name") or "Barbería"

    st.markdown(
        f'<div class="login-marca">{_logo()}'
        f'<div class="login-nombre">{nombre}</div>'
        f'<div class="login-cinta"><i></i>Panel privado<i class="der"></i></div>'
        f"</div>",
        unsafe_allow_html=True,
    )

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

    st.markdown(
        '<div class="login-aviso">🔒 Sólo para el barbero</div>', unsafe_allow_html=True
    )

    with st.form("form_login"):
        clave = st.text_input(
            "Contraseña", type="password", placeholder="Escribe tu contraseña"
        )
        enviado = st.form_submit_button("Entrar", type="primary", width="stretch")

    st.markdown(
        f'<div class="login-pie">{nombre} · Estilo y calidad</div>',
        unsafe_allow_html=True,
    )

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

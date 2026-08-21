"""Registro central de las paginas de la app -- un solo lugar.

Por que existe: `st.switch_page()` necesita el objeto de pagina real (no un string de
ruta) para paginas registradas con `st.Page()` + `st.navigation()` -- un string de ruta
solo funciona con el patron viejo de carpeta `pages/`, que aqui no se usa. Probado en
vivo: usar el string tira `StreamlitAPIException: Could not find page`. Por eso
`Aplicacion.py` y `admin_login.py` (que necesita cambiar de pagina al loguearse)
importan los mismos objetos de aqui, en vez de que cada uno cree los suyos.
"""
import streamlit as st

reservar = st.Page(
    "app/paginas/reservar.py", title="Reservar", icon="💈", default=True, url_path="",
)
admin_login = st.Page(
    "app/paginas/admin_login.py", title="Panel", icon="🔒", url_path="admin",
)
admin_inicio = st.Page(
    "app/paginas/admin_inicio.py", title="Inicio", icon="🏠", url_path="panel",
)

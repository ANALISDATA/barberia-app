"""Registro central de las paginas de la app -- un solo lugar.

Por que existe: `st.switch_page()` necesita el objeto de pagina real (no un string de
ruta) para paginas registradas con `st.Page()` + `st.navigation()` -- un string de ruta
solo funciona con el patron viejo de carpeta `pages/`, que aqui no se usa. Probado en
vivo: usar el string tira `StreamlitAPIException: Could not find page`. Por eso
`Aplicacion.py` y `admin_login.py` (que necesita cambiar de pagina al loguearse)
importan los mismos objetos de aqui, en vez de que cada uno cree los suyos.
"""
import streamlit as st

inicio = st.Page(
    "app/paginas/inicio.py", title="Inicio", icon="💈", default=True, url_path="",
)
cita = st.Page(
    "app/paginas/cita.py", title="Pedir cita", icon="📅", url_path="cita",
)
productos = st.Page(
    "app/paginas/productos.py", title="Productos", icon="🧴", url_path="productos",
)
admin_login = st.Page(
    "app/paginas/admin_login.py", title="Panel", icon="🔒", url_path="admin",
)
admin_inicio = st.Page(
    "app/paginas/admin_inicio.py", title="Inicio", icon="🏠", url_path="panel",
)
admin_dia = st.Page(
    "app/paginas/admin_dia.py", title="Tablero diario", icon="📊", url_path="dia",
)
admin_semana = st.Page(
    "app/paginas/admin_semana.py", title="Semana", icon="📈", url_path="semana",
)
admin_historial = st.Page(
    "app/paginas/admin_historial.py", title="Historial", icon="🏆", url_path="historial",
)
admin_recordar = st.Page(
    "app/paginas/admin_recordar.py", title="Invitar a volver", icon="💬", url_path="recordar",
)
admin_config = st.Page(
    "app/paginas/admin_config.py", title="Configuración", icon="⚙️", url_path="configuracion",
)

# Menú del panel: se recorre para pintar el navegador lateral, así agregar una página
# nueva es añadir una línea aquí y nada más.
MENU_ADMIN = [
    (admin_inicio, "Agenda", "📅"),
    (admin_dia, "Hoy", "📊"),
    (admin_semana, "Semana", "📈"),
    (admin_historial, "Top", "🏆"),
    (admin_recordar, "Volver", "💬"),
    (admin_config, "Ajustes", "⚙️"),
]

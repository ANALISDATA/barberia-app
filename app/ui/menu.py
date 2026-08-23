"""Navegador del panel del administrador.

En módulo aparte y con sus propios estilos, por lo mismo que `volver.py`: Streamlit
Cloud deja cacheados en memoria los módulos ya importados, así que meter esto en
`tema.py` obligaría a reiniciar la app a mano cada vez que se toque. Ver la explicación
completa en `app/ui/volver.py`.

OJO -- por qué son BOTONES y no enlaces, aunque un enlace se vería más limpio:
un enlace recarga la página entera, Streamlit levanta una sesión nueva y se pierde
`admin_autenticado`. El administrador quedaría fuera cada vez que cambia de pestaña, y
la página ni siquiera existiría para esa sesión ("Page not found"). Con `st.switch_page`
no hay recarga y la sesión sigue viva.

En computador el menú va arriba en fila; en celular también, porque una barra lateral
en una pantalla de 390px se come el ancho útil.
"""
import streamlit as st

_CSS = """
<style>
/* Los botones del menú se identifican por la clase que Streamlit le pone al
   contenedor cuando se le pasa `key` (st-key-menu_admin). Sin ese gancho habría que
   estilar TODOS los botones de la app. */
.st-key-menu_admin {
    background: rgba(16,18,21,0.92);
    border: 1px solid #2A2E35;
    border-radius: 4px;
    padding: 6px;
    margin-bottom: 18px;
}
.st-key-menu_admin div[data-testid="stHorizontalBlock"] {
    gap: 4px !important;
    flex-wrap: nowrap !important;
}
.st-key-menu_admin div[data-testid="stColumn"] {
    min-width: 0 !important;
    flex: 1 1 0 !important;
}
.st-key-menu_admin .stButton > button {
    width: 100%;
    padding: 10px 2px !important;
    border: none !important;
    background: transparent !important;
    color: #8B8579 !important;
    font-family: 'Oswald','Arial Narrow',sans-serif !important;
    font-size: 10px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase;
    border-radius: 3px !important;
    line-height: 1.5 !important;
    /* Que la etiqueta nunca se parta en dos lineas: con 5 botones en una pantalla de
       390px, una etiqueta partida descuadra la altura de toda la fila. */
    white-space: nowrap !important;
}
.st-key-menu_admin .stButton > button:hover {
    background: rgba(201,162,39,0.12) !important;
    color: #E8CE7A !important;
}
/* La página en la que se está va con el botón "primary" de Streamlit. */
.st-key-menu_admin .stButton > button[kind="primary"] {
    background: linear-gradient(180deg, #E8CE7A, #C9A227) !important;
    color: #14100A !important;
    font-weight: 600 !important;
}
</style>
"""


def pintar(pagina_actual: str):
    """Dibuja el navegador del panel. `pagina_actual` es el `url_path` de la página en
    la que se está, para resaltarla."""
    from app.navegacion import MENU_ADMIN

    st.markdown(_CSS, unsafe_allow_html=True)

    with st.container(key="menu_admin"):
        columnas = st.columns(len(MENU_ADMIN))
        for columna, (pagina, etiqueta, icono) in zip(columnas, MENU_ADMIN):
            aqui = pagina.url_path == pagina_actual
            if columna.button(
                f"{icono}\n\n{etiqueta}",
                key=f"nav_{pagina.url_path}",
                type="primary" if aqui else "secondary",
                width="stretch",
            ):
                if not aqui:
                    st.switch_page(pagina)

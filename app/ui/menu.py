"""Navegador del panel del administrador: barra lateral con el logo arriba.

En módulo aparte y con sus propios estilos, por lo mismo que `volver.py`: Streamlit
Cloud deja cacheados en memoria los módulos ya importados, así que meter esto en
`tema.py` obligaría a reiniciar la app a mano cada vez que se toque. Ver la explicación
completa en `app/ui/volver.py`.

OJO -- por qué son BOTONES y no enlaces, aunque un enlace se vería más limpio:
un enlace recarga la página entera, Streamlit levanta una sesión nueva y se pierde
`admin_autenticado`. El administrador quedaría fuera cada vez que cambia de pestaña.
Con `st.switch_page` no hay recarga y la sesión sigue viva.

En computador va como columna a la izquierda, con el logo arriba y las opciones debajo.
En celular se convierte en una fila de iconos arriba: una columna lateral en 390px se
comería el ancho útil, y ahí lo que importa es el contenido.
"""
import base64
from pathlib import Path

import streamlit as st

RUTA_LOGO = "assets/logo.png"

_CSS = """
<style>
/* El contenedor se identifica por la clase que Streamlit le pone cuando se le pasa
   `key` (st-key-menu_admin). Sin ese gancho habría que estilar TODOS los botones. */
.st-key-menu_admin {
    background: linear-gradient(180deg, #16181C 0%, #101216 100%);
    border: 1px solid #2A2E35;
    border-radius: 8px;
    padding: 14px 10px 10px;
    margin-bottom: 20px;
    box-shadow: 0 8px 26px rgba(0,0,0,0.35);
}
.menu-marca {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding-bottom: 12px;
    margin-bottom: 10px;
    border-bottom: 1px solid #2A2E35;
}
.menu-marca img {
    width: 92px;
    height: auto;
    filter: drop-shadow(0 4px 16px rgba(201,162,39,0.35));
}
.menu-marca span {
    font-family: 'Oswald','Arial Narrow',sans-serif;
    font-size: 10px;
    letter-spacing: 0.26em;
    text-indent: 0.26em;
    text-transform: uppercase;
    color: #8B8579;
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
    border-radius: 4px !important;
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

/* En computador hay ancho de sobra: el logo crece y el menú respira. */
@media (min-width: 900px) {
    .menu-marca img { width: 118px; }
    .st-key-menu_admin { padding: 18px 14px 12px; }
    .st-key-menu_admin .stButton > button { font-size: 11px !important; padding: 12px 4px !important; }
}
</style>
"""


@st.cache_data(show_spinner=False)
def _logo_incrustado() -> str:
    """El logo como data URI. Cacheado: el archivo no cambia entre recargas."""
    return base64.b64encode(Path(RUTA_LOGO).read_bytes()).decode()


def pintar(pagina_actual: str):
    """Dibuja el navegador del panel. `pagina_actual` es el `url_path` de la página en
    la que se está, para resaltarla."""
    from app.navegacion import MENU_ADMIN

    st.markdown(_CSS, unsafe_allow_html=True)

    with st.container(key="menu_admin"):
        try:
            src = f"data:image/png;base64,{_logo_incrustado()}"
            st.markdown(
                f'<div class="menu-marca"><img src="{src}" alt="Logo">'
                "<span>Panel</span></div>",
                unsafe_allow_html=True,
            )
        except FileNotFoundError:
            # Sin logo el menú sigue sirviendo; sólo pierde la marca.
            pass

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

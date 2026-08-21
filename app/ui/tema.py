"""Identidad visual de la app: paleta, tipografía y estilos reutilizables.

La paleta base (fondo carbón + dorado) ya vive en `.streamlit/config.toml` -- eso pinta los
componentes nativos de Streamlit (botones, inputs). Aquí solo se agrega el CSS que Streamlit
no cubre: la tarjeta de "próximo espacio", las píldoras de estado de las citas y el encabezado
de la página pública. Un solo lugar para todo esto, para no repetir estilos sueltos por cada
página.
"""
import streamlit as st

DORADO = "#C89B3C"
DORADO_SUAVE = "#3A331E"
VERDE_OK = "#4CAF7D"
ROJO_ALERTA = "#D96C6C"
CARBON = "#14161A"
SUPERFICIE = "#1E2126"
TEXTO_SUAVE = "#9AA0A6"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Inter:wght@400;500;600&display=swap');

h1, h2, h3 {{ font-family: 'Fraunces', serif; letter-spacing: -0.01em; }}
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

.tarjeta {{
    background: {SUPERFICIE};
    border: 1px solid #2A2D33;
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 14px;
}}
.tarjeta-dorada {{
    background: linear-gradient(135deg, {DORADO_SUAVE}, {SUPERFICIE});
    border: 1px solid {DORADO};
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 14px;
}}
.etiqueta {{
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {TEXTO_SUAVE};
    margin-bottom: 4px;
}}
.valor-grande {{
    font-family: 'Fraunces', serif;
    font-size: 30px;
    font-weight: 700;
    color: {DORADO};
}}
.pildora {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}}
.pildora-confirmada {{ background: #2A2D33; color: {TEXTO_SUAVE}; }}
.pildora-atendida {{ background: rgba(76,175,125,0.15); color: {VERDE_OK}; }}
.pildora-cancelada {{ background: rgba(217,108,108,0.15); color: {ROJO_ALERTA}; }}
.pildora-no_asistio {{ background: rgba(217,108,108,0.15); color: {ROJO_ALERTA}; }}

.hero-publico {{
    text-align: center;
    padding: 32px 16px 12px;
}}
.hero-publico h1 {{ font-size: 30px; margin-bottom: 4px; }}
.hero-publico p {{ color: {TEXTO_SUAVE}; font-size: 15px; }}
</style>
"""


def aplicar():
    st.markdown(_CSS, unsafe_allow_html=True)


def tarjeta_metrica(etiqueta: str, valor: str, dorada: bool = False):
    clase = "tarjeta-dorada" if dorada else "tarjeta"
    st.markdown(
        f'<div class="{clase}"><div class="etiqueta">{etiqueta}</div>'
        f'<div class="valor-grande">{valor}</div></div>',
        unsafe_allow_html=True,
    )


def pildora_estado(estado: str) -> str:
    etiquetas = {
        "confirmada": "Confirmada",
        "atendida": "Atendida",
        "cancelada": "Cancelada",
        "no_asistio": "No asistió",
    }
    texto = etiquetas.get(estado, estado)
    return f'<span class="pildora pildora-{estado}">{texto}</span>'

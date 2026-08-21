"""Identidad visual de la app: paleta, tipografía, emblema y componentes reutilizables.

Un solo lugar para TODO lo visual. Las páginas no escriben CSS suelto: piden aquí el
componente que necesitan (`hero_publico`, `seccion`, `tarjeta_metrica`, ...).

Dos cosas aprendidas probando en el navegador y que hay que respetar al tocar este archivo:

1. Streamlit pinta sus propios estilos con más prioridad que un selector de clase normal.
   Las reglas que compiten con los suyos (tipografía de h1/h2/h3, colores de botones,
   padding del contenedor principal) necesitan `!important` o se pierden EN SILENCIO --
   la página se ve mal pero no hay ningún error que lo delate.
2. El fondo y los colores base viven en `.streamlit/config.toml` (Streamlit los necesita
   antes de que corra este archivo, para pintar sus widgets). Si se cambia la paleta aquí,
   hay que cambiarla también allá o quedan dos temas peleando.
"""
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Paleta -- mantener sincronizada con .streamlit/config.toml
# ---------------------------------------------------------------------------
NEGRO = "#0A0B0D"          # fondo del hero, el punto más oscuro
CARBON = "#111316"          # fondo general de la app
SUPERFICIE = "#191C21"      # tarjetas
SUPERFICIE_ALTA = "#20242A"  # tarjetas destacadas / hover
LINEA = "#2A2E35"           # bordes y separadores

DORADO = "#C9A227"          # dorado principal (acentos, botones)
DORADO_CLARO = "#E8CE7A"    # dorado claro (títulos grandes)
DORADO_PROFUNDO = "#8A6E15"  # dorado oscuro para degradados

BLANCO_CALIDO = "#F2EDE4"   # texto principal
GRIS_CALIDO = "#8B8579"     # etiquetas, texto secundario
GRIS_TENUE = "#5F6169"      # texto terciario

VERDE_OK = "#5FB98A"
ROJO_ALERTA = "#D97A6C"

_FUENTES = (
    "https://fonts.googleapis.com/css2?"
    "family=Oswald:wght@300;400;500;600;700&"
    "family=Cormorant+Garamond:ital,wght@1,400;1,500&"
    "family=Inter:wght@400;500;600;700&display=swap"
)

# Grano sutil sobre el hero: le quita el aspecto "degradado plano de plantilla".
# Va como data URI para no depender de ningún archivo ni servidor externo.
_GRANO = (
    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' "
    "height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' "
    "baseFrequency='0.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='200' height='200' "
    "filter='url(%23n)' opacity='0.35'/%3E%3C/svg%3E\")"
)

_CSS = f"""
<style>
@import url('{_FUENTES}');

/* ---------- Base ---------- */
html, body, [class*="css"], .stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}
h1, h2, h3, h4 {{
    font-family: 'Oswald', 'Arial Narrow', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    color: {BLANCO_CALIDO} !important;
}}

/* Streamlit deja un hueco arriba del contenido. En la página pública el hero tiene que
   pegar con el borde superior, así que se anula ese hueco -- pero SÓLO el de arriba.
   El margen lateral se conserva a propósito: los widgets de Streamlit (calendario,
   botones, formulario) son hermanos del hero en el DOM, no hijos, así que si se quita
   el padding lateral quedan pegados al borde de la pantalla en celular. El hero se
   sale a lo ancho por su cuenta con el truco de `100vw` de abajo. */
.block-container {{ padding-top: 0 !important; padding-bottom: 3rem !important; }}

/* ---------- HERO ---------- */
.hero {{
    position: relative;
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    background:
        radial-gradient(ellipse 900px 520px at 50% -8%, rgba(201,162,39,0.16) 0%, transparent 62%),
        radial-gradient(ellipse 700px 420px at 50% 108%, rgba(201,162,39,0.06) 0%, transparent 60%),
        linear-gradient(178deg, #101215 0%, {NEGRO} 55%, #08090B 100%);
    overflow: hidden;
    border-bottom: 1px solid {LINEA};
}}
/* Textura: franjas diagonales muy tenues (guiño al poste de barbería) + grano */
.hero::before {{
    content: '';
    position: absolute; inset: 0;
    background:
        repeating-linear-gradient(118deg,
            rgba(232,206,122,0.030) 0px, rgba(232,206,122,0.030) 1px,
            transparent 1px, transparent 26px);
    pointer-events: none;
}}
.hero::after {{
    content: '';
    position: absolute; inset: 0;
    background-image: {_GRANO};
    opacity: 0.05;
    mix-blend-mode: overlay;
    pointer-events: none;
}}
.hero-inner {{
    position: relative;
    z-index: 2;
    text-align: center;
    padding: 34px 22px 30px;
    max-width: 860px;
    margin: 0 auto;
}}

.hero-emblema {{
    display: block;
    margin: 0 auto 12px;
    width: clamp(96px, 19vw, 146px);
    height: auto;
    filter: drop-shadow(0 6px 26px rgba(201,162,39,0.34));
}}

/* Logo pequeño al pie de cada página: la marca acompaña sin estorbar. */
.pie-logo {{
    display: flex; flex-direction: column; align-items: center;
    gap: 8px;
    margin: 40px 0 8px;
    padding-top: 22px;
    border-top: 1px solid {LINEA};
}}
.pie-logo img {{ width: 54px; height: auto; opacity: 0.85; }}
.pie-logo span {{
    font-family: 'Oswald', sans-serif;
    font-size: 10.5px;
    letter-spacing: 0.28em; text-indent: 0.28em; text-transform: uppercase;
    color: {GRIS_TENUE};
}}

/* El nombre va SIEMPRE en una sola línea: se mide en vw (ancho de pantalla) para que
   se encoja solo en vez de partirse en dos. Así la portada ocupa menos alto y en
   computador caben también la dirección, el horario y los productos sin bajar. */
.hero-nombre {{
    font-family: 'Oswald', 'Arial Narrow', sans-serif !important;
    font-weight: 700 !important;
    font-size: clamp(28px, 8.4vw, 74px) !important;
    line-height: 1.02 !important;
    letter-spacing: 0.015em !important;
    text-transform: uppercase;
    white-space: nowrap;
    margin: 0 0 12px !important;
    color: {DORADO_CLARO} !important;
    text-shadow: 0 0 60px rgba(201,162,39,0.30), 0 2px 2px rgba(0,0,0,0.6);
}}

.hero-cinta {{
    display: flex; align-items: center; justify-content: center;
    gap: 16px;
    margin-bottom: 18px;
    font-family: 'Oswald', sans-serif;
    font-weight: 400;
    font-size: 13px;
    letter-spacing: 0.42em;
    text-indent: 0.42em;
    text-transform: uppercase;
    color: {GRIS_CALIDO};
    white-space: nowrap;
}}
.hero-cinta i {{
    display: block; height: 1px; width: clamp(24px, 9vw, 78px); flex: none;
    background: linear-gradient(90deg, transparent, {DORADO});
}}
.hero-cinta i.der {{ background: linear-gradient(90deg, {DORADO}, transparent); }}

.hero-tagline {{
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    font-style: italic;
    font-weight: 400;
    font-size: clamp(17px, 2.2vw, 22px) !important;
    line-height: 1.4 !important;
    color: #CFC8BC !important;
    max-width: 34ch;
    margin: 0 auto 24px !important;
    text-wrap: balance;
}}

.hero-cta {{
    display: inline-block;
    background: linear-gradient(178deg, {DORADO_CLARO} 0%, {DORADO} 52%, {DORADO_PROFUNDO} 100%);
    color: #14100A !important;
    font-family: 'Oswald', sans-serif;
    font-weight: 600;
    font-size: 16px;
    letter-spacing: 0.19em;
    text-indent: 0.19em;
    text-transform: uppercase;
    padding: 17px 46px;
    border: none;
    text-decoration: none !important;
    box-shadow: 0 14px 38px -12px rgba(201,162,39,0.75), inset 0 1px 0 rgba(255,255,255,0.35);
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}}
.hero-cta:hover {{
    transform: translateY(-2px);
    box-shadow: 0 20px 46px -12px rgba(201,162,39,0.9), inset 0 1px 0 rgba(255,255,255,0.45);
}}
.hero-cta:active {{ transform: translateY(0); }}

/* Botón secundario: mismo tamaño y peso que el principal pero en contorno, para que
   se lea como "la otra cosa que puedes hacer aquí" sin competir con pedir la cita. */
.hero-cta2 {{
    display: block;
    width: fit-content;
    margin: 16px auto 0;
    font-family: 'Oswald', sans-serif;
    font-weight: 500;
    font-size: 14px;
    letter-spacing: 0.16em;
    text-indent: 0.16em;
    text-transform: uppercase;
    padding: 13px 32px;
    border: 1px solid rgba(201,162,39,0.55);
    border-radius: 3px;
    color: {DORADO_CLARO} !important;
    text-decoration: none !important;
    transition: all 0.18s ease;
}}
.hero-cta2:hover {{
    background: rgba(201,162,39,0.12);
    border-color: {DORADO};
}}

/* ---------- Barra de datos del negocio ---------- */
.hero-barra {{
    position: relative; z-index: 2;
    display: flex; flex-wrap: wrap;
    border-top: 1px solid {LINEA};
    background: rgba(0,0,0,0.30);
    backdrop-filter: blur(2px);
}}
.barra-col {{
    flex: 1 1 210px;
    padding: 24px 20px;
    text-align: center;
    border-left: 1px solid {LINEA};
    text-decoration: none !important;
    transition: background 0.18s ease;
}}
.barra-col:first-child {{ border-left: none; }}
a.barra-col:hover {{ background: rgba(201,162,39,0.07); }}
.barra-icono {{ display: block; margin: 0 auto 9px; opacity: 0.95; }}
.barra-etiqueta {{
    font-family: 'Oswald', sans-serif;
    font-weight: 500;
    font-size: 11px;
    letter-spacing: 0.26em;
    text-indent: 0.26em;
    text-transform: uppercase;
    color: {DORADO};
    margin-bottom: 7px;
}}
.barra-valor {{
    font-size: 14.5px;
    font-weight: 500;
    color: {BLANCO_CALIDO};
    line-height: 1.5;
}}
a.barra-col .barra-valor {{ color: {BLANCO_CALIDO} !important; }}
.barra-accion {{
    display: inline-block;
    margin-top: 6px;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {DORADO};
    border-bottom: 1px solid rgba(201,162,39,0.45);
    padding-bottom: 1px;
}}

/* ---------- Encabezados de sección ---------- */
.seccion {{ margin: 46px 0 20px; text-align: center; }}
.seccion .eyebrow {{
    font-family: 'Oswald', sans-serif;
    font-weight: 500;
    font-size: 11px;
    letter-spacing: 0.3em;
    text-indent: 0.3em;
    text-transform: uppercase;
    color: {DORADO};
    margin-bottom: 8px;
}}
.seccion h2 {{
    font-size: 30px !important;
    text-transform: uppercase;
    letter-spacing: 0.05em !important;
    margin: 0 0 14px !important;
}}
.seccion .rule {{
    width: 54px; height: 2px; margin: 0 auto;
    background: linear-gradient(90deg, transparent, {DORADO}, transparent);
}}

/* Variante compacta, para el panel del administrador. El encabezado grande y centrado
   funciona en la portada (es una presentación); en el panel sólo aleja los datos, que
   es justo lo contrario de lo que se necesita al abrir la app entre corte y corte. */
.seccion.compacta {{
    text-align: left;
    margin: 30px 0 12px;
    padding-bottom: 9px;
    border-bottom: 1px solid {LINEA};
    display: flex; align-items: baseline; justify-content: space-between; gap: 12px;
}}
.seccion.compacta h2 {{ font-size: 19px !important; margin: 0 !important; }}
.seccion.compacta .eyebrow {{ margin: 0; font-size: 10px; }}
.seccion.compacta .rule {{ display: none; }}

/* ---------- Widgets de Streamlit ---------- */
/* Botones de hora libre: chip con borde dorado. Streamlit los pinta con su propio
   estilo, de ahí los !important. */
.stButton > button {{
    font-family: 'Oswald', sans-serif !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase;
    border-radius: 2px !important;
    border: 1px solid {LINEA} !important;
    background: {SUPERFICIE} !important;
    color: {BLANCO_CALIDO} !important;
    transition: all 0.16s ease !important;
}}
.stButton > button:hover {{
    border-color: {DORADO} !important;
    color: {DORADO_CLARO} !important;
    background: {SUPERFICIE_ALTA} !important;
}}
.stButton > button[kind="primary"], .stFormSubmitButton > button {{
    background: linear-gradient(178deg, {DORADO_CLARO}, {DORADO} 55%, {DORADO_PROFUNDO}) !important;
    color: #14100A !important;
    border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 8px 22px -10px rgba(201,162,39,0.8) !important;
}}
.stFormSubmitButton > button:hover {{ filter: brightness(1.07); }}

/* Inputs */
div[data-baseweb="input"], div[data-baseweb="select"] > div {{
    border-radius: 2px !important;
    border-color: {LINEA} !important;
}}
label, .stRadio label, div[data-testid="stWidgetLabel"] p {{
    font-family: 'Oswald', sans-serif !important;
    font-size: 12px !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase;
    color: {GRIS_CALIDO} !important;
}}

/* ---------- Tarjetas ---------- */
.tarjeta {{
    background: {SUPERFICIE};
    border: 1px solid {LINEA};
    border-radius: 3px;
    padding: 20px 22px;
    margin-bottom: 14px;
}}
.tarjeta-dorada {{
    position: relative;
    background: linear-gradient(140deg, rgba(201,162,39,0.14), {SUPERFICIE} 62%);
    border: 1px solid rgba(201,162,39,0.55);
    border-radius: 3px;
    padding: 22px 24px;
    margin-bottom: 14px;
}}
.etiqueta {{
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.22em;
    text-indent: 0.22em;
    color: {GRIS_CALIDO};
    margin-bottom: 6px;
}}
.valor-grande {{
    font-family: 'Oswald', sans-serif;
    font-size: 34px;
    font-weight: 600;
    line-height: 1.1;
    color: {DORADO_CLARO};
}}
.valor-medio {{
    font-family: 'Oswald', sans-serif;
    font-size: 20px;
    font-weight: 500;
    color: {BLANCO_CALIDO};
}}

/* Rejilla de indicadores. `auto-fit` + `minmax` hace el trabajo responsivo solo:
   3 columnas en computador, 2 en celular, sin media queries ni st.columns (que en
   pantallas angostas aprieta el contenido en vez de apilarlo). */
.metricas {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(148px, 1fr));
    gap: 10px;
    margin-bottom: 16px;
}}
.metrica {{
    background: {SUPERFICIE};
    border: 1px solid {LINEA};
    border-radius: 3px;
    padding: 15px 16px;
}}
.metrica .n {{
    font-family: 'Oswald', sans-serif;
    font-size: 27px; font-weight: 600; line-height: 1.15;
    color: {BLANCO_CALIDO};
}}
.metrica.oro {{ border-color: rgba(201,162,39,0.5); background: linear-gradient(140deg, rgba(201,162,39,0.10), {SUPERFICIE} 70%); }}
.metrica.oro .n {{ color: {DORADO_CLARO}; }}
.metrica.apagada .n {{ color: {GRIS_TENUE}; }}

/* Tarjeta que envuelve una gráfica.
   Se usa `st.container(border=True)` de Streamlit, NO un <div> propio: un div abierto
   con st.markdown no llega a envolver los widgets que vienen después (son hermanos en
   el DOM, no hijos) -- se comprobó viendo el título en su propia caja y la gráfica
   fuera. Aquí sólo se le da el aspecto de la app al contenedor real de Streamlit. */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {SUPERFICIE};
    border-color: {LINEA} !important;
    border-radius: 3px !important;
}}
.panel-titulo {{
    font-family: 'Oswald', sans-serif;
    font-size: 12px; font-weight: 500;
    letter-spacing: 0.2em; text-indent: 0.2em; text-transform: uppercase;
    color: {DORADO};
    margin-bottom: 4px;
}}

/* Saludo del panel */
.saludo {{
    padding: 26px 0 6px;
    border-bottom: 1px solid {LINEA};
    margin-bottom: 22px;
}}
.saludo h1 {{
    font-size: clamp(28px, 6vw, 38px) !important;
    text-transform: uppercase;
    margin: 0 0 4px !important;
    color: {BLANCO_CALIDO} !important;
}}
.saludo .fecha {{
    font-family: 'Oswald', sans-serif;
    font-size: 12px; letter-spacing: 0.2em; text-transform: uppercase;
    color: {GRIS_CALIDO};
}}

/* Fila de cita en el panel */
.fila-cita {{
    display: flex; align-items: center; gap: 14px;
    background: {SUPERFICIE};
    border: 1px solid {LINEA};
    border-left: 2px solid {DORADO};
    border-radius: 3px;
    padding: 13px 18px;
    margin-bottom: 9px;
}}
.fila-cita .hora {{
    font-family: 'Oswald', sans-serif;
    font-size: 19px; font-weight: 600;
    color: {DORADO_CLARO};
    min-width: 68px;
}}
.fila-cita .quien {{ flex: 1; color: {BLANCO_CALIDO}; font-weight: 500; }}
.fila-cita .que {{ color: {GRIS_CALIDO}; font-size: 13.5px; }}

/* Fila de descanso en la vista de la jornada */
.fila-descanso {{
    display: flex; align-items: center; gap: 14px;
    background: repeating-linear-gradient(135deg,
        rgba(255,255,255,0.022) 0 8px, transparent 8px 16px), {CARBON};
    border: 1px dashed {LINEA};
    border-radius: 3px;
    padding: 11px 18px;
    margin-bottom: 9px;
}}
.fila-descanso .hora {{
    font-family: 'Oswald', sans-serif;
    font-size: 14px; color: {GRIS_TENUE}; min-width: 108px;
}}
.fila-descanso .que {{
    font-family: 'Oswald', sans-serif;
    letter-spacing: 0.2em; text-transform: uppercase;
    font-size: 12px; color: {GRIS_CALIDO};
}}
.fila-libre {{ border-left-color: {LINEA} !important; }}
.fila-libre .hora {{ color: {GRIS_CALIDO} !important; }}
.fila-libre .quien {{ color: {GRIS_TENUE} !important; font-weight: 400 !important; }}

.pildora {{
    display: inline-block;
    padding: 3px 11px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}
.pildora-confirmada {{ background: rgba(201,162,39,0.14); color: {DORADO_CLARO}; }}
.pildora-atendida {{ background: rgba(95,185,138,0.15); color: {VERDE_OK}; }}
.pildora-cancelada {{ background: rgba(217,122,108,0.15); color: {ROJO_ALERTA}; }}
.pildora-no_asistio {{ background: rgba(217,122,108,0.15); color: {ROJO_ALERTA}; }}

/* ---------- Catálogo de productos ---------- */
.producto {{
    display: flex;
    gap: 14px;
    align-items: stretch;
    background: {SUPERFICIE};
    border: 1px solid {LINEA};
    border-radius: 3px;
    padding: 12px;
    margin-bottom: 12px;
}}
.producto-foto {{
    flex: 0 0 104px;
    width: 104px; height: 104px;
    border-radius: 2px;
    overflow: hidden;
    background: #FFFFFF;   /* las fotos vienen recortadas sobre fondo blanco */
    display: flex; align-items: center; justify-content: center;
}}
.producto-foto img {{ width: 100%; height: 100%; object-fit: contain; }}
.producto-info {{ flex: 1; min-width: 0; display: flex; flex-direction: column; }}
.producto-nombre {{
    font-family: 'Oswald', sans-serif;
    font-size: 17px; font-weight: 500;
    color: {BLANCO_CALIDO};
    line-height: 1.2;
}}
.producto-precio {{
    font-family: 'Oswald', sans-serif;
    font-size: 20px; font-weight: 600;
    color: {DORADO_CLARO};
    margin: 2px 0 5px;
}}
.producto-desc {{
    font-size: 13px; line-height: 1.45;
    color: {GRIS_CALIDO};
    margin-bottom: 9px;
}}
.producto-wa {{
    align-self: flex-start;
    margin-top: auto;
    font-family: 'Oswald', sans-serif;
    font-size: 12px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {DORADO} !important;
    text-decoration: none !important;
    border: 1px solid rgba(201,162,39,0.45);
    border-radius: 2px;
    padding: 7px 13px;
    transition: all 0.16s ease;
}}
.producto-wa:hover {{
    background: rgba(201,162,39,0.12);
    border-color: {DORADO};
    color: {DORADO_CLARO} !important;
}}
/* Tira de productos de la portada: vistazo rápido al catálogo sin salir de la página */
.tira {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
    gap: 10px;
    margin-bottom: 14px;
}}
.tira-item {{
    background: {SUPERFICIE};
    border: 1px solid {LINEA};
    border-radius: 3px;
    padding: 9px;
    text-align: center;
    text-decoration: none !important;
    transition: border-color 0.16s ease;
}}
.tira-item:hover {{ border-color: rgba(201,162,39,0.6); }}
.tira-item .foto {{
    width: 100%; aspect-ratio: 1; background: #FFF;
    border-radius: 2px; overflow: hidden; margin-bottom: 7px;
}}
.tira-item .foto img {{ width: 100%; height: 100%; object-fit: contain; }}
.tira-item .n {{
    font-size: 11.5px; line-height: 1.3; color: {GRIS_CALIDO};
    display: block; margin-bottom: 2px;
}}
.tira-item .p {{
    font-family: 'Oswald', sans-serif;
    font-size: 14px; font-weight: 600; color: {DORADO_CLARO};
}}

.cierre-catalogo {{
    text-align: center;
    color: {GRIS_CALIDO};
    font-size: 14.5px;
    line-height: 1.6;
    margin: 26px 0 14px;
}}

/* ---------- Confirmación de cita ---------- */
.ticket {{
    background: linear-gradient(150deg, rgba(201,162,39,0.10), {SUPERFICIE} 65%);
    border: 1px solid rgba(201,162,39,0.5);
    border-radius: 3px;
    padding: 34px 26px;
    text-align: center;
    margin-bottom: 22px;
}}
.ticket .dia {{
    font-family: 'Oswald', sans-serif;
    font-size: 13px; letter-spacing: 0.24em; text-transform: uppercase;
    color: {GRIS_CALIDO}; margin-bottom: 10px;
}}
.ticket .hora-grande {{
    font-family: 'Oswald', sans-serif;
    font-size: 62px; font-weight: 700; line-height: 1;
    color: {DORADO_CLARO};
    text-shadow: 0 0 44px rgba(201,162,39,0.3);
    margin-bottom: 12px;
}}
.ticket .detalle {{
    font-size: 15px; color: {BLANCO_CALIDO};
    padding-top: 14px; border-top: 1px dashed rgba(201,162,39,0.4);
}}

.aviso-vacio {{
    background: {SUPERFICIE};
    border: 1px dashed {LINEA};
    border-radius: 3px;
    padding: 26px 20px;
    text-align: center;
    color: {GRIS_CALIDO};
}}

/* Streamlit le pone un icono de enlace (🔗) a cada título al pasar el mouse. En una
   página de cara al cliente sobra: no es documentación, es una barbería. */
h1 a, h2 a, h3 a, .stMarkdown a[href^="#"] svg {{ display: none !important; }}

/* ---------- Móvil ---------- */
@media (max-width: 640px) {{
    .hero-inner {{ padding: 46px 18px 38px; }}
    .hero-cinta {{ font-size: 10px; letter-spacing: 0.3em; gap: 10px; }}
    .barra-col {{ flex-basis: 100%; border-left: none; border-top: 1px solid {LINEA}; }}
    .barra-col:first-child {{ border-top: none; }}
    .ticket .hora-grande {{ font-size: 50px; }}

    /* Por defecto Streamlit apila las columnas una debajo de otra en pantalla angosta.
       Aquí NO conviene: la rejilla de horas quedaría en una sola tira larguísima (15
       horas = 15 filas de scroll). Se fuerzan a quedar lado a lado, que es justo lo
       que hace cómoda la elección con el pulgar. */
    div[data-testid="stHorizontalBlock"] {{
        flex-wrap: nowrap !important;
        gap: 7px !important;
    }}
    div[data-testid="stColumn"] {{
        min-width: 0 !important;
        flex: 1 1 0 !important;
        width: auto !important;
    }}
    .stButton > button {{
        padding-left: 4px !important;
        padding-right: 4px !important;
        font-size: 13px !important;
    }}

    .producto-foto {{ flex-basis: 84px; width: 84px; height: 84px; }}
    .producto-nombre {{ font-size: 15.5px; }}
    .producto-desc {{ font-size: 12.5px; }}
}}
</style>
"""

# Los iconos van dibujados a mano en SVG (no son imágenes externas: así nunca fallan
# por falta de conexión y se ven nítidos en cualquier pantalla).
#
# Van en UNA sola línea a propósito, igual que el resto del HTML de este archivo: un
# salto de línea seguido de espacios convierte el bloque en código para el Markdown de
# Streamlit y el SVG saldría escrito como texto. Ver la nota en `hero_publico`.

RUTA_LOGO = "assets/logo.png"
RUTA_LOGO_PEQUENO = "assets/logo-pequeno.png"

_ICONO_PIN = (
    '<svg class="barra-icono" width="21" height="21" viewBox="0 0 24 24" fill="none"'
    ' xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<path d="M12 21s7-6.03 7-11a7 7 0 1 0-14 0c0 4.97 7 11 7 11z"'
    f' stroke="{DORADO}" stroke-width="1.6" stroke-linejoin="round"/>'
    f'<circle cx="12" cy="10" r="2.6" stroke="{DORADO}" stroke-width="1.6"/></svg>'
)

_ICONO_TEL = (
    '<svg class="barra-icono" width="21" height="21" viewBox="0 0 24 24" fill="none"'
    ' xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<path d="M6.5 3.5h3l1.5 4-2 1.4a12 12 0 0 0 6.1 6.1l1.4-2 4 1.5v3a2 2 0 0 1-2.2 2'
    'A16.5 16.5 0 0 1 4.5 5.7 2 2 0 0 1 6.5 3.5z"'
    f' stroke="{DORADO}" stroke-width="1.6" stroke-linejoin="round"/></svg>'
)

_ICONO_RELOJ = (
    '<svg class="barra-icono" width="21" height="21" viewBox="0 0 24 24" fill="none"'
    ' xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    f'<circle cx="12" cy="12" r="8.6" stroke="{DORADO}" stroke-width="1.6"/>'
    f'<path d="M12 7.2V12l3.1 2" stroke="{DORADO}" stroke-width="1.6" stroke-linecap="round"/></svg>'
)


def aplicar():
    """Inyecta la hoja de estilos. Se llama al principio de cada página."""
    st.markdown(_CSS, unsafe_allow_html=True)


def hero_publico(negocio: dict, resumen_horario: str = "", url_waze: str = ""):
    """Portada: emblema, nombre grande, frase, botón y barra con dirección (enlace a
    Waze), teléfono (enlace para llamar) y horario."""
    nombre = negocio.get("name", "Barbería")
    descripcion = negocio.get("description") or "Corte y barba con cita previa. Sin filas, sin esperas."

    columnas = ""
    if negocio.get("address"):
        columnas += (
            f'<a class="barra-col" href="{url_waze}" target="_blank" rel="noopener">'
            f'{_ICONO_PIN}'
            f'<div class="barra-etiqueta">Dónde estamos</div>'
            f'<div class="barra-valor">{negocio["address"]}</div>'
            f'<span class="barra-accion">Cómo llegar ›</span>'
            f"</a>"
        )
    if negocio.get("phone"):
        solo_digitos = "".join(c for c in negocio["phone"] if c.isdigit())
        columnas += (
            f'<a class="barra-col" href="tel:+57{solo_digitos}">'
            f'{_ICONO_TEL}'
            f'<div class="barra-etiqueta">Contacto</div>'
            f'<div class="barra-valor">{negocio["phone"]}</div>'
            f'<span class="barra-accion">Llamar ›</span>'
            f"</a>"
        )
    if resumen_horario:
        columnas += (
            f'<div class="barra-col">'
            f'{_ICONO_RELOJ}'
            f'<div class="barra-etiqueta">Horario</div>'
            f'<div class="barra-valor">{resumen_horario}</div>'
            f"</div>"
        )
    barra = f'<div class="hero-barra">{columnas}</div>' if columnas else ""

    # OJO: el HTML va SIN indentar y en una sola cadena continua. Streamlit pasa esto
    # por un procesador de Markdown antes de renderizarlo, y Markdown convierte
    # cualquier línea con 4 o más espacios al inicio en un bloque de código -- el HTML
    # aparecería como texto literal en la pantalla. Se detectó exactamente así probando
    # en el navegador. No "ordenar" esto con indentación bonita.
    st.markdown(
        '<div class="hero"><div class="hero-inner">'
        f"{_logo_html()}"
        f'<h1 class="hero-nombre">{nombre}</h1>'
        '<div class="hero-cinta"><i></i>Barbería<i class="der"></i></div>'
        f'<p class="hero-tagline">{descripcion}</p>'
        '<a class="hero-cta" href="/cita" target="_self">Pide aquí tu cita</a>'
        '<a class="hero-cta2" href="/productos" target="_self">Ver nuestros productos</a>'
        f"</div>{barra}</div>",
        unsafe_allow_html=True,
    )


def _logo_html(clase: str = "hero-emblema") -> str:
    """El logo del negocio, incrustado en el HTML. Si el archivo no está, se devuelve
    vacío: la página sigue funcionando, sólo sin logo."""
    try:
        return f'<img class="{clase}" src="{_imagen_incrustada(RUTA_LOGO)}" alt="Logo">'
    except FileNotFoundError:
        return ""


def hero_simple(titulo: str, cinta: str = "", frase: str = "", con_logo: bool = True):
    """Portada corta, para páginas internas (cita, catálogo, confirmación). Mismo
    lenguaje visual que la portada principal pero sin la barra de datos del negocio."""
    cinta_html = (
        f'<div class="hero-cinta"><i></i>{cinta}<i class="der"></i></div>' if cinta else ""
    )
    frase_html = f'<p class="hero-tagline">{frase}</p>' if frase else ""
    logo = (
        f'<img class="hero-emblema" style="width:clamp(64px,12vw,92px);"'
        f' src="{_imagen_incrustada(RUTA_LOGO)}" alt="Logo">'
        if con_logo and Path(RUTA_LOGO).exists()
        else ""
    )
    st.markdown(
        '<div class="hero"><div class="hero-inner" style="padding:30px 22px 28px;">'
        f"{logo}"
        f'<h1 class="hero-nombre" style="font-size:clamp(30px,7.5vw,58px)!important;">{titulo}</h1>'
        f"{cinta_html}{frase_html}</div></div>",
        unsafe_allow_html=True,
    )


def pie_de_pagina(negocio: dict | None = None):
    """Logo pequeño y nombre al final de cada página, para que la marca esté presente
    en todas sin robar espacio arriba."""
    try:
        src = _imagen_incrustada(RUTA_LOGO_PEQUENO)
    except FileNotFoundError:
        return
    nombre = (negocio or {}).get("name", "")
    st.markdown(
        f'<div class="pie-logo"><img src="{src}" alt="Logo">'
        f"<span>{nombre or 'Estilo y calidad'}</span></div>",
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def _imagen_incrustada(ruta: str) -> str:
    """Convierte una imagen del disco en un data URI para poder meterla dentro del HTML
    de la tarjeta. Se hace así (y no con st.image) porque st.image dibuja la imagen en
    su propio bloque, fuera de la tarjeta, y no se puede maquetar al lado del texto.
    Va cacheado: el archivo no cambia entre recargas."""
    import base64
    from pathlib import Path

    datos = Path(ruta).read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(datos).decode()


def tarjeta_producto(
    nombre: str, precio: str, descripcion: str, imagen: str, url_whatsapp: str
):
    try:
        src = _imagen_incrustada(imagen)
        foto = f'<div class="producto-foto"><img src="{src}" alt="{nombre}"></div>'
    except FileNotFoundError:
        # Si falta la foto, la tarjeta sigue siendo útil (nombre, precio y contacto).
        foto = ""

    st.markdown(
        f'<div class="producto">{foto}<div class="producto-info">'
        f'<div class="producto-nombre">{nombre}</div>'
        f'<div class="producto-precio">{precio}</div>'
        f'<div class="producto-desc">{descripcion}</div>'
        f'<a class="producto-wa" href="{url_whatsapp}" target="_blank" rel="noopener">'
        f"Preguntar por este ›</a>"
        f"</div></div>",
        unsafe_allow_html=True,
    )


def tira_productos(productos: list[dict], carpeta: str = "assets/productos"):
    """Vistazo rápido al catálogo en la portada: foto, nombre y precio, y al tocar
    cualquiera se abre el catálogo completo."""
    celdas = ""
    for p in productos:
        try:
            src = _imagen_incrustada(f"{carpeta}/{p['imagen']}")
            foto = f'<div class="foto"><img src="{src}" alt="{p["nombre"]}"></div>'
        except FileNotFoundError:
            foto = ""
        precio = "$" + f"{p['precio']:,.0f}".replace(",", ".")
        celdas += (
            f'<a class="tira-item" href="/productos" target="_self">{foto}'
            f'<span class="n">{p["nombre"]}</span>'
            f'<span class="p">{precio}</span></a>'
        )
    st.markdown(f'<div class="tira">{celdas}</div>', unsafe_allow_html=True)


def url_whatsapp(telefono: str, producto: str = "") -> str:
    """Abre WhatsApp con el mensaje ya escrito. Si se pasa un producto, el mensaje lo
    nombra, para que el cliente no tenga que explicar qué quiere."""
    from urllib.parse import quote

    solo_digitos = "".join(c for c in (telefono or "") if c.isdigit())
    if not solo_digitos:
        return ""
    # Colombia: si viene sin indicativo (10 dígitos), se antepone el 57.
    numero = solo_digitos if solo_digitos.startswith("57") else f"57{solo_digitos}"

    if producto:
        texto = f"¡Hola! Me interesa el producto: {producto}. ¿Está disponible?"
    else:
        texto = "¡Hola! Quiero preguntar por los productos."
    return f"https://wa.me/{numero}?text={quote(texto)}"


def seccion(titulo: str, eyebrow: str = "", ancla: str = "", compacta: bool = False):
    """Encabezado de sección.

    `compacta=True` para el panel del administrador: una sola línea, alineada a la
    izquierda. Sin ella, el encabezado grande de la portada (centrado, con filete) roba
    media pantalla de celular por cada bloque de datos.
    """
    id_attr = f' id="{ancla}"' if ancla else ""
    clase = "seccion compacta" if compacta else "seccion"
    eyebrow_html = f'<div class="eyebrow">{eyebrow}</div>' if eyebrow else ""
    # En la versión compacta el eyebrow va DESPUÉS del título: el flex los separa a
    # lados opuestos y el dato de contexto (la fecha, el rango) queda a la derecha.
    cuerpo = (
        f"<h2>{titulo}</h2>{eyebrow_html}" if compacta
        else f'{eyebrow_html}<h2>{titulo}</h2><div class="rule"></div>'
    )
    st.markdown(f'<div class="{clase}"{id_attr}>{cuerpo}</div>', unsafe_allow_html=True)


def tarjeta_metrica(etiqueta: str, valor: str, dorada: bool = False):
    clase = "tarjeta-dorada" if dorada else "tarjeta"
    st.markdown(
        f'<div class="{clase}"><div class="etiqueta">{etiqueta}</div>'
        f'<div class="valor-grande">{valor}</div></div>',
        unsafe_allow_html=True,
    )


def grid_metricas(items: list[tuple[str, str, str]]):
    """Rejilla de indicadores. Cada item es (etiqueta, valor, tono) donde tono es
    "" (normal), "oro" (destacado) o "apagada" (cuando el valor es cero y no importa)."""
    celdas = "".join(
        f'<div class="metrica {tono}"><div class="etiqueta">{etiqueta}</div>'
        f'<div class="n">{valor}</div></div>'
        for etiqueta, valor, tono in items
    )
    st.markdown(f'<div class="metricas">{celdas}</div>', unsafe_allow_html=True)


def panel(titulo: str):
    """Tarjeta con título que envuelve una gráfica. Se usa como contexto:

        with tema.panel("Jornada"):
            st.altair_chart(...)

    Devuelve el contenedor de Streamlit (no un <div> propio) porque es la única forma
    de que los widgets queden REALMENTE dentro de la tarjeta -- ver la nota del CSS.
    """
    caja = st.container(border=True)
    caja.markdown(f'<div class="panel-titulo">{titulo}</div>', unsafe_allow_html=True)
    return caja


def saludo(texto: str, fecha_texto: str):
    st.markdown(
        f'<div class="saludo"><h1>{texto}</h1><div class="fecha">{fecha_texto}</div></div>',
        unsafe_allow_html=True,
    )


def fila_cita(hora: str, quien: str, que: str, estado_html: str = "", libre: bool = False):
    clase = "fila-cita fila-libre" if libre else "fila-cita"
    st.markdown(
        f'<div class="{clase}"><span class="hora">{hora}</span>'
        f'<span class="quien">{quien}<br><span class="que">{que}</span></span>'
        f"{estado_html}</div>",
        unsafe_allow_html=True,
    )


def fila_descanso(rango: str, etiqueta: str = "Descanso"):
    st.markdown(
        f'<div class="fila-descanso"><span class="hora">{rango}</span>'
        f'<span class="que">{etiqueta}</span></div>',
        unsafe_allow_html=True,
    )


def aviso_vacio(texto: str):
    st.markdown(f'<div class="aviso-vacio">{texto}</div>', unsafe_allow_html=True)


def pildora_estado(estado: str) -> str:
    etiquetas = {
        "confirmada": "Confirmada",
        "atendida": "Atendida",
        "cancelada": "Cancelada",
        "no_asistio": "No asistió",
    }
    texto = etiquetas.get(estado, estado)
    return f'<span class="pildora pildora-{estado}">{texto}</span>'


def url_waze(direccion: str) -> str:
    """Enlace que abre Waze con la ruta ya trazada. En celular abre la app si está
    instalada; en computador abre Waze web."""
    from urllib.parse import quote

    return f"https://waze.com/ul?q={quote(direccion)}&navigate=yes"


def resumen_horario_texto(horario_semanal: dict) -> str:
    """'Lun a Sáb · 7:00am – 8:00pm' cuando todos los días abiertos comparten horario;
    si no, un texto genérico. Es sólo para mostrar en la portada -- la disponibilidad
    real siempre la calcula el motor, nunca este texto."""
    from config import NOMBRES_DIA

    abiertos = {d: h for d, h in horario_semanal.items() if h is not None}
    if not abiertos:
        return ""

    horarios_unicos = set(abiertos.values())
    dias_ordenados = sorted(abiertos.keys())

    def fmt(t) -> str:
        return t.strftime("%I:%M%p").lstrip("0").lower().replace(":00", "")

    if len(horarios_unicos) == 1:
        inicio, fin = next(iter(horarios_unicos))
        primero, ultimo = NOMBRES_DIA[dias_ordenados[0]][:3], NOMBRES_DIA[dias_ordenados[-1]][:3]
        rango = primero if primero == ultimo else f"{primero} a {ultimo}"
        return f"{rango}<br>{fmt(inicio)} – {fmt(fin)}"

    return "Consulta abajo<br>la disponibilidad"

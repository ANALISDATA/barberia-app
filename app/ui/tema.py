"""Identidad visual de la app: paleta, tipografía y estilos reutilizables.

La paleta base (fondo carbón + dorado) ya vive en `.streamlit/config.toml` -- eso pinta los
componentes nativos de Streamlit (botones, inputs). Aquí solo se agrega el CSS que Streamlit
no cubre: la tarjeta de "próximo espacio", las píldoras de estado de las citas y el encabezado
de la página pública. Un solo lugar para todo esto, para no repetir estilos sueltos por cada
página.
"""
import streamlit as st

DORADO = "#C89B3C"
DORADO_CLARO = "#E4C878"
DORADO_SUAVE = "#3A331E"
VERDE_OK = "#4CAF7D"
ROJO_ALERTA = "#D96C6C"
CARBON = "#14161A"
CARBON_HERO = "#0D0F13"
SUPERFICIE = "#1E2126"
TEXTO_SUAVE = "#9AA0A6"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Fraunces:ital,wght@0,600;0,700;1,500&family=Inter:wght@400;500;600&display=swap');

/* Streamlit aplica su propia tipografia a h1/h2/h3 y a los parrafos dentro de
   [data-testid="stMarkdownContainer"] con mas prioridad que un simple selector de clase o
   de etiqueta -- sin !important estas reglas se pierden en silencio (se detecto inspeccionando
   los estilos ya calculados en el navegador, no a simple vista). */
h1, h2, h3 {{ font-family: 'Fraunces', serif !important; letter-spacing: -0.01em; }}
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

/* ---------- Hero de la página pública ---------- */
.hero-full {{
    position: relative;
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    margin-top: -70px;
    margin-bottom: 40px;
    padding: 96px 24px 0;
    background:
        repeating-linear-gradient(115deg, rgba(200,155,60,0.05) 0 2px, transparent 2px 34px),
        radial-gradient(ellipse at 50% 0%, #23262d 0%, {CARBON_HERO} 70%);
    border-bottom: 1px solid #2A2D33;
    text-align: center;
    overflow: hidden;
}}
.hero-marca {{
    font-size: 34px;
    line-height: 1;
    margin-bottom: 18px;
    filter: drop-shadow(0 4px 18px rgba(200,155,60,0.25));
}}
.hero-nombre {{
    font-family: 'Bebas Neue', 'Arial Narrow', sans-serif !important;
    font-size: clamp(48px, 11vw, 108px);
    line-height: 0.92;
    letter-spacing: 0.02em;
    color: {DORADO_CLARO};
    text-shadow: 0 2px 28px rgba(200,155,60,0.18);
    margin: 0 !important;
    text-wrap: balance;
}}
.hero-linea {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
    margin: 14px 0 22px;
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 0.35em;
    font-size: 13px;
    color: #C7CFD9;
}}
.hero-linea .raya {{ width: 46px; height: 1px; background: linear-gradient(90deg, transparent, {DORADO}); }}
.hero-linea .raya.der {{ background: linear-gradient(90deg, {DORADO}, transparent); }}
.hero-tagline {{
    font-family: 'Fraunces', serif !important;
    font-style: italic;
    font-weight: 500;
    font-size: 18px;
    color: #D7DBE0;
    max-width: 46ch;
    margin: 0 auto 34px !important;
    text-wrap: balance;
}}
.hero-cta {{
    display: inline-block;
    background: linear-gradient(180deg, {DORADO_CLARO}, {DORADO});
    color: {CARBON_HERO} !important;
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 0.14em;
    font-size: 18px;
    padding: 15px 42px;
    border-radius: 3px;
    text-decoration: none !important;
    box-shadow: 0 10px 30px -8px rgba(200,155,60,0.55);
    transition: transform 0.15s ease;
}}
.hero-cta:hover {{ transform: translateY(-2px); }}

.info-barra {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0;
    margin-top: 56px;
    border-top: 1px solid #2A2D33;
}}
.info-col {{
    flex: 1 1 200px;
    padding: 20px 18px;
    text-align: center;
    border-left: 1px solid #2A2D33;
}}
.info-col:first-child {{ border-left: none; }}
.info-col .etiqueta {{
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 0.18em;
    color: {DORADO};
    font-size: 12px;
    margin-bottom: 6px;
}}
.info-col .valor {{ color: #E7ECF2; font-size: 15px; font-weight: 500; }}

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

.exito-publico {{
    text-align: center;
    padding: 32px 16px 12px;
}}
.exito-publico h1 {{ font-size: 30px; margin-bottom: 4px; font-family: 'Fraunces', serif; }}
</style>
"""


def aplicar():
    st.markdown(_CSS, unsafe_allow_html=True)


def hero_publico(negocio: dict, resumen_horario: str = ""):
    """Portada de la página pública -- a todo el ancho, tipografía grande, barra de
    dirección/teléfono/horario abajo. `resumen_horario` es un texto ya formateado
    (ver `resumen_horario_texto`), se pasa vacío si no se pudo calcular.
    """
    nombre = negocio.get("name", "Barbería")
    descripcion = negocio.get("description") or "Reserva tu cita en un par de clics"

    columnas = ""
    if negocio.get("address"):
        columnas += (
            f'<div class="info-col"><div class="etiqueta">Dirección</div>'
            f'<div class="valor">{negocio["address"]}</div></div>'
        )
    if negocio.get("phone"):
        columnas += (
            f'<div class="info-col"><div class="etiqueta">Teléfono</div>'
            f'<div class="valor">{negocio["phone"]}</div></div>'
        )
    if resumen_horario:
        columnas += (
            f'<div class="info-col"><div class="etiqueta">Horario</div>'
            f'<div class="valor">{resumen_horario}</div></div>'
        )
    barra = f'<div class="info-barra">{columnas}</div>' if columnas else ""

    st.markdown(
        f"""
        <div class="hero-full">
            <div class="hero-marca">💈</div>
            <h1 class="hero-nombre">{nombre}</h1>
            <div class="hero-linea"><span class="raya"></span>BARBERÍA<span class="raya der"></span></div>
            <p class="hero-tagline">{descripcion}</p>
            <a class="hero-cta" href="#elige-el-dia">Reservar cita</a>
            {barra}
        </div>
        """,
        unsafe_allow_html=True,
    )


def resumen_horario_texto(horario_semanal: dict) -> str:
    """'Lun–Sáb 7:00am–8:00pm' cuando todos los días abiertos comparten horario;
    si no, un texto genérico. Se usa solo para mostrar en la portada -- la
    disponibilidad real siempre la calcula el motor, no este texto."""
    from config import NOMBRES_DIA

    abiertos = {d: h for d, h in horario_semanal.items() if h is not None}
    if not abiertos:
        return ""

    horarios_unicos = set(abiertos.values())
    dias_ordenados = sorted(abiertos.keys())

    def fmt_hora(t) -> str:
        return t.strftime("%I:%M%p").lstrip("0").lower()

    if len(horarios_unicos) == 1:
        inicio, fin = next(iter(horarios_unicos))
        primero, ultimo = NOMBRES_DIA[dias_ordenados[0]][:3], NOMBRES_DIA[dias_ordenados[-1]][:3]
        rango_dias = primero if primero == ultimo else f"{primero}–{ultimo}"
        return f"{rango_dias} {fmt_hora(inicio)}–{fmt_hora(fin)}"

    return "Consulta la disponibilidad abajo"


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

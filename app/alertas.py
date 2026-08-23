"""Alertas de espacio libre: avisar cuando se libera un hueco en la agenda.

En módulo NUEVO, como manda la regla del proyecto (ver CLAUDE.md): meterlo en `db.py`
o `tema.py` tumbaría la app al publicar, porque Streamlit Cloud sirve cacheados los
módulos ya importados.

QUÉ SE CONSIDERA "SE LIBERÓ UN ESPACIO", y por qué:

Lo que hay que avisar es un HECHO NUEVO -- que una cita que estaba en pie se cayó --,
no el estado normal de la agenda. Tener huecos libres es lo corriente y avisarlo cada
rato convertiría la alerta en ruido que se acaba ignorando.

Por eso NO se comparan las horas libres entre una revisión y otra: al empujarse unas a
otras, cancelar una sola cita mueve la hora de todas las siguientes y parecerían diez
huecos nuevos. Lo que se compara son las CITAS ACTIVAS: si una que estaba antes ya no
está (se canceló, o se marcó que no asistió), ese rato quedó libre y ESO es la noticia.

Sobre el sonido: los navegadores no dejan sonar nada hasta que la persona toca algo en
la página. No es algo que se pueda saltar desde el código -- por eso hay un botón para
activarlo al abrir el panel en la mañana, y de ahí en adelante suena solo.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import time
from pathlib import Path

import streamlit as st

from app.db import NEGOCIO_ID, _cliente

RUTA_SONIDO = "assets/alerta.wav"

_CLAVE_CITAS = "alertas_citas_conocidas"
_CLAVE_AVISADAS = "alertas_ya_avisadas"
_CLAVE_SONIDO_LISTO = "alertas_sonido_activado"


@dataclass(frozen=True)
class EspacioLiberado:
    inicio: time
    fin: time
    quien: str

    @property
    def clave(self) -> str:
        """Identifica el espacio para no volver a avisar por lo mismo."""
        return f"{self.inicio}-{self.fin}"

    def rango(self) -> str:
        return f"{self.inicio.strftime('%I:%M %p').lstrip('0')} — " \
               f"{self.fin.strftime('%I:%M %p').lstrip('0')}"


# ---------------------------------------------------------------------------
# Preferencia de sonido (tabla notification_settings, ya existe en el esquema)
# ---------------------------------------------------------------------------

def sonido_encendido() -> bool:
    try:
        r = (
            _cliente()
            .table("notification_settings")
            .select("sound_enabled")
            .eq("business_id", NEGOCIO_ID)
            .single()
            .execute()
        )
        return bool(r.data.get("sound_enabled", True))
    except Exception:
        # Sin la fila o sin la tabla: se asume encendido, que es lo que el barbero espera.
        return True


def guardar_sonido(encendido: bool) -> None:
    cliente = _cliente()
    existe = (
        cliente.table("notification_settings")
        .select("business_id")
        .eq("business_id", NEGOCIO_ID)
        .execute()
    )
    if existe.data:
        cliente.table("notification_settings").update(
            {"sound_enabled": encendido}
        ).eq("business_id", NEGOCIO_ID).execute()
    else:
        cliente.table("notification_settings").insert(
            {"business_id": NEGOCIO_ID, "sound_enabled": encendido}
        ).execute()


# ---------------------------------------------------------------------------
# Detección
# ---------------------------------------------------------------------------

def revisar(citas_del_dia: list[dict]) -> list[EspacioLiberado]:
    """Compara con la revisión anterior y devuelve los espacios que se liberaron.

    `citas_del_dia` son TODAS las citas del día tal como vienen de la base de datos.
    En la primera revisión sólo se toma la foto: no se avisa de nada, porque si no, al
    abrir el panel saltarían alertas de cancelaciones viejas que ya se sabían.
    """
    activas = {
        c["id"]: c
        for c in citas_del_dia
        if c["status"] in ("confirmada", "atendida")
    }

    conocidas = st.session_state.get(_CLAVE_CITAS)
    st.session_state[_CLAVE_CITAS] = set(activas)

    if conocidas is None:
        return []  # primera vez: sólo se toma la foto

    desaparecidas = conocidas - set(activas)
    if not desaparecidas:
        return []

    por_id = {c["id"]: c for c in citas_del_dia}
    liberados = []
    for cita_id in desaparecidas:
        c = por_id.get(cita_id)
        if not c:
            continue
        liberados.append(
            EspacioLiberado(
                inicio=time.fromisoformat(c["start_time"]),
                fin=time.fromisoformat(c["end_time"]),
                quien=(c.get("customers") or {}).get("name", "—"),
            )
        )
    return sorted(liberados, key=lambda e: e.inicio)


def nuevos(liberados: list[EspacioLiberado]) -> list[EspacioLiberado]:
    """Filtra los que ya se avisaron, para no repetir el sonido por lo mismo."""
    avisadas = st.session_state.setdefault(_CLAVE_AVISADAS, set())
    frescos = [e for e in liberados if e.clave not in avisadas]
    for e in frescos:
        avisadas.add(e.clave)
    return frescos


# ---------------------------------------------------------------------------
# Sonido
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _sonido_incrustado() -> str:
    return base64.b64encode(Path(RUTA_SONIDO).read_bytes()).decode()


def sonido_activado() -> bool:
    return bool(st.session_state.get(_CLAVE_SONIDO_LISTO))


def boton_activar_sonido():
    """El navegador no deja sonar nada hasta que la persona toca algo en la página.
    Este botón es ese toque: se pulsa una vez al abrir el panel y de ahí en adelante
    las alertas suenan solas."""
    if st.button("🔔  Activar el sonido de las alertas", width="stretch"):
        st.session_state[_CLAVE_SONIDO_LISTO] = True
        sonar()
        st.rerun()


def sonar():
    """Reproduce la alerta. Sólo suena si el navegador ya lo permite."""
    try:
        datos = _sonido_incrustado()
    except FileNotFoundError:
        return
    st.markdown(
        f'<audio autoplay><source src="data:audio/wav;base64,{datos}" '
        'type="audio/wav"></audio>',
        unsafe_allow_html=True,
    )

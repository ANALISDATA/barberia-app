"""Pruebas de la detección de espacios liberados.

Se prueba con cuidado porque una alerta que no salta deja al barbero con un hueco sin
llenar, y una que salta de más se vuelve ruido que se acaba ignorando -- y entonces
tampoco sirve la que sí importa.

Streamlit guarda el estado en `st.session_state`, que fuera de la app es un objeto
normal: se limpia entre pruebas para que cada una arranque de cero.
"""
import sys
from pathlib import Path

import pytest
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.alertas import nuevos, revisar  # noqa: E402


@pytest.fixture(autouse=True)
def estado_limpio():
    st.session_state.clear()
    yield
    st.session_state.clear()


def cita(cita_id, estado="confirmada", inicio="09:00:00", fin="09:45:00", quien="Carlos"):
    return {
        "id": cita_id,
        "status": estado,
        "start_time": inicio,
        "end_time": fin,
        "customers": {"name": quien, "phone": "300"},
    }


def test_la_primera_revision_no_avisa_de_nada():
    """Al abrir el panel no pueden saltar alertas de cancelaciones viejas: la primera
    pasada sólo toma la foto."""
    assert revisar([cita("a"), cita("b", "cancelada")]) == []


def test_avisa_cuando_una_cita_se_cancela():
    revisar([cita("a"), cita("b")])                      # foto inicial
    liberados = revisar([cita("a"), cita("b", "cancelada")])

    assert len(liberados) == 1
    assert liberados[0].quien == "Carlos"
    assert liberados[0].inicio.strftime("%H:%M") == "09:00"


def test_avisa_cuando_alguien_no_asistio():
    """Si no llegó, ese rato queda libre igual que si hubiera cancelado."""
    revisar([cita("a")])
    liberados = revisar([cita("a", "no_asistio")])
    assert len(liberados) == 1


def test_no_avisa_cuando_una_cita_se_marca_atendida():
    """Atender una cita no libera nada: ese rato se usó."""
    revisar([cita("a")])
    assert revisar([cita("a", "atendida")]) == []


def test_no_avisa_por_una_cita_nueva():
    revisar([cita("a")])
    assert revisar([cita("a"), cita("b", inicio="10:00:00", fin="10:45:00")]) == []


def test_no_avisa_dos_veces_por_lo_mismo():
    """El barbero no puede tener el celular sonando cada rato por la misma cancelación."""
    revisar([cita("a")])
    liberados = revisar([cita("a", "cancelada")])
    assert len(nuevos(liberados)) == 1
    assert nuevos(liberados) == [], "la segunda vez ya no es noticia"


def test_avisa_de_varias_cancelaciones_ordenadas_por_hora():
    revisar([
        cita("tarde", inicio="15:00:00", fin="15:45:00"),
        cita("manana", inicio="08:00:00", fin="08:45:00"),
    ])
    liberados = revisar([
        cita("tarde", "cancelada", inicio="15:00:00", fin="15:45:00"),
        cita("manana", "cancelada", inicio="08:00:00", fin="08:45:00"),
    ])
    assert [e.inicio.strftime("%H:%M") for e in liberados] == ["08:00", "15:00"]


def test_dos_cancelaciones_distintas_avisan_las_dos():
    """Cada espacio se identifica por su hora: dos huecos distintos son dos noticias."""
    revisar([
        cita("a", inicio="08:00:00", fin="08:45:00"),
        cita("b", inicio="09:00:00", fin="09:45:00"),
    ])
    primera = nuevos(revisar([
        cita("a", "cancelada", inicio="08:00:00", fin="08:45:00"),
        cita("b", inicio="09:00:00", fin="09:45:00"),
    ]))
    segunda = nuevos(revisar([
        cita("a", "cancelada", inicio="08:00:00", fin="08:45:00"),
        cita("b", "cancelada", inicio="09:00:00", fin="09:45:00"),
    ]))
    assert len(primera) == 1 and primera[0].inicio.strftime("%H:%M") == "08:00"
    assert len(segunda) == 1 and segunda[0].inicio.strftime("%H:%M") == "09:00"

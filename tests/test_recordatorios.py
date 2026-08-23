"""Pruebas de a quién se le escribe para que vuelva.

Importa acertar: escribirle a quien ya tiene cita para el jueves queda mal, y
escribirle tres veces a la misma persona es la forma más rápida de que bloqueen el
número del barbero.

Se prueba `buscar()` inyectando lo que devolvería la base de datos, sin conexión.
"""
from datetime import date, timedelta

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import recordatorios  # noqa: E402

HOY = date(2026, 8, 23)


class _Respuesta:
    def __init__(self, data):
        self.data = data


class _Consulta:
    """Imita lo justo del cliente de Supabase: select/eq/limit/execute encadenados."""

    def __init__(self, datos):
        self._datos = datos

    def select(self, *_a, **_k):
        return self

    def eq(self, *_a, **_k):
        return self

    def limit(self, *_a, **_k):
        return self

    def execute(self):
        return _Respuesta(self._datos)


class _ClienteFalso:
    def __init__(self, clientes, citas):
        self._tablas = {"customers": clientes, "appointments": citas}

    def table(self, nombre):
        return _Consulta(self._tablas.get(nombre, []))


@pytest.fixture
def montar(monkeypatch):
    def _montar(clientes, citas):
        falso = _ClienteFalso(clientes, citas)
        monkeypatch.setattr(recordatorios, "_cliente", lambda: falso)
        monkeypatch.setattr(recordatorios, "hay_columna_recordatorio", lambda: True)
    return _montar


def cliente(cid, nombre="Carlos Pérez", telefono="3001112233", recordado=None):
    return {"id": cid, "name": nombre, "phone": telefono, "ultimo_recordatorio": recordado}


def cita(cid, dias_atras, estado="atendida", tipo="sin_barba"):
    return {
        "customer_id": cid,
        "date": (HOY - timedelta(days=dias_atras)).isoformat(),
        "status": estado,
        "service_type": tipo,
    }


def test_entra_quien_lleva_15_dias_o_mas_sin_venir(montar):
    montar([cliente("a")], [cita("a", 20)])
    dormidos = recordatorios.buscar(HOY)
    assert len(dormidos) == 1
    assert dormidos[0].dias_sin_venir(HOY) == 20


def test_no_entra_quien_vino_hace_poco(montar):
    montar([cliente("a")], [cita("a", 5)])
    assert recordatorios.buscar(HOY) == []


def test_no_entra_quien_ya_tiene_cita_para_los_proximos_dias(montar):
    """Sería absurdo invitar a volver a quien ya tiene cita el jueves."""
    montar([cliente("a")], [cita("a", 30), cita("a", -4, "confirmada")])
    assert recordatorios.buscar(HOY) == []


def test_una_cita_futura_cancelada_no_lo_salva(montar):
    """Si la canceló, sigue sin volver: hay que invitarlo igual."""
    montar([cliente("a")], [cita("a", 30), cita("a", -4, "cancelada")])
    assert len(recordatorios.buscar(HOY)) == 1


def test_no_entra_quien_nunca_ha_sido_atendido(montar):
    """Alguien que reservó y no llegó no 'vino' hace 30 días: no hay a qué invitarlo."""
    montar([cliente("a")], [cita("a", 30, "no_asistio")])
    assert recordatorios.buscar(HOY) == []


def test_no_se_le_escribe_dos_veces_seguidas(montar):
    """El mismo mensaje tres veces es la forma más rápida de que lo bloqueen."""
    hace_poco = (HOY - timedelta(days=3)).isoformat()
    montar([cliente("a", recordado=hace_poco)], [cita("a", 40)])
    assert recordatorios.buscar(HOY) == []


def test_se_le_vuelve_a_escribir_pasado_un_tiempo(montar):
    viejo = (HOY - timedelta(days=recordatorios.DESCANSO_ENTRE_MENSAJES + 1)).isoformat()
    montar([cliente("a", recordado=viejo)], [cita("a", 40)])
    assert len(recordatorios.buscar(HOY)) == 1


def test_salen_primero_los_que_llevan_mas_tiempo(montar):
    montar(
        [cliente("reciente", "Ana"), cliente("viejo", "Beto")],
        [cita("reciente", 16), cita("viejo", 60)],
    )
    assert [c.nombre for c in recordatorios.buscar(HOY)] == ["Beto", "Ana"]


def test_cuenta_cuantas_veces_ha_venido(montar):
    montar([cliente("a")], [cita("a", 60), cita("a", 40), cita("a", 20)])
    assert recordatorios.buscar(HOY)[0].veces == 3


def test_el_mensaje_saluda_por_el_nombre_y_lleva_el_enlace():
    c = recordatorios.ClienteDormido(
        "1", "carlos pérez", "3001112233", HOY, 3, "sin_barba", None
    )
    texto = recordatorios.mensaje(c, {"name": "Esteban Barber"}, "https://ejemplo.app")
    assert "Carlos" in texto
    assert "https://ejemplo.app" in texto
    assert "Esteban Barber" in texto


def test_el_enlace_de_whatsapp_lleva_indicativo_de_colombia():
    c = recordatorios.ClienteDormido("1", "Ana", "3145900531", HOY, 1, "sin_barba", None)
    url = recordatorios.url_whatsapp(c, "hola")
    assert url.startswith("https://wa.me/573145900531?text=")


def test_sin_telefono_no_hay_enlace():
    c = recordatorios.ClienteDormido("1", "Ana", "", HOY, 1, "sin_barba", None)
    assert recordatorios.url_whatsapp(c, "hola") == ""

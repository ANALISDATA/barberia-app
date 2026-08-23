"""Pruebas de los indicadores del panel.

Se prueban aquí y no en las páginas porque son las que responden preguntas de plata:
un error en "efectividad" o en "ingresos" no se ve a simple vista en la pantalla, se
ve cuando las cuentas del mes no cuadran.
"""
from datetime import date

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.indicadores import (  # noqa: E402
    clientes_nuevos,
    mejor_dia,
    por_dia,
    resumir,
    semana_de,
    top_clientes,
)

LUNES = date(2026, 8, 24)
DOMINGO = date(2026, 8, 30)


def cita(dia, estado="atendida", precio=25000, tipo="sin_barba", quien="Carlos", tel="300"):
    return {
        "date": dia.isoformat(),
        "status": estado,
        "price_at_booking": precio,
        "service_type": tipo,
        "customers": {"name": quien, "phone": tel},
    }


def test_la_semana_va_de_lunes_a_domingo():
    for dia in [LUNES, date(2026, 8, 27), DOMINGO]:
        inicio, fin = semana_de(dia)
        assert inicio == LUNES
        assert fin == DOMINGO
        assert inicio.weekday() == 0 and fin.weekday() == 6


def test_solo_las_atendidas_cuentan_como_corte_y_como_ingreso():
    citas = [
        cita(LUNES, "atendida", 25000),
        cita(LUNES, "atendida", 30000),
        cita(LUNES, "confirmada", 25000),
        cita(LUNES, "cancelada", 25000),
        cita(LUNES, "no_asistio", 25000),
    ]
    r = resumir(citas)
    assert r.atendidas == 2
    assert r.ingresos == 55000, "confirmada, cancelada y no_asistio no pueden sumar"
    assert r.confirmadas == 1 and r.canceladas == 1 and r.no_asistieron == 1


def test_la_cancelada_no_cuenta_como_agendada():
    """Una cancelada libera el espacio, así que no ocupó nada."""
    r = resumir([cita(LUNES, "atendida"), cita(LUNES, "cancelada")])
    assert r.agendadas == 1


def test_efectividad_es_lo_atendido_sobre_lo_agendado():
    # 10 agendadas: 7 atendidas, 2 por atender, 1 plantón -> 70%
    citas = (
        [cita(LUNES, "atendida")] * 7
        + [cita(LUNES, "confirmada")] * 2
        + [cita(LUNES, "no_asistio")]
    )
    assert round(resumir(citas).efectividad) == 70


def test_el_planton_baja_la_efectividad():
    """Si sólo se midiera contra lo confirmado, un día lleno de plantones daría 100%."""
    con_planton = resumir([cita(LUNES, "atendida"), cita(LUNES, "no_asistio")])
    sin_planton = resumir([cita(LUNES, "atendida")])
    assert con_planton.efectividad == 50
    assert sin_planton.efectividad == 100


def test_efectividad_sin_citas_no_revienta():
    assert resumir([]).efectividad == 0
    assert resumir([]).ticket_promedio == 0
    assert resumir([]).ocupacion_sobre(0) == 0


def test_ocupacion_sobre_los_espacios_del_dia():
    citas = [cita(LUNES, "atendida")] * 7
    assert round(resumir(citas).ocupacion_sobre(14)) == 50


def test_ticket_promedio():
    r = resumir([cita(LUNES, "atendida", 25000), cita(LUNES, "atendida", 35000)])
    assert r.ticket_promedio == 30000


def test_por_dia_incluye_los_dias_sin_citas():
    """Un día cerrado y un día flojo no pueden verse igual en la gráfica."""
    filas = por_dia([cita(LUNES, "atendida")], LUNES, DOMINGO)
    assert len(filas) == 7
    assert filas[0][1].atendidas == 1
    assert all(r.atendidas == 0 for _, r in filas[1:])


def test_mejor_dia():
    citas = (
        [cita(LUNES, "atendida")] * 3
        + [cita(date(2026, 8, 26), "atendida")] * 8
        + [cita(date(2026, 8, 28), "atendida")] * 5
    )
    dia, resumen = mejor_dia(citas, LUNES, DOMINGO)
    assert dia == date(2026, 8, 26)
    assert resumen.atendidas == 8


def test_mejor_dia_sin_citas_devuelve_nada():
    assert mejor_dia([], LUNES, DOMINGO) is None


def test_top_clientes_ordena_por_cortes():
    citas = (
        [cita(LUNES, quien="Ana", tel="1")] * 5
        + [cita(LUNES, quien="Beto", tel="2")] * 9
        + [cita(LUNES, quien="Caro", tel="3")] * 2
    )
    top = top_clientes(citas, cuantos=2)
    assert [c.nombre for c in top] == ["Beto", "Ana"]
    assert top[0].cortes == 9


def test_top_clientes_ignora_las_que_no_asistieron():
    """Alguien que reservó diez veces y no llegó nunca no es un buen cliente."""
    citas = [cita(LUNES, "no_asistio", quien="Fantasma", tel="9")] * 10 + [
        cita(LUNES, "atendida", quien="Real", tel="1")
    ]
    top = top_clientes(citas)
    assert [c.nombre for c in top] == ["Real"]


def test_top_clientes_guarda_ultima_visita_y_servicio():
    citas = [
        cita(LUNES, tipo="sin_barba", tel="1"),
        cita(date(2026, 8, 28), tipo="con_barba", tel="1"),
    ]
    top = top_clientes(citas)
    assert top[0].ultima_visita == date(2026, 8, 28)
    assert top[0].ultimo_servicio == "con_barba"
    assert top[0].gastado == 50000


def test_clientes_nuevos_solo_cuenta_primeras_visitas():
    citas = [
        cita(date(2026, 8, 10), tel="viejo"),   # vino antes del periodo
        cita(LUNES, tel="viejo"),               # repite: no es nuevo
        cita(LUNES, tel="nuevo1"),
        cita(date(2026, 8, 26), tel="nuevo2"),
    ]
    assert clientes_nuevos(citas, desde=LUNES) == 2

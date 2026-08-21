"""Pruebas del motor de disponibilidad -- los casos obligatorios del prompt original (parte 55).

Correr con:  python -m pytest tests/test_disponibilidad.py -v
"""
from datetime import date, datetime, time

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.disponibilidad import horarios_disponibles, proximo_espacio  # noqa: E402

LUNES = date(2026, 8, 24)  # lunes real, para pruebas con dia de la semana fijo
DOMINGO = date(2026, 8, 23)

HORARIO_NORMAL = {
    0: (time(7, 0), time(20, 0)),  # lunes
    1: (time(7, 0), time(20, 0)),
    2: (time(7, 0), time(20, 0)),
    3: (time(7, 0), time(20, 0)),
    4: (time(7, 0), time(20, 0)),
    5: (time(7, 0), time(20, 0)),
    6: None,  # domingo cerrado
}
DESCANSOS = {0: [(time(12, 0), time(14, 0))], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
SIN_EXCEPCIONES: dict = {}


def test_caso1_bloques_de_45_minutos_respetando_descanso():
    libres = horarios_disponibles(LUNES, HORARIO_NORMAL, DESCANSOS, SIN_EXCEPCIONES, [])
    # ninguna franja debe caer dentro de 12:00-14:00
    for franja in libres:
        assert not (franja.inicio < time(14, 0) and time(12, 0) < franja.fin)
    # todas duran exactamente 45 minutos
    for franja in libres:
        inicio_dt = datetime.combine(LUNES, franja.inicio)
        fin_dt = datetime.combine(LUNES, franja.fin)
        assert (fin_dt - inicio_dt).seconds == 45 * 60


def test_caso2_cita_que_termina_justo_en_el_cierre_se_permite():
    horario = {0: (time(19, 15), time(20, 0))}
    libres = horarios_disponibles(LUNES, horario, {0: []}, SIN_EXCEPCIONES, [])
    assert len(libres) == 1
    assert libres[0].inicio == time(19, 15)
    assert libres[0].fin == time(20, 0)


def test_caso3_cita_que_pasa_del_cierre_se_rechaza():
    horario = {0: (time(19, 30), time(20, 0))}  # 19:30 + 45min = 20:15 > 20:00
    libres = horarios_disponibles(LUNES, horario, {0: []}, SIN_EXCEPCIONES, [])
    assert libres == []


def test_caso4_cita_que_invade_el_descanso_se_rechaza():
    # 11:30-12:15 invade el descanso 12:00-14:00 -> no debe aparecer como libre
    horario = {0: (time(7, 0), time(20, 0))}
    descansos = {0: [(time(12, 0), time(14, 0))]}
    libres = horarios_disponibles(LUNES, horario, descansos, SIN_EXCEPCIONES, [])
    assert not any(f.inicio == time(11, 30) for f in libres)


def test_caso9_dia_cerrado_no_muestra_disponibilidad():
    libres = horarios_disponibles(DOMINGO, HORARIO_NORMAL, DESCANSOS, SIN_EXCEPCIONES, [])
    assert libres == []


def test_caso10_excepcion_de_horario_se_respeta():
    excepciones = {LUNES: {"closed": False, "start": time(8, 0), "end": time(14, 0)}}
    libres = horarios_disponibles(LUNES, HORARIO_NORMAL, DESCANSOS, excepciones, [])
    assert all(time(8, 0) <= f.inicio for f in libres)
    assert all(f.fin <= time(14, 0) for f in libres)


def test_excepcion_cerrado_prevalece_sobre_horario_normal():
    excepciones = {LUNES: {"closed": True, "start": None, "end": None}}
    libres = horarios_disponibles(LUNES, HORARIO_NORMAL, DESCANSOS, excepciones, [])
    assert libres == []


def test_cita_existente_bloquea_su_horario():
    horario = {0: (time(7, 0), time(9, 15))}
    citas = [(time(7, 45), time(8, 30))]
    libres = horarios_disponibles(LUNES, horario, {0: []}, SIN_EXCEPCIONES, citas)
    horas = [f.inicio for f in libres]
    assert time(7, 45) not in horas
    assert time(7, 0) in horas
    assert time(8, 30) in horas


def test_caso5_cancelar_libera_el_horario():
    horario = {0: (time(7, 0), time(9, 0))}
    con_cita = horarios_disponibles(LUNES, horario, {0: []}, SIN_EXCEPCIONES, [(time(7, 45), time(8, 30))])
    sin_cita = horarios_disponibles(LUNES, horario, {0: []}, SIN_EXCEPCIONES, [])  # cita cancelada = no se manda
    assert time(7, 45) not in [f.inicio for f in con_cita]
    assert time(7, 45) in [f.inicio for f in sin_cita]


def test_no_muestra_horas_que_ya_pasaron_hoy():
    horario = {0: (time(7, 0), time(11, 0))}
    ahora = datetime.combine(LUNES, time(8, 0))
    libres = horarios_disponibles(LUNES, horario, {0: []}, SIN_EXCEPCIONES, [], ahora=ahora)
    assert all(f.inicio > time(8, 0) or f.inicio >= time(8, 0) for f in libres)
    assert time(7, 0) not in [f.inicio for f in libres]
    assert time(7, 45) not in [f.inicio for f in libres]
    assert time(8, 30) in [f.inicio for f in libres]


def test_la_tarde_arranca_justo_al_terminar_el_descanso():
    """Reportado por el usuario probando en vivo: tras el descanso de 12:00-14:00 la
    primera hora libre salía a las 14:30 en vez de las 14:00, porque la rejilla venía
    corrida desde las 7:00 y el bloque de 13:45 se descartaba por chocar con el
    descanso. Se perdían 30 minutos de agenda todos los días."""
    libres = horarios_disponibles(LUNES, HORARIO_NORMAL, DESCANSOS, SIN_EXCEPCIONES, [])
    horas = [f.inicio for f in libres]
    assert time(14, 0) in horas       # la tarde arranca en punto, no a las 14:30
    assert time(14, 30) not in horas  # 14:30 sería la secuencia vieja, corrida
    assert time(11, 30) not in horas  # invadiría el descanso
    # La mañana termina en 10:45-11:30: de 11:30 a 12:00 quedan 30 minutos, que no
    # alcanzan para un corte de 45. Ese hueco es real y no se puede aprovechar.
    assert libres[5].inicio == time(10, 45)
    assert libres[6].inicio == time(14, 0)


def test_el_ultimo_bloque_cierra_exacto_a_la_hora_de_cierre():
    """La regla del negocio dice que 19:15-20:00 sí se permite. Con la rejilla corrida
    desde las 7:00 el último bloque quedaba en 19:00 y se desperdiciaban 15 minutos."""
    libres = horarios_disponibles(LUNES, HORARIO_NORMAL, DESCANSOS, SIN_EXCEPCIONES, [])
    assert libres[-1].inicio == time(19, 15)
    assert libres[-1].fin == time(20, 0)


def test_las_horas_salen_en_orden_sin_solaparse_y_dentro_de_la_jornada():
    libres = horarios_disponibles(LUNES, HORARIO_NORMAL, DESCANSOS, SIN_EXCEPCIONES, [])
    horas = [f.inicio for f in libres]

    assert horas == sorted(horas), "las horas deben salir de la más temprana a la más tarde"
    assert len(horas) == len(set(horas)), "no puede haber horas repetidas"

    for anterior, siguiente in zip(libres, libres[1:]):
        assert anterior.fin <= siguiente.inicio, "dos bloques no se pueden solapar"

    for f in libres:
        assert time(7, 0) <= f.inicio and f.fin <= time(20, 0)
        assert not (f.inicio < time(14, 0) and time(12, 0) < f.fin), "invade el descanso"


def test_la_duracion_se_puede_cambiar():
    horario = {0: (time(7, 0), time(9, 0))}
    de_30 = horarios_disponibles(
        LUNES, horario, {0: []}, SIN_EXCEPCIONES, [], duracion=30
    )
    assert [f.inicio for f in de_30] == [time(7, 0), time(7, 30), time(8, 0), time(8, 30)]
    assert de_30[0].fin == time(7, 30)

    de_60 = horarios_disponibles(
        LUNES, horario, {0: []}, SIN_EXCEPCIONES, [], duracion=60
    )
    assert [f.inicio for f in de_60] == [time(7, 0), time(8, 0)]


def test_proximo_espacio_cambia_segun_la_hora_actual():
    horario = {0: (time(7, 0), time(11, 0))}
    temprano = proximo_espacio(LUNES, horario, {0: []}, SIN_EXCEPCIONES, [], ahora=datetime.combine(LUNES, time(7, 0)))
    tarde = proximo_espacio(LUNES, horario, {0: []}, SIN_EXCEPCIONES, [], ahora=datetime.combine(LUNES, time(8, 0)))
    assert temprano.inicio == time(7, 0)
    assert tarde.inicio == time(8, 30)

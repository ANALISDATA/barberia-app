"""Motor central de disponibilidad de citas.

Toda la aplicacion -- la pagina donde reserva el cliente, el contador
"Disponibles" del panel, el calendario, la tarjeta "Proximo espacio" y las
alertas de espacio libre -- usa UNICAMENTE la funcion `horarios_disponibles`
de este archivo. Nunca se duplica esta logica en otro lado: si un dia se
necesita cambiar una regla (por ejemplo, cuanto antes se puede reservar),
se cambia aqui una sola vez y toda la app queda consistente.

No depende de Streamlit ni de Supabase -- son funciones puras (mismos datos
de entrada, mismo resultado siempre), por eso se pueden probar con
`tests/test_disponibilidad.py` sin necesitar conexion a nada.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

DURACION_MINUTOS = 45


@dataclass(frozen=True)
class Franja:
    """Un bloque de tiempo libre u ocupado, siempre de 45 minutos."""

    inicio: time
    fin: time

    def se_solapa_con(self, otro_inicio: time, otro_fin: time) -> bool:
        return self.inicio < otro_fin and otro_inicio < self.fin


@dataclass(frozen=True)
class HorarioDia:
    """Horario de apertura de un dia concreto, ya resuelto (normal o excepcion)."""

    cerrado: bool
    apertura: time | None
    cierre: time | None
    descansos: list[tuple[time, time]]


def resolver_horario_del_dia(
    fecha: date,
    horario_semanal: dict[int, tuple[time, time] | None],
    descansos_por_dia: dict[int, list[tuple[time, time]]],
    excepciones: dict[date, dict],
) -> HorarioDia:
    """Decide el horario real de un dia: excepcion si existe, si no el semanal.

    `horario_semanal`: {0: (apertura, cierre), 1: None (cerrado), ...} -- 0 = lunes .. 6 = domingo
        (Python: date.weekday(), NO confundir con day_of_week de la base de datos que usa 0=domingo).
    `excepciones`: {fecha: {"closed": bool, "start": time|None, "end": time|None}}
    """
    excepcion = excepciones.get(fecha)
    if excepcion is not None:
        if excepcion.get("closed"):
            return HorarioDia(cerrado=True, apertura=None, cierre=None, descansos=[])
        return HorarioDia(
            cerrado=False,
            apertura=excepcion["start"],
            cierre=excepcion["end"],
            descansos=[],  # una excepcion de horario reemplaza tambien los descansos del dia
        )

    dia_semana = fecha.weekday()
    horario_normal = horario_semanal.get(dia_semana)
    if horario_normal is None:
        return HorarioDia(cerrado=True, apertura=None, cierre=None, descansos=[])

    apertura, cierre = horario_normal
    return HorarioDia(
        cerrado=False,
        apertura=apertura,
        cierre=cierre,
        descansos=descansos_por_dia.get(dia_semana, []),
    )


def _generar_bloques(apertura: time, cierre: time) -> list[Franja]:
    """Bloques de 45 min desde la apertura, mientras inicio + 45min <= cierre."""
    bloques: list[Franja] = []
    cursor = datetime.combine(date.today(), apertura)
    fin_jornada = datetime.combine(date.today(), cierre)
    paso = timedelta(minutes=DURACION_MINUTOS)

    while cursor + paso <= fin_jornada:
        bloques.append(Franja(inicio=cursor.time(), fin=(cursor + paso).time()))
        cursor += paso

    return bloques


def horarios_disponibles(
    fecha: date,
    horario_semanal: dict[int, tuple[time, time] | None],
    descansos_por_dia: dict[int, list[tuple[time, time]]],
    excepciones: dict[date, dict],
    citas_activas: list[tuple[time, time]],
    ahora: datetime | None = None,
) -> list[Franja]:
    """Calcula las horas realmente libres de un dia. La UNICA fuente de verdad.

    `citas_activas`: horas ya ocupadas ese dia (estado distinto de "cancelada").
    `ahora`: se recibe por parametro (no se usa datetime.now() adentro) para que las
        pruebas puedan fijar una hora exacta sin depender del reloj real.
    """
    horario = resolver_horario_del_dia(fecha, horario_semanal, descansos_por_dia, excepciones)
    if horario.cerrado or horario.apertura is None or horario.cierre is None:
        return []

    libres = []
    for bloque in _generar_bloques(horario.apertura, horario.cierre):
        si_choca_descanso = any(
            bloque.se_solapa_con(d_inicio, d_fin) for d_inicio, d_fin in horario.descansos
        )
        if si_choca_descanso:
            continue

        si_choca_cita = any(
            bloque.se_solapa_con(c_inicio, c_fin) for c_inicio, c_fin in citas_activas
        )
        if si_choca_cita:
            continue

        if ahora is not None and fecha == ahora.date() and bloque.inicio < ahora.time():
            continue

        libres.append(bloque)

    return libres


def proximo_espacio(
    fecha: date,
    horario_semanal: dict[int, tuple[time, time] | None],
    descansos_por_dia: dict[int, list[tuple[time, time]]],
    excepciones: dict[date, dict],
    citas_activas: list[tuple[time, time]],
    ahora: datetime,
) -> Franja | None:
    """El primer espacio libre de hoy en adelante. Usado por la tarjeta 'Proximo espacio'."""
    libres = horarios_disponibles(
        fecha, horario_semanal, descansos_por_dia, excepciones, citas_activas, ahora=ahora
    )
    return libres[0] if libres else None

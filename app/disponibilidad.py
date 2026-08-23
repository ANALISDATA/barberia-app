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

# Valor por defecto cuando nadie dice otra cosa. La duracion REAL de una cita se
# guarda en la base de datos (services.duration_minutes) y se pasa por parametro a
# `horarios_disponibles`, para poder cambiarla sin tocar codigo.
DURACION_MINUTOS = 45

# Fecha de apoyo para hacer cuentas con horas. Ver la nota en `_generar_bloques`.
_DIA_CUALQUIERA = date(2000, 1, 1)


@dataclass(frozen=True)
class Franja:
    """Un bloque de tiempo: una cita ocupada o un espacio libre."""

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


def _tramos_abiertos(
    apertura: time, cierre: time, descansos: list[tuple[time, time]]
) -> list[tuple[time, time]]:
    """Parte la jornada en los ratos en los que de verdad se atiende, quitando los
    descansos. Un día de 7:00 a 20:00 con descanso de 12:00 a 14:00 da dos tramos:
    (7:00, 12:00) y (14:00, 20:00)."""
    tramos: list[tuple[time, time]] = []
    cursor = apertura
    for inicio_d, fin_d in sorted(descansos):
        if inicio_d > cursor:
            tramos.append((cursor, min(inicio_d, cierre)))
        cursor = max(cursor, fin_d)
        if cursor >= cierre:
            break
    if cursor < cierre:
        tramos.append((cursor, cierre))
    return [(a, b) for a, b in tramos if a < b]


def _ratos_libres(
    apertura: time,
    cierre: time,
    descansos: list[tuple[time, time]],
    citas: list[tuple[time, time]],
) -> list[tuple[time, time, bool]]:
    """Los ratos de la jornada que no están ocupados por un descanso ni por una cita.

    Devuelve `(inicio, fin, se_puede_pasar)`. `se_puede_pasar` dice si lo que viene
    justo después es tiempo del barbero (un descanso o el cierre) y no otra cita: sólo
    ahí tiene sentido permitir que una cita se pase unos minutos.
    """
    ocupado = sorted(
        [(a, b, False) for a, b in citas] + [(a, b, True) for a, b in descansos]
    )

    libres: list[tuple[time, time, bool]] = []
    cursor = apertura
    for inicio_o, fin_o, es_descanso in ocupado:
        if inicio_o > cursor:
            libres.append((cursor, min(inicio_o, cierre), es_descanso))
        cursor = max(cursor, fin_o)
        if cursor >= cierre:
            break
    if cursor < cierre:
        # Lo que hay después del último rato es el cierre: también es tiempo suyo.
        libres.append((cursor, cierre, True))

    return [(a, b, t) for a, b, t in libres if a < b]


def _generar_bloques(
    apertura: time,
    cierre: time,
    descansos: list[tuple[time, time]],
    duracion: int,
    citas: list[tuple[time, time]] = (),
    tolerancia: int = 0,
) -> list[Franja]:
    """Las horas que se pueden ofrecer, pegadas unas a otras.

    Los bloques se generan desde el inicio de CADA rato libre, no sobre una rejilla
    fija del día. Es la diferencia entre aprovechar la agenda y desperdiciarla:

      * Rejilla fija: unas cejas de 15 min a las 7:00 dejaban el siguiente corte en
        las 7:45 (la casilla de la rejilla), tirando a la basura 7:15-7:45.
      * Pegado: el siguiente corte arranca a las 7:15, y a partir de ahí todo se
        recalcula solo cada vez que entra una cita.

    Por la misma razón cada tramo arranca en su propio inicio: sin eso, tras el
    descanso de 12:00-14:00 la tarde empezaba a las 14:30 en vez de las 14:00.

    `tolerancia` son los minutos que una cita puede pasarse del descanso o del cierre
    para no dejar ese rato muerto. NUNCA se aplica contra otra cita: pasarse del
    descanso es meterse en el tiempo del barbero; pasarse de una cita sería poner dos
    personas a la misma hora.
    """
    bloques: list[Franja] = []
    paso = timedelta(minutes=duracion)
    margen = timedelta(minutes=tolerancia)
    # Fecha cualquiera: sólo se usa para poder sumar minutos a una hora (datetime sabe
    # sumar, time no). De aquí sólo salen horas, nunca fechas, así que da igual cuál
    # sea -- NO es la fecha del día que se está calculando.
    hoy = _DIA_CUALQUIERA

    for rato_inicio, rato_fin, se_puede_pasar in _ratos_libres(
        apertura, cierre, descansos, list(citas)
    ):
        cursor = datetime.combine(hoy, rato_inicio)
        limite = datetime.combine(hoy, rato_fin)
        tope = limite + margen if se_puede_pasar else limite

        while cursor + paso <= tope:
            fin = cursor + paso
            # El día no puede desbordarse a la madrugada del día siguiente.
            if fin.date() != cursor.date():
                break
            bloques.append(Franja(inicio=cursor.time(), fin=fin.time()))
            cursor = fin

    return sorted(bloques, key=lambda f: f.inicio)


def horarios_disponibles(
    fecha: date,
    horario_semanal: dict[int, tuple[time, time] | None],
    descansos_por_dia: dict[int, list[tuple[time, time]]],
    excepciones: dict[date, dict],
    citas_activas: list[tuple[time, time]],
    ahora: datetime | None = None,
    duracion: int = DURACION_MINUTOS,
    tolerancia: int = 0,
) -> list[Franja]:
    """Calcula las horas realmente libres de un dia. La UNICA fuente de verdad.

    `citas_activas`: horas ya ocupadas ese dia (estado distinto de "cancelada"). No se
        usan sólo para descartar bloques: son las que definen dónde empieza cada
        bloque, porque las horas se pegan a lo que ya está reservado.
    `ahora`: se recibe por parametro (no se usa datetime.now() adentro) para que las
        pruebas puedan fijar una hora exacta sin depender del reloj real.
    `duracion`: minutos que dura la cita. Cada servicio tiene la suya.
    `tolerancia`: minutos que una cita puede pasarse del descanso o del cierre para no
        dejar ese rato muerto. Nunca se aplica contra otra cita.
    """
    horario = resolver_horario_del_dia(fecha, horario_semanal, descansos_por_dia, excepciones)
    if horario.cerrado or horario.apertura is None or horario.cierre is None:
        return []

    bloques = _generar_bloques(
        horario.apertura, horario.cierre, horario.descansos, duracion,
        citas=citas_activas, tolerancia=tolerancia,
    )

    if ahora is None or fecha != ahora.date():
        return bloques
    return [b for b in bloques if b.inicio >= ahora.time()]


@dataclass(frozen=True)
class Hueco:
    """Un rato de la jornada que no se puede vender."""

    inicio: time
    fin: time
    minutos: int
    es_descanso: bool  # True = descanso configurado; False = sobrante sin usar


def analizar_jornada(
    fecha: date,
    horario_semanal: dict[int, tuple[time, time] | None],
    descansos_por_dia: dict[int, list[tuple[time, time]]],
    excepciones: dict[date, dict],
    duracion: int = DURACION_MINUTOS,
) -> tuple[list[Franja], list[Hueco]]:
    """Radiografía del día completo: todos los bloques vendibles y todos los huecos.

    Sirve para responder "¿por qué me queda tiempo muerto?" sin adivinar. Un hueco con
    `es_descanso=False` es tiempo que se pierde por pura aritmética: si la jornada de
    la mañana dura 300 minutos y cada corte son 45, caben 6 cortes (270) y sobran 30
    minutos que no alcanzan para otro. Esos sobrantes se pegan al descanso de al lado
    (ver `descansos_efectivos`) para que no queden flotando en mitad de la agenda.
    """
    horario = resolver_horario_del_dia(fecha, horario_semanal, descansos_por_dia, excepciones)
    if horario.cerrado or horario.apertura is None or horario.cierre is None:
        return [], []

    bloques = _generar_bloques(horario.apertura, horario.cierre, horario.descansos, duracion)
    huecos: list[Hueco] = []
    hoy = _DIA_CUALQUIERA  # ver la nota de _generar_bloques

    def minutos_entre(a: time, b: time) -> int:
        return int(
            (datetime.combine(hoy, b) - datetime.combine(hoy, a)).total_seconds() // 60
        )

    descansos = sorted(horario.descansos)
    cursor = horario.apertura
    for bloque in bloques:
        if bloque.inicio > cursor:
            # Todo lo que hay entre el fin del bloque anterior y el inicio de este es
            # hueco. Puede ser descanso, sobrante, o los dos pegados.
            for inicio_h, fin_h in _partir_hueco(cursor, bloque.inicio, descansos):
                es_descanso = any(
                    inicio_h >= d0 and fin_h <= d1 for d0, d1 in descansos
                )
                huecos.append(
                    Hueco(inicio_h, fin_h, minutos_entre(inicio_h, fin_h), es_descanso)
                )
        cursor = bloque.fin

    if cursor < horario.cierre:
        for inicio_h, fin_h in _partir_hueco(cursor, horario.cierre, descansos):
            es_descanso = any(inicio_h >= d0 and fin_h <= d1 for d0, d1 in descansos)
            huecos.append(
                Hueco(inicio_h, fin_h, minutos_entre(inicio_h, fin_h), es_descanso)
            )

    return bloques, huecos


def _partir_hueco(
    inicio: time, fin: time, descansos: list[tuple[time, time]]
) -> list[tuple[time, time]]:
    """Corta un hueco en los pedazos que son descanso y los que no, para poder
    distinguirlos. Sin esto, el rato de 11:30 a 14:00 se veria como un solo bloque y no
    se sabria que 30 minutos de ahi son sobrante y 120 son el almuerzo."""
    cortes = {inicio, fin}
    for d0, d1 in descansos:
        if inicio < d0 < fin:
            cortes.add(d0)
        if inicio < d1 < fin:
            cortes.add(d1)
    ordenados = sorted(cortes)
    return list(zip(ordenados, ordenados[1:]))


def descansos_efectivos(
    fecha: date,
    horario_semanal: dict[int, tuple[time, time] | None],
    descansos_por_dia: dict[int, list[tuple[time, time]]],
    excepciones: dict[date, dict],
    duracion: int = DURACION_MINUTOS,
) -> list[tuple[time, time]]:
    """Los descansos tal como se ven de verdad en la agenda, con el sobrante pegado.

    Regla del negocio: el único tiempo muerto del día debe ser el descanso. Si la
    mañana deja 30 minutos que no alcanzan para un corte, esos 30 minutos no quedan
    "volando" sueltos: pasan a ser parte del descanso. Nada se pierde (en 30 minutos no
    cabe un corte de 45 igual), pero la agenda queda limpia y se lee de corrido.
    """
    _, huecos = analizar_jornada(
        fecha, horario_semanal, descansos_por_dia, excepciones, duracion
    )
    if not huecos:
        return []

    # Se juntan los huecos que se tocan; el resultado son los ratos muertos reales.
    fusionados: list[list[time]] = []
    for h in huecos:
        if fusionados and fusionados[-1][1] == h.inicio:
            fusionados[-1][1] = h.fin
        else:
            fusionados.append([h.inicio, h.fin])
    return [(a, b) for a, b in fusionados]


def proximo_espacio(
    fecha: date,
    horario_semanal: dict[int, tuple[time, time] | None],
    descansos_por_dia: dict[int, list[tuple[time, time]]],
    excepciones: dict[date, dict],
    citas_activas: list[tuple[time, time]],
    ahora: datetime,
    duracion: int = DURACION_MINUTOS,
) -> Franja | None:
    """El primer espacio libre de hoy en adelante. Usado por la tarjeta 'Proximo espacio'."""
    libres = horarios_disponibles(
        fecha, horario_semanal, descansos_por_dia, excepciones, citas_activas,
        ahora=ahora, duracion=duracion,
    )
    return libres[0] if libres else None

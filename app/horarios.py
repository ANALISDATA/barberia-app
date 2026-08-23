"""Puerta de entrada al motor de disponibilidad, a prueba de despliegues a medias.

POR QUÉ EXISTE ESTE ENVOLTORIO:

Streamlit Cloud recarga los archivos de página pero deja en memoria los módulos ya
importados. Al añadirle el parámetro `tolerancia` a `horarios_disponibles()`, las
páginas nuevas empezaron a pasárselo a un `disponibilidad.py` viejo que seguía en
memoria, y la app se cayó con `TypeError`. Es la cuarta vez que la misma trampa tumba
la app (ver CLAUDE.md).

Aquí se mira UNA vez qué parámetros acepta el motor que está realmente cargado y se
llama en consecuencia. Si es el nuevo, se le pasa la tolerancia; si es el viejo, se
llama sin ella y la app funciona igual, sólo sin margen sobre el descanso -- que es
exactamente como funcionaba antes.

No se usa `try/except TypeError` a propósito: eso también se tragaría un TypeError de
verdad dentro del motor y escondería un bug real.
"""
import inspect

from app.disponibilidad import horarios_disponibles as _motor

_ACEPTA_TOLERANCIA = "tolerancia" in inspect.signature(_motor).parameters


def libres(
    fecha,
    horario_semanal,
    descansos_por_dia,
    excepciones,
    citas_activas,
    ahora=None,
    duracion=45,
    tolerancia=0,
):
    """Las horas libres de un día. Misma respuesta que `horarios_disponibles`."""
    if _ACEPTA_TOLERANCIA:
        return _motor(
            fecha, horario_semanal, descansos_por_dia, excepciones, citas_activas,
            ahora=ahora, duracion=duracion, tolerancia=tolerancia,
        )
    return _motor(
        fecha, horario_semanal, descansos_por_dia, excepciones, citas_activas,
        ahora=ahora, duracion=duracion,
    )


def capacidad(
    fecha, horario_semanal, descansos_por_dia, excepciones, duracion=45, tolerancia=0
) -> int:
    """Cuántos cortes caben en el día si estuviera vacío.

    Se calcula con las MISMAS reglas que las horas que se ofrecen (incluido el margen
    sobre el descanso). Antes se usaba `analizar_jornada`, que no conoce el margen: la
    app ofrecía 15 cortes y el panel decía que cabían 14. Dos números distintos para la
    misma pregunta es peor que no dar ninguno.
    """
    return len(
        libres(
            fecha, horario_semanal, descansos_por_dia, excepciones, [],
            ahora=None, duracion=duracion, tolerancia=tolerancia,
        )
    )


def ratos_muertos(
    fecha, horario_semanal, descansos_por_dia, excepciones, duracion=45, tolerancia=0
):
    """Los ratos del día que no se pueden vender: descansos y lo que sobra.

    Se calcula como "todo lo que NO es un bloque vendible", así que por construcción
    siempre cuadra con lo que la app ofrece. Devuelve [(inicio, fin, minutos)].
    """
    from datetime import date as _date
    from datetime import datetime as _dt

    from app.disponibilidad import resolver_horario_del_dia

    horario = resolver_horario_del_dia(
        fecha, horario_semanal, descansos_por_dia, excepciones
    )
    if horario.cerrado or horario.apertura is None or horario.cierre is None:
        return []

    bloques = libres(
        fecha, horario_semanal, descansos_por_dia, excepciones, [],
        ahora=None, duracion=duracion, tolerancia=tolerancia,
    )

    hoy = _date.today()

    def minutos_entre(a, b):
        return int((_dt.combine(hoy, b) - _dt.combine(hoy, a)).total_seconds() // 60)

    muertos = []
    cursor = horario.apertura
    for b in bloques:
        if b.inicio > cursor:
            muertos.append((cursor, b.inicio, minutos_entre(cursor, b.inicio)))
        cursor = max(cursor, b.fin)
    if cursor < horario.cierre:
        muertos.append((cursor, horario.cierre, minutos_entre(cursor, horario.cierre)))

    return muertos


def proximo(
    fecha,
    horario_semanal,
    descansos_por_dia,
    excepciones,
    citas_activas,
    ahora,
    duracion=45,
    tolerancia=0,
):
    """El primer espacio libre. Se calcula sobre `libres` en vez de llamar a
    `proximo_espacio` del motor, que tampoco acepta la tolerancia si está cacheado."""
    disponibles = libres(
        fecha, horario_semanal, descansos_por_dia, excepciones, citas_activas,
        ahora=ahora, duracion=duracion, tolerancia=tolerancia,
    )
    return disponibles[0] if disponibles else None

"""Margen: minutos que una cita puede pasarse del descanso o del cierre.

POR QUÉ ESTÁ AQUÍ Y NO EN `catalogo.py`, que sería su sitio natural:

Streamlit Cloud recarga los archivos de página cuando cambia el código, pero deja en
memoria los módulos ya importados. Estas funciones se metieron primero en `catalogo.py`
-- que ya estaba cargado -- y la app se cayó con `AttributeError`: la página nueva
llamaba a `catalogo.tolerancia_minutos()` y el módulo en memoria no la tenía todavía.

Un módulo NUEVO no arrastra ese problema: como nunca se había importado, se carga tal
cual. Es la tercera vez que pasa lo mismo (ver `app/ui/volver.py`), así que la regla es
firme: **toda función nueva que una página vaya a llamar va en un módulo nuevo, no
añadida a uno que ya existía.**

Para qué sirve el margen: antes del almuerzo casi siempre sobra un rato que no alcanza
para otro corte y se pierde. Con unos minutos de margen esa cita sí cabe y termina un
poco dentro del descanso, que es tiempo del barbero. NUNCA se aplica contra otra cita:
pasarse del descanso es meterse en su propio tiempo; pasarse de una cita sería poner a
dos personas a la misma hora.
"""
from app.db import NEGOCIO_ID, _cliente

OPCIONES = [0, 5, 10, 15, 20, 30]


def minutos() -> int:
    """Los minutos configurados. Si la columna aún no existe (falta la migración 004),
    devuelve 0 -- o sea, el comportamiento de siempre."""
    try:
        r = (
            _cliente()
            .table("business")
            .select("tolerancia_minutos")
            .eq("id", NEGOCIO_ID)
            .single()
            .execute()
        )
        return int(r.data.get("tolerancia_minutos") or 0)
    except Exception:
        return 0


def guardar(valor: int) -> None:
    _cliente().table("business").update(
        {"tolerancia_minutos": int(valor)}
    ).eq("id", NEGOCIO_ID).execute()

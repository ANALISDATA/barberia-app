"""Constantes compartidas por toda la app. Un solo lugar para no repetir strings sueltos."""
from zoneinfo import ZoneInfo

ZONA_HORARIA = ZoneInfo("America/Bogota")

NOMBRES_SERVICIO = {
    "sin_barba": "Sin barba",
    "con_barba": "Con barba",
}

NOMBRES_DIA = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}

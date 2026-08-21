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

NOMBRES_MES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def fecha_larga(fecha) -> str:
    """'Jueves 20 de agosto, 2026' -- sin depender del locale del sistema operativo
    (el servidor de Streamlit Cloud no trae instalado el idioma español)."""
    dia_semana = NOMBRES_DIA[fecha.weekday()]
    mes = NOMBRES_MES[fecha.month]
    return f"{dia_semana} {fecha.day} de {mes}, {fecha.year}"

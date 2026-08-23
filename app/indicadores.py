"""Cálculo de todos los indicadores del panel, en un solo sitio.

Los tableros (diario, semanal, historial) SÓLO dibujan: los números salen de aquí. Así
"cortes realizados" significa exactamente lo mismo en las tres páginas, y si mañana hay
que cambiar una definición se cambia una vez.

Reglas de negocio que se aplican en todo el archivo:
  * Sólo las citas ATENDIDAS cuentan como corte realizado y suman a los ingresos.
  * Confirmada, cancelada y no_asistio nunca suman.
  * La semana va de LUNES a DOMINGO (el domingo es el día de cierre del barbero).

No depende de Streamlit: son funciones puras sobre listas de citas, así que se pueden
probar sin conexión ni navegador.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


def semana_de(dia: date) -> tuple[date, date]:
    """Lunes y domingo de la semana a la que pertenece `dia`."""
    lunes = dia - timedelta(days=dia.weekday())
    return lunes, lunes + timedelta(days=6)


@dataclass(frozen=True)
class Resumen:
    """Los números de un periodo (un día, una semana, un mes...)."""

    atendidas: int
    confirmadas: int
    canceladas: int
    no_asistieron: int
    ingresos: int
    sin_barba: int
    con_barba: int

    @property
    def agendadas(self) -> int:
        """Citas que ocuparon un espacio: todo menos las canceladas (una cancelada
        libera el espacio, así que no cuenta como agendada para las cuentas del día)."""
        return self.atendidas + self.confirmadas + self.no_asistieron

    @property
    def efectividad(self) -> float:
        """De lo que se agendó, qué porcentaje se terminó atendiendo.

        Es el indicador que responde "¿de las 10 que tenía, cuántas ya hice?". Se mide
        contra las agendadas y no contra las confirmadas a secas, porque una cita a la
        que el cliente no llegó también resta efectividad -- si sólo se mirara lo
        confirmado, un día lleno de plantones daría 100%.
        """
        return (self.atendidas / self.agendadas * 100) if self.agendadas else 0.0

    @property
    def ocupacion(self) -> float:
        """Qué porcentaje de la agenda del periodo se llegó a ocupar. Se calcula fuera
        (necesita saber cuántos espacios cabían) con `ocupacion_sobre`."""
        return 0.0

    def ocupacion_sobre(self, espacios: int) -> float:
        return (self.agendadas / espacios * 100) if espacios else 0.0

    @property
    def ticket_promedio(self) -> int:
        return round(self.ingresos / self.atendidas) if self.atendidas else 0


def resumir(citas: list[dict]) -> Resumen:
    """Cuenta un montón de citas. `citas` son filas tal como vienen de la base de datos."""
    atendidas = [c for c in citas if c["status"] == "atendida"]
    return Resumen(
        atendidas=len(atendidas),
        confirmadas=len([c for c in citas if c["status"] == "confirmada"]),
        canceladas=len([c for c in citas if c["status"] == "cancelada"]),
        no_asistieron=len([c for c in citas if c["status"] == "no_asistio"]),
        ingresos=sum(c["price_at_booking"] for c in atendidas),
        sin_barba=len([c for c in atendidas if c["service_type"] == "sin_barba"]),
        con_barba=len([c for c in atendidas if c["service_type"] == "con_barba"]),
    )


def por_dia(citas: list[dict], desde: date, hasta: date) -> list[tuple[date, Resumen]]:
    """Un resumen por cada día del rango, incluidos los días sin citas.

    Los días vacíos van a propósito: si se omitieran, la gráfica mentiría -- un lunes
    flojo se vería igual que un lunes cerrado.
    """
    filas = []
    dia = desde
    while dia <= hasta:
        del_dia = [c for c in citas if c["date"] == dia.isoformat()]
        filas.append((dia, resumir(del_dia)))
        dia += timedelta(days=1)
    return filas


def mejor_dia(citas: list[dict], desde: date, hasta: date) -> tuple[date, Resumen] | None:
    """El día con más cortes realizados. Empate: gana el de más ingresos."""
    dias = [(d, r) for d, r in por_dia(citas, desde, hasta) if r.atendidas > 0]
    if not dias:
        return None
    return max(dias, key=lambda x: (x[1].atendidas, x[1].ingresos))


@dataclass(frozen=True)
class ClienteFiel:
    nombre: str
    telefono: str
    cortes: int
    gastado: int
    ultima_visita: date | None
    ultimo_servicio: str


def top_clientes(citas: list[dict], cuantos: int = 5) -> list[ClienteFiel]:
    """Los que más se motilan. Sólo cuenta citas atendidas: alguien que reservó diez
    veces y no llegó nunca no es un buen cliente."""
    por_persona: dict[str, dict] = {}
    for c in sorted(
        (c for c in citas if c["status"] == "atendida"), key=lambda x: x["date"]
    ):
        cliente = c.get("customers") or {}
        telefono = cliente.get("phone") or "—"
        ficha = por_persona.setdefault(
            telefono,
            {"nombre": cliente.get("name") or "—", "cortes": 0, "gastado": 0,
             "ultima": None, "servicio": ""},
        )
        ficha["cortes"] += 1
        ficha["gastado"] += c["price_at_booking"]
        # Van ordenadas por fecha, así que la última que pase es la más reciente.
        ficha["ultima"] = date.fromisoformat(c["date"])
        ficha["servicio"] = c["service_type"]
        ficha["nombre"] = cliente.get("name") or ficha["nombre"]

    fichas = [
        ClienteFiel(
            nombre=f["nombre"], telefono=tel, cortes=f["cortes"], gastado=f["gastado"],
            ultima_visita=f["ultima"], ultimo_servicio=f["servicio"],
        )
        for tel, f in por_persona.items()
    ]
    fichas.sort(key=lambda x: (x.cortes, x.gastado), reverse=True)
    return fichas[:cuantos]


def clientes_nuevos(citas: list[dict], desde: date) -> int:
    """Cuántos clientes vinieron por primera vez a partir de `desde`.

    `citas` tiene que traer TODO el historial, no sólo el periodo: para saber si alguien
    es nuevo hay que poder ver si ya había venido antes.
    """
    primera_vez: dict[str, date] = {}
    for c in citas:
        if c["status"] != "atendida":
            continue
        telefono = (c.get("customers") or {}).get("phone")
        if not telefono:
            continue
        fecha = date.fromisoformat(c["date"])
        if telefono not in primera_vez or fecha < primera_vez[telefono]:
            primera_vez[telefono] = fecha
    return len([1 for f in primera_vez.values() if f >= desde])

"""Acceso a Supabase -- toda la app pasa por aqui, nunca por SQL suelto en otro archivo.

Streamlit corre 100% en el servidor (no hay navegador ejecutando este codigo), asi que a
diferencia de una app web normal, es seguro usar aqui la clave `service_role` -- nunca llega
al navegador del cliente ni del administrador, solo se queda en este proceso de Python. Ese es
el mismo criterio que ya usa `EXTRACCION OP/app/db.py`.

Si no hay credenciales en `.streamlit/secrets.toml`, `disponible()` devuelve False. Las paginas
de la app deben revisar eso antes de usar cualquier funcion de aqui, igual que el patron de
EXTRACCION OP -- pero a diferencia de esa app, ESTA si depende de Supabase (no hay Excel local
de respaldo: la agenda de citas tiene que ser compartida entre el celular del cliente y el
panel del administrador).
"""
from __future__ import annotations

from datetime import date, time
from functools import lru_cache

import streamlit as st

TABLA_NEGOCIO = "business"
TABLA_SERVICIOS = "services"
TABLA_HORARIOS = "working_hours"
TABLA_DESCANSOS = "breaks"
TABLA_EXCEPCIONES = "schedule_exceptions"
TABLA_CLIENTES = "customers"
TABLA_CITAS = "appointments"
TABLA_NOTIFICACIONES = "notification_settings"

NEGOCIO_ID = "00000000-0000-0000-0000-000000000001"  # un solo barbero, un solo negocio

DURACION_POR_DEFECTO = 45  # sólo si la base de datos no dice otra cosa

_RUTA_SCHEMA = __import__("pathlib").Path(__file__).parent.parent / "supabase" / "schema.sql"


def sql_crear_tablas() -> str:
    """Contenido de supabase/schema.sql, para pegar en Supabase -> SQL Editor -> Run."""
    return _RUTA_SCHEMA.read_text(encoding="utf-8")


def _secrets_completos() -> bool:
    # st.secrets.get(...) no se comporta como un dict normal: si no existe NINGUN archivo
    # secrets.toml (ni siquiera vacio), lanza StreamlitSecretNotFoundError en vez de devolver
    # None. Hay que atraparlo para que la app no se caiga la primera vez que alguien la abre
    # sin haber configurado todavia nada.
    try:
        return bool(st.secrets.get("supabase_url")) and bool(st.secrets.get("supabase_key"))
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _cliente():
    from supabase import create_client

    return create_client(st.secrets["supabase_url"], st.secrets["supabase_key"])


def disponible() -> bool:
    if not _secrets_completos():
        return False
    try:
        _cliente().table(TABLA_NEGOCIO).select("id").limit(1).execute()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Negocio / servicios / horarios -- lectura (config del panel, Fase 4)
# ---------------------------------------------------------------------------

def obtener_negocio() -> dict:
    r = _cliente().table(TABLA_NEGOCIO).select("*").eq("id", NEGOCIO_ID).single().execute()
    return r.data


def obtener_servicios() -> list[dict]:
    r = (
        _cliente()
        .table(TABLA_SERVICIOS)
        .select("*")
        .eq("business_id", NEGOCIO_ID)
        .eq("active", True)
        .execute()
    )
    return r.data


def obtener_duracion_cita() -> int:
    """Minutos que dura una cita. Se guarda por servicio, pero todos comparten el mismo
    valor por diseño (la barbería agenda bloques iguales sin importar el corte), así que
    se toma el del primer servicio activo. Cambiarlo en Supabase cambia toda la agenda,
    sin tocar código."""
    servicios = obtener_servicios()
    if not servicios:
        return DURACION_POR_DEFECTO
    return servicios[0].get("duration_minutes") or DURACION_POR_DEFECTO


def obtener_horario_semanal() -> dict[int, tuple[time, time] | None]:
    """Devuelve {dia_semana_python: (apertura, cierre) | None}.

    OJO: la base de datos guarda day_of_week con 0=domingo (como pide el prompt original),
    pero Python (`date.weekday()`, que usa el motor de disponibilidad) usa 0=lunes. Esta
    funcion hace la conversion en el UNICO lugar donde debe hacerse.
    """
    r = (
        _cliente()
        .table(TABLA_HORARIOS)
        .select("day_of_week, start_time, end_time, active")
        .eq("business_id", NEGOCIO_ID)
        .execute()
    )
    resultado: dict[int, tuple[time, time] | None] = {i: None for i in range(7)}
    for fila in r.data:
        dia_bd = fila["day_of_week"]  # 0=domingo..6=sabado
        dia_python = (dia_bd - 1) % 7  # 0=lunes..6=domingo
        if fila["active"]:
            resultado[dia_python] = (
                time.fromisoformat(fila["start_time"]),
                time.fromisoformat(fila["end_time"]),
            )
    return resultado


def obtener_descansos() -> dict[int, list[tuple[time, time]]]:
    r = (
        _cliente()
        .table(TABLA_DESCANSOS)
        .select("start_time, end_time, working_hours(day_of_week, business_id)")
        .execute()
    )
    resultado: dict[int, list[tuple[time, time]]] = {i: [] for i in range(7)}
    for fila in r.data:
        wh = fila.get("working_hours") or {}
        if wh.get("business_id") != NEGOCIO_ID:
            continue
        dia_python = (wh["day_of_week"] - 1) % 7
        resultado[dia_python].append(
            (time.fromisoformat(fila["start_time"]), time.fromisoformat(fila["end_time"]))
        )
    return resultado


# ---------------------------------------------------------------------------
# Configuracion -- escritura (pagina "Configuracion" del panel)
# ---------------------------------------------------------------------------

def _a_dia_bd(dia_python: int) -> int:
    """Python usa 0=lunes; la base de datos, 0=domingo. Esta es la conversion inversa
    de la que hacen `obtener_horario_semanal` y `obtener_descansos`. Vive aqui, junto a
    ellas, para que las dos direcciones esten siempre a la vista y no se desincronicen."""
    return (dia_python + 1) % 7


def guardar_horario_dia(
    dia_python: int, inicio: time | None, fin: time | None, activo: bool
) -> None:
    """Crea o actualiza el horario de un dia de la semana."""
    dia_bd = _a_dia_bd(dia_python)
    existente = (
        _cliente()
        .table(TABLA_HORARIOS)
        .select("id")
        .eq("business_id", NEGOCIO_ID)
        .eq("day_of_week", dia_bd)
        .execute()
    )
    datos = {
        "business_id": NEGOCIO_ID,
        "day_of_week": dia_bd,
        # Un dia cerrado conserva su horario y solo apaga `active`: asi, al volver a
        # abrirlo, no hay que escribir las horas otra vez.
        "start_time": (inicio or time(7, 0)).isoformat(),
        "end_time": (fin or time(20, 0)).isoformat(),
        "active": activo,
    }
    if existente.data:
        _cliente().table(TABLA_HORARIOS).update(datos).eq(
            "id", existente.data[0]["id"]
        ).execute()
    else:
        _cliente().table(TABLA_HORARIOS).insert(datos).execute()


def guardar_descansos_dia(dia_python: int, descansos: list[tuple[time, time]]) -> None:
    """Reemplaza TODOS los descansos de un dia por la lista que se pase.

    Se borra y se vuelve a escribir en vez de ir comparando uno por uno: son dos o tres
    filas por dia y asi no hay forma de que quede un descanso viejo colgado.
    """
    dia_bd = _a_dia_bd(dia_python)
    horario = (
        _cliente()
        .table(TABLA_HORARIOS)
        .select("id")
        .eq("business_id", NEGOCIO_ID)
        .eq("day_of_week", dia_bd)
        .execute()
    )
    if not horario.data:
        return  # sin horario ese dia no hay a que colgar los descansos
    horario_id = horario.data[0]["id"]

    _cliente().table(TABLA_DESCANSOS).delete().eq("working_hours_id", horario_id).execute()
    filas = [
        {
            "working_hours_id": horario_id,
            "start_time": inicio.isoformat(),
            "end_time": fin.isoformat(),
        }
        for inicio, fin in descansos
        if inicio < fin
    ]
    if filas:
        _cliente().table(TABLA_DESCANSOS).insert(filas).execute()


def guardar_duracion_cita(minutos: int) -> None:
    """Todos los servicios comparten duracion: la barberia agenda bloques iguales sin
    importar el corte."""
    _cliente().table(TABLA_SERVICIOS).update({"duration_minutes": minutos}).eq(
        "business_id", NEGOCIO_ID
    ).execute()


def guardar_precio_servicio(tipo: str, precio: int) -> None:
    _cliente().table(TABLA_SERVICIOS).update({"price": precio}).eq(
        "business_id", NEGOCIO_ID
    ).eq("type", tipo).execute()


def guardar_datos_negocio(datos: dict) -> None:
    _cliente().table(TABLA_NEGOCIO).update(datos).eq("id", NEGOCIO_ID).execute()


def actualizar_precio_cita(cita_id: str, precio: int) -> None:
    """Cambia lo que se le cobro a UNA cita concreta.

    Existe porque el barbero no le cobra lo mismo a todo el mundo: el precio del
    servicio es solo el punto de partida, y al cerrar el dia ajusta lo que de verdad
    cobro para que los ingresos cuadren. No toca el precio del servicio ni el de las
    demas citas.
    """
    _cliente().table(TABLA_CITAS).update({"price_at_booking": precio}).eq(
        "id", cita_id
    ).execute()


def obtener_excepciones(desde: date, hasta: date) -> dict[date, dict]:
    r = (
        _cliente()
        .table(TABLA_EXCEPCIONES)
        .select("*")
        .eq("business_id", NEGOCIO_ID)
        .gte("date", desde.isoformat())
        .lte("date", hasta.isoformat())
        .execute()
    )
    resultado = {}
    for fila in r.data:
        resultado[date.fromisoformat(fila["date"])] = {
            "closed": fila["closed"],
            "start": time.fromisoformat(fila["start_time"]) if fila["start_time"] else None,
            "end": time.fromisoformat(fila["end_time"]) if fila["end_time"] else None,
        }
    return resultado


def obtener_citas_activas(fecha: date) -> list[tuple[time, time]]:
    r = (
        _cliente()
        .table(TABLA_CITAS)
        .select("start_time, end_time")
        .eq("business_id", NEGOCIO_ID)
        .eq("date", fecha.isoformat())
        .neq("status", "cancelada")
        .execute()
    )
    return [
        (time.fromisoformat(f["start_time"]), time.fromisoformat(f["end_time"])) for f in r.data
    ]


def obtener_citas_rango(desde: date, hasta: date) -> list[dict]:
    """Todas las citas entre dos fechas (inclusive). Alimenta las estadísticas de
    semana y mes del panel. Devuelve todos los estados -- quien llama decide cuáles
    cuentan (sólo 'atendida' suma cortes e ingresos)."""
    r = (
        _cliente()
        .table(TABLA_CITAS)
        .select("date, start_time, service_type, price_at_booking, status")
        .eq("business_id", NEGOCIO_ID)
        .gte("date", desde.isoformat())
        .lte("date", hasta.isoformat())
        .order("date")
        .execute()
    )
    return r.data


def obtener_citas_con_cliente(desde: date, hasta: date) -> list[dict]:
    """Como `obtener_citas_rango` pero trayendo también el nombre y teléfono. Se usa en
    los tableros que hablan de personas (top de clientes, clientes nuevos)."""
    r = (
        _cliente()
        .table(TABLA_CITAS)
        .select("date, start_time, service_type, price_at_booking, status, customers(name, phone)")
        .eq("business_id", NEGOCIO_ID)
        .gte("date", desde.isoformat())
        .lte("date", hasta.isoformat())
        .order("date")
        .execute()
    )
    return r.data


# ---------------------------------------------------------------------------
# Cierres de semana
# ---------------------------------------------------------------------------

TABLA_CIERRES = "cierres_semana"


class FaltaTablaCierres(Exception):
    """Todavía no se ha corrido `supabase/002_cierres_semana.sql`."""


def _es_tabla_faltante(err: Exception) -> bool:
    texto = str(err).lower()
    return "cierres_semana" in texto and (
        "could not find the table" in texto or "does not exist" in texto
    )


def hay_tabla_cierres() -> bool:
    """Si la tabla de cierres existe. Se pregunta antes de usarla para que la página de
    la semana siga funcionando aunque falte correr el SQL -- sin esto, olvidar ese paso
    rompía la página entera en vez de avisar."""
    try:
        _cliente().table(TABLA_CIERRES).select("id").limit(1).execute()
        return True
    except Exception as err:
        if _es_tabla_faltante(err):
            return False
        raise


def obtener_cierres(limite: int = 12) -> list[dict]:
    """Las últimas semanas cerradas, de la más reciente a la más vieja."""
    try:
        r = (
            _cliente()
            .table(TABLA_CIERRES)
            .select("*")
            .eq("business_id", NEGOCIO_ID)
            .order("semana_inicio", desc=True)
            .limit(limite)
            .execute()
        )
    except Exception as err:
        if _es_tabla_faltante(err):
            return []
        raise
    return r.data


def semana_esta_cerrada(lunes: date) -> bool:
    try:
        r = (
            _cliente()
            .table(TABLA_CIERRES)
            .select("id")
            .eq("business_id", NEGOCIO_ID)
            .eq("semana_inicio", lunes.isoformat())
            .execute()
        )
    except Exception as err:
        if _es_tabla_faltante(err):
            return False
        raise
    return bool(r.data)


class SemanaYaCerrada(Exception):
    """Esa semana ya se había cerrado antes."""


def cerrar_semana(lunes: date, domingo: date, numeros: dict) -> dict:
    """Guarda cómo quedó la semana. `numeros` son los totales ya calculados.

    Se congela la foto en vez de recalcular al consultar: si después se corrige el
    precio de una cita vieja, un cierre ya guardado no debe moverse -- si no, las
    cuentas de una semana cerrada cambiarían solas y no habría con qué comparar.
    """
    try:
        r = (
            _cliente()
            .table(TABLA_CIERRES)
            .insert({
                "business_id": NEGOCIO_ID,
                "semana_inicio": lunes.isoformat(),
                "semana_fin": domingo.isoformat(),
                **numeros,
            })
            .execute()
        )
        return r.data[0]
    except Exception as err:
        # La restricción `unique (business_id, semana_inicio)` de la base de datos es la
        # que de verdad impide cerrar dos veces la misma semana.
        if "duplicate" in str(err).lower() or "unique" in str(err).lower():
            raise SemanaYaCerrada() from err
        raise


def obtener_citas_del_dia(fecha: date) -> list[dict]:
    """Version con todos los datos (cliente, servicio, precio, estado) para el panel."""
    r = (
        _cliente()
        .table(TABLA_CITAS)
        .select("*, customers(name, phone), services(type)")
        .eq("business_id", NEGOCIO_ID)
        .eq("date", fecha.isoformat())
        .order("start_time")
        .execute()
    )
    return r.data


# ---------------------------------------------------------------------------
# Clientes y citas -- escritura
# ---------------------------------------------------------------------------

def obtener_o_crear_cliente(nombre: str, telefono: str) -> str:
    existente = (
        _cliente()
        .table(TABLA_CLIENTES)
        .select("id")
        .eq("business_id", NEGOCIO_ID)
        .eq("phone", telefono)
        .execute()
    )
    if existente.data:
        return existente.data[0]["id"]

    nuevo = (
        _cliente()
        .table(TABLA_CLIENTES)
        .insert({"business_id": NEGOCIO_ID, "name": nombre, "phone": telefono})
        .execute()
    )
    return nuevo.data[0]["id"]


class HorarioYaReservado(Exception):
    """Alguien mas reservo ese horario justo antes -- la base de datos lo impidio (ver schema.sql)."""


def crear_cita(
    *,
    nombre: str,
    telefono: str,
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
    tipo_servicio: str,
    service_id: str,
    precio: int,
) -> dict:
    """Crea la cita. El precio se guarda tal cual se recibe (precio historico, nunca se recalcula)."""
    cliente_id = obtener_o_crear_cliente(nombre, telefono)
    try:
        r = (
            _cliente()
            .table(TABLA_CITAS)
            .insert(
                {
                    "business_id": NEGOCIO_ID,
                    "customer_id": cliente_id,
                    "service_id": service_id,
                    "date": fecha.isoformat(),
                    "start_time": hora_inicio.isoformat(),
                    "end_time": hora_fin.isoformat(),
                    "service_type": tipo_servicio,
                    "price_at_booking": precio,
                    "status": "confirmada",
                }
            )
            .execute()
        )
        return r.data[0]
    except Exception as err:
        # La restriccion "no_solapes" de la base de datos (schema.sql) es la que
        # realmente evita reservas duplicadas simultaneas -- esto solo traduce
        # ese rechazo a un mensaje que la interfaz pueda mostrar.
        if "no_solapes" in str(err) or "exclusion" in str(err).lower():
            raise HorarioYaReservado() from err
        raise


def cambiar_estado_cita(cita_id: str, nuevo_estado: str, motivo: str | None = None) -> None:
    datos = {"status": nuevo_estado}
    if motivo:
        datos["cancellation_reason"] = motivo
    _cliente().table(TABLA_CITAS).update(datos).eq("id", cita_id).execute()


def cancelar_por_token(token: str, motivo: str | None = None) -> bool:
    r = (
        _cliente()
        .table(TABLA_CITAS)
        .update({"status": "cancelada", "cancellation_reason": motivo})
        .eq("cancel_token", token)
        .neq("status", "cancelada")
        .execute()
    )
    return bool(r.data)


def historial_cliente(telefono: str) -> list[dict]:
    r = (
        _cliente()
        .table(TABLA_CITAS)
        .select("*, customers!inner(phone, name)")
        .eq("business_id", NEGOCIO_ID)
        .eq("customers.phone", telefono)
        .order("date", desc=True)
        .execute()
    )
    return r.data

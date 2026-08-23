"""Servicios y productos: leer, crear, editar y borrar.

En módulo NUEVO y no dentro de `db.py` a propósito: Streamlit Cloud deja cacheados en
memoria los módulos ya importados, así que agregarle funciones a `db.py` obliga a
reiniciar la app a mano tras publicar, o se cae. Un módulo que nunca se había
importado se carga tal cual. Ver la explicación completa en `app/ui/volver.py`.

Los servicios dejaron de estar fijos en el código: se leen de la base de datos, cada
uno con su propio precio y su propia duración. Por eso NO se debe volver a escribir
una lista de servicios a mano en ningún sitio -- si mañana el barbero agrega "cejas",
tiene que aparecer sola en la página de reservas.
"""
from __future__ import annotations

import base64

from app.db import NEGOCIO_ID, _cliente

TABLA_SERVICIOS = "services"
TABLA_PRODUCTOS = "productos"

DURACION_POR_DEFECTO = 45


# ---------------------------------------------------------------------------
# Servicios
# ---------------------------------------------------------------------------

def servicios(solo_activos: bool = True) -> list[dict]:
    consulta = (
        _cliente()
        .table(TABLA_SERVICIOS)
        .select("*")
        .eq("business_id", NEGOCIO_ID)
    )
    if solo_activos:
        consulta = consulta.eq("active", True)
    filas = consulta.execute().data
    # `orden` puede no existir todavía si no se ha corrido la migración 003.
    return sorted(filas, key=lambda s: (s.get("orden") or 0, s.get("name") or ""))


def nombres_servicios() -> dict[str, str]:
    """{tipo: nombre bonito}. Reemplaza al diccionario fijo que había en config.py."""
    return {s["type"]: s["name"] for s in servicios(solo_activos=False)}


def duracion_de(tipo: str, por_defecto: int = DURACION_POR_DEFECTO) -> int:
    for s in servicios(solo_activos=False):
        if s["type"] == tipo:
            return s.get("duration_minutes") or por_defecto
    return por_defecto


def duracion_mas_larga() -> int:
    """La duración del servicio más largo.

    Es la que usa el panel para contar espacios libres: si en un hueco cabe el servicio
    más largo, cabe cualquiera. Al revés no -- contar con el más corto mostraría huecos
    donde no cabe un corte completo y el barbero agendaría encima de su propio tiempo.
    """
    activos = servicios()
    if not activos:
        return DURACION_POR_DEFECTO
    return max((s.get("duration_minutes") or DURACION_POR_DEFECTO) for s in activos)


def _tipo_desde_nombre(nombre: str) -> str:
    """Convierte "Solo cejas" en "solo_cejas": un identificador estable que no cambia
    aunque después se corrija el nombre visible."""
    limpio = (
        nombre.lower()
        .replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    )
    solo_letras = "".join(c if c.isalnum() else "_" for c in limpio)
    return "_".join(p for p in solo_letras.split("_") if p)[:40] or "servicio"


class TipoRepetido(Exception):
    """Ya hay un servicio con ese nombre."""


def crear_servicio(nombre: str, precio: int, duracion: int) -> dict:
    tipo = _tipo_desde_nombre(nombre)
    existentes = {s["type"] for s in servicios(solo_activos=False)}
    if tipo in existentes:
        raise TipoRepetido()

    orden = len(existentes)
    try:
        r = (
            _cliente()
            .table(TABLA_SERVICIOS)
            .insert({
                "business_id": NEGOCIO_ID,
                "type": tipo,
                "name": nombre.strip(),
                "price": int(precio),
                "duration_minutes": int(duracion),
                "active": True,
                "orden": orden,
            })
            .execute()
        )
    except Exception as err:
        if "duplicate" in str(err).lower() or "unique" in str(err).lower():
            raise TipoRepetido() from err
        raise
    return r.data[0]


def actualizar_servicio(servicio_id: str, datos: dict) -> None:
    _cliente().table(TABLA_SERVICIOS).update(datos).eq("id", servicio_id).execute()


def desactivar_servicio(servicio_id: str) -> None:
    """No se borra: se apaga.

    Borrarlo rompería las citas viejas que apuntan a él (y la base de datos lo impide),
    y además perderías el historial de cuántos de esos hiciste. Apagado, deja de
    ofrecerse a los clientes pero las citas pasadas siguen contando.
    """
    _cliente().table(TABLA_SERVICIOS).update({"active": False}).eq(
        "id", servicio_id
    ).execute()


def activar_servicio(servicio_id: str) -> None:
    _cliente().table(TABLA_SERVICIOS).update({"active": True}).eq(
        "id", servicio_id
    ).execute()


# ---------------------------------------------------------------------------
# Productos
# ---------------------------------------------------------------------------

def hay_tabla_productos() -> bool:
    """Si ya se corrió la migración 003. Se pregunta antes de usar la tabla para que la
    app siga funcionando mientras ese paso esté pendiente, en vez de romperse."""
    try:
        _cliente().table(TABLA_PRODUCTOS).select("id").limit(1).execute()
        return True
    except Exception as err:
        texto = str(err).lower()
        if "productos" in texto and (
            "could not find the table" in texto or "does not exist" in texto
        ):
            return False
        raise


def productos(solo_activos: bool = True) -> list[dict]:
    try:
        consulta = (
            _cliente()
            .table(TABLA_PRODUCTOS)
            .select("*")
            .eq("business_id", NEGOCIO_ID)
        )
        if solo_activos:
            consulta = consulta.eq("activo", True)
        filas = consulta.execute().data
    except Exception:
        return []
    return sorted(filas, key=lambda p: (p.get("orden") or 0, p.get("nombre") or ""))


def crear_producto(nombre: str, precio: int, descripcion: str,
                   imagen_base64: str | None = None) -> dict:
    r = (
        _cliente()
        .table(TABLA_PRODUCTOS)
        .insert({
            "business_id": NEGOCIO_ID,
            "nombre": nombre.strip(),
            "precio": int(precio),
            "descripcion": (descripcion or "").strip(),
            "imagen_base64": imagen_base64,
            "orden": len(productos(solo_activos=False)),
        })
        .execute()
    )
    return r.data[0]


def actualizar_producto(producto_id: str, datos: dict) -> None:
    _cliente().table(TABLA_PRODUCTOS).update(datos).eq("id", producto_id).execute()


def borrar_producto(producto_id: str) -> None:
    """Los productos sí se borran de verdad: no los referencia ninguna cita, así que
    no rompen nada ni hay historial que conservar."""
    _cliente().table(TABLA_PRODUCTOS).delete().eq("id", producto_id).execute()


def preparar_imagen(archivo, ancho_max: int = 700) -> str:
    """Deja la foto lista para guardar: la encoge y la devuelve como texto base64.

    Se reduce antes de guardar porque una foto de celular pesa varios MB y se guarda
    dentro de la base de datos: sin encoger, unos pocos productos llenarían la cuota y
    la página del catálogo tardaría en abrir en un celular con datos.
    """
    from io import BytesIO

    from PIL import Image

    imagen = Image.open(archivo)
    if imagen.mode not in ("RGB", "L"):
        imagen = imagen.convert("RGB")
    if imagen.width > ancho_max:
        alto = round(imagen.height * ancho_max / imagen.width)
        imagen = imagen.resize((ancho_max, alto), Image.LANCZOS)

    buffer = BytesIO()
    imagen.save(buffer, format="JPEG", quality=85, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode()

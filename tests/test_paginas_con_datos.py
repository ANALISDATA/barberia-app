"""Las páginas tienen que aguantar un día CON citas, no sólo un día vacío.

POR QUÉ EXISTE ESTA PRUEBA: `test_paginas_sin_conexion.py` sólo comprobaba que las
páginas no truenan cuando no hay Supabase. Pero sin conexión las páginas se salen
temprano ("No hay conexión") y la mitad del código nunca llega a correr. Así se publicó
un `NameError` de verdad en la agenda del panel (23/08/2026): la tabla de citas
reservadas usaba una variable que no existía, y sólo reventaba cuando había al menos
UNA cita ese día. Con la agenda vacía no se veía.

Aquí se le inventa a la app un día normal de trabajo -- citas atendidas, confirmadas,
canceladas y un plantón -- y se pintan TODAS las páginas. Si alguna revienta, esta
prueba lo dice antes de publicar, no el barbero delante de un cliente.

No toca la base de datos real: `db._cliente` queda cortado a propósito, así que
cualquier consulta que se nos haya olvidado simular falla aquí en vez de irse callada
a internet.

Corre con:  python -m pytest tests/test_paginas_con_datos.py -v
"""
from datetime import date, datetime, time, timedelta

import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ZONA_HORARIA  # noqa: E402

PAGINAS_PUBLICAS = [
    "app/paginas/inicio.py",
    "app/paginas/cita.py",
    "app/paginas/productos.py",
]

PAGINAS_PANEL = [
    "app/paginas/admin_inicio.py",
    "app/paginas/admin_dia.py",
    "app/paginas/admin_semana.py",
    "app/paginas/admin_historial.py",
    "app/paginas/admin_recordar.py",
    "app/paginas/admin_config.py",
]

HOY = datetime.now(ZONA_HORARIA).date()


def _cita(num, hora, estado, tipo="sin_barba", precio=25000, dia=None):
    """Una cita tal como la devuelve Supabase, con el cliente y el servicio pegados."""
    inicio = time(hora, 0)
    fin = time(hora, 45) if hora < 23 else time(23, 59)
    return {
        "id": f"cita-{num}",
        "date": (dia or HOY).isoformat(),
        "start_time": inicio.isoformat(),
        "end_time": fin.isoformat(),
        "status": estado,
        "service_type": tipo,
        "price_at_booking": precio,
        "customers": {"name": f"Cliente {num}", "phone": f"30011122{num:02d}"},
        "services": {"type": tipo},
    }


# Un día como cualquier otro: dos cobradas, una por atender, una cancelada y un plantón.
CITAS_DE_HOY = [
    _cita(1, 8, "atendida"),
    _cita(2, 9, "atendida", tipo="con_barba", precio=35000),
    _cita(3, 10, "confirmada"),
    _cita(4, 11, "cancelada"),
    _cita(5, 14, "no_asistio"),
]

# Para las estadísticas de semana y mes hace falta historia, no sólo hoy.
CITAS_DEL_RANGO = CITAS_DE_HOY + [
    _cita(6, 8, "atendida", dia=HOY - timedelta(days=3)),
    _cita(7, 9, "atendida", tipo="con_barba", precio=35000, dia=HOY - timedelta(days=10)),
    _cita(8, 10, "atendida", dia=HOY - timedelta(days=25)),
]

SERVICIOS = [
    {"id": "s1", "type": "sin_barba", "name": "Corte", "price": 25000,
     "duration_minutes": 45, "active": True, "orden": 1},
    {"id": "s2", "type": "con_barba", "name": "Corte con barba", "price": 35000,
     "duration_minutes": 50, "active": True, "orden": 2},
    {"id": "s3", "type": "cejas", "name": "Cejas", "price": 8000,
     "duration_minutes": 15, "active": True, "orden": 3},
]

PRODUCTOS = [
    {"id": "p1", "nombre": "Cera mate", "precio": 30000, "activo": True,
     "descripcion": "Fijación fuerte, acabado seco.", "imagen_src": "", "orden": 1},
]

NEGOCIO = {
    "id": "b1",
    "name": "Esteban Barber",
    "address": "Cra 58 #49A-23, Copacabana",
    "phone": "3045508809",
    "pricing_mode": "por_servicio",
}

# Abierto los SIETE días, aunque el barbero de verdad descanse el domingo. Si aquí se
# dejara el domingo cerrado, la prueba pasaría de lunes a sábado y el domingo se saltaría
# la mitad del código sin avisar -- que es justo cómo se coló el fallo que originó este
# archivo. Una prueba no puede depender del día en que se corra.
HORARIO = {d: (time(8, 0), time(20, 0)) for d in range(7)}

DESCANSOS = {d: [(time(12, 0), time(13, 0))] for d in range(7)}


class _SinBaseDeDatos:
    """Corta el acceso real a Supabase. Si una página pide algo que no simulamos, se
    entera aquí y no en producción."""

    def __getattr__(self, nombre):
        raise RuntimeError(
            f"La página intentó consultar Supabase de verdad ('{nombre}'). "
            "Falta simular esa función en tests/test_paginas_con_datos.py."
        )


@pytest.fixture
def dia_normal(monkeypatch):
    from app import catalogo, db, margen, recordatorios
    from app.ui import menu

    # El menú del panel se apaga SÓLO aquí, y no porque falle: `st.Page` busca los
    # archivos partiendo del script principal, que en la app de verdad es
    # `Aplicacion.py` (en la raíz) y en esta prueba es la página suelta. Fuera de la app
    # completa no los encuentra. Es una limitación de probar una página aislada, no un
    # fallo del menú; lo que interesa comprobar aquí es el cuerpo de cada página.
    monkeypatch.setattr(menu, "pintar", lambda *_a, **_k: None)

    monkeypatch.setattr(db, "_cliente", lambda: _SinBaseDeDatos())
    monkeypatch.setattr(db, "disponible", lambda: True)
    monkeypatch.setattr(db, "obtener_negocio", lambda: NEGOCIO)
    monkeypatch.setattr(db, "obtener_horario_semanal", lambda: HORARIO)
    monkeypatch.setattr(db, "obtener_descansos", lambda: DESCANSOS)
    monkeypatch.setattr(db, "obtener_excepciones", lambda *_a, **_k: {})
    monkeypatch.setattr(db, "obtener_citas_del_dia", lambda f: [
        c for c in CITAS_DEL_RANGO if c["date"] == f.isoformat()
    ])
    monkeypatch.setattr(db, "obtener_citas_rango", lambda *_a, **_k: CITAS_DEL_RANGO)
    monkeypatch.setattr(db, "obtener_citas_con_cliente", lambda *_a, **_k: CITAS_DEL_RANGO)
    monkeypatch.setattr(db, "obtener_citas_activas", lambda *_a, **_k: [])
    monkeypatch.setattr(db, "obtener_servicios", lambda: SERVICIOS)
    monkeypatch.setattr(db, "obtener_duracion_cita", lambda: 45)
    monkeypatch.setattr(db, "hay_tabla_cierres", lambda: True)
    monkeypatch.setattr(db, "obtener_cierres", lambda *_a, **_k: [])
    monkeypatch.setattr(db, "semana_esta_cerrada", lambda *_a, **_k: False)

    monkeypatch.setattr(catalogo, "servicios", lambda *_a, **_k: SERVICIOS)
    monkeypatch.setattr(catalogo, "nombres_servicios",
                        lambda: {s["type"]: s["name"] for s in SERVICIOS})
    monkeypatch.setattr(catalogo, "productos", lambda *_a, **_k: PRODUCTOS)
    monkeypatch.setattr(catalogo, "hay_tabla_productos", lambda: True)
    monkeypatch.setattr(catalogo, "duracion_mas_larga", lambda: 50)
    monkeypatch.setattr(catalogo, "duracion_de", lambda t, *_a, **_k: 45)

    monkeypatch.setattr(margen, "minutos", lambda: 15)

    monkeypatch.setattr(recordatorios, "hay_columna_recordatorio", lambda: True)
    monkeypatch.setattr(recordatorios, "buscar", lambda *_a, **_k: [
        recordatorios.ClienteDormido(
            cliente_id="c1", nombre="Carlos Pérez", telefono="3145900531",
            ultima_visita=HOY - timedelta(days=22), veces=4,
            ultimo_servicio="con_barba", ultimo_recordatorio=None,
        )
    ])


def _pintar(pagina, autenticado):
    at = AppTest.from_file(pagina, default_timeout=60)
    if autenticado:
        at.session_state["admin_autenticado"] = True
    at.run()
    return at


@pytest.mark.parametrize("pagina", PAGINAS_PUBLICAS + PAGINAS_PANEL)
def test_la_pagina_aguanta_un_dia_con_citas(pagina, dia_normal):
    at = _pintar(pagina, autenticado=pagina in PAGINAS_PANEL)
    assert not at.exception, f"{pagina} reventó con un día normal de citas: {at.exception}"


def test_la_agenda_del_dia_muestra_el_nombre_del_servicio(dia_normal):
    """El fallo real que se publicó: la tabla de reservadas traducía el tipo de servicio
    a su nombre bonito usando una variable que no existía en esa función."""
    at = AppTest.from_file("app/paginas/admin_inicio.py", default_timeout=60)
    at.session_state["admin_autenticado"] = True
    at.session_state["vista_agenda"] = "reservadas"
    at.run()

    assert not at.exception, f"La agenda reventó: {at.exception}"
    texto = " ".join(str(e.value) for e in at.markdown) + " ".join(
        str(getattr(e, "label", "")) for e in at.button
    )
    assert "Corte" in texto, "La agenda no está mostrando el nombre del servicio."


def test_el_consolidado_aparece_cuando_hay_citas_atendidas(dia_normal):
    """El consolidado sólo se pinta si hubo cobros: es el otro trozo de código que
    únicamente corre con datos y que también estaba roto."""
    at = AppTest.from_file("app/paginas/admin_inicio.py", default_timeout=60)
    at.session_state["admin_autenticado"] = True
    at.run()

    assert not at.exception
    etiquetas = [e.label for e in at.number_input]
    assert etiquetas, "No se pintó el consolidado del día pese a haber citas atendidas."
    assert any("Corte" in e for e in etiquetas)

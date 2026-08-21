"""Las páginas nunca deben mostrar un error feo (traceback) si todavía no hay
`secrets.toml` -- deben avisar con un mensaje claro y seguir funcionando.
Bug real encontrado la primera vez que se probó la app: `st.secrets.get(...)` no se
comporta como un diccionario normal cuando el archivo no existe, revienta en vez de
devolver None. Esta prueba evita que se repita sin darse cuenta.

No depende de que este computador tenga o no `secrets.toml` real -- se fuerza el estado
"sin conexión" directamente (`app.db.disponible` -> False), para que la prueba de el mismo
resultado en cualquier máquina, incluida esta, que ya tiene credenciales reales configuradas
para desarrollo.

Corre con:  python -m pytest tests/test_paginas_sin_conexion.py -v
"""
from streamlit.testing.v1 import AppTest

PAGINAS = [
    "app/paginas/reservar.py",
    "app/paginas/admin_login.py",
    "app/paginas/admin_inicio.py",
]


def test_paginas_no_truenan_sin_conexion(monkeypatch):
    monkeypatch.setattr("app.db.disponible", lambda: False)
    for pagina in PAGINAS:
        at = AppTest.from_file(pagina)
        at.run()
        assert not at.exception, f"{pagina} lanzó un error sin conexión a Supabase: {at.exception}"

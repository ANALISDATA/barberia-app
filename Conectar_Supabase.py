"""Comprueba la conexión con Supabase y guía paso a paso si falta algo.

Se ejecuta así, con doble clic en `3 - Conectar Supabase.bat`, o a mano:

    python Conectar_Supabase.py

No borra ni cambia nada — solo revisa y te dice exactamente qué falta.
Se puede correr las veces que haga falta.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# En Windows, la consola a veces usa una codificacion vieja (cp1252) que no sabe
# imprimir tildes ni el simbolo ✔ -- forzamos UTF-8 para que nunca truene por eso,
# sin depender de que quien lo ejecute haya hecho antes "chcp 65001".
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    print("=" * 70)
    print("  CONECTAR BARBERIA APP CON SUPABASE")
    print("=" * 70)
    print()

    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print("✖ Todavía no existe el archivo .streamlit/secrets.toml")
        print()
        print("  1. Copia .streamlit/secrets.toml.example y renómbralo a secrets.toml")
        print("     (en la misma carpeta .streamlit).")
        print("  2. Entra a supabase.com/dashboard → tu proyecto → Project Settings → API.")
        print("  3. Copia estos dos valores dentro de secrets.toml:")
        print('       supabase_url = "https://xxxxxxxx.supabase.co"   (Project URL)')
        print('       supabase_key = "…"   ← la clave "service_role", NO la "anon public"')
        print()
        print("  Vuelve a correr este script cuando lo hayas hecho.")
        return 1

    import streamlit as st
    from app import db

    if not db._secrets_completos():
        print("✖ El archivo secrets.toml existe pero faltan supabase_url o supabase_key.")
        print("  Revísalo: debe tener las dos líneas exactas (ver arriba).")
        return 1

    if not db.disponible():
        print("✖ No se pudo conectar con Supabase.")
        print()
        print("  Puede ser que las tablas todavía no existan. Entra a tu proyecto de Supabase")
        print("  → SQL Editor → New query, pega todo esto y dale RUN:")
        print()
        print("-" * 70)
        print(db.sql_crear_tablas())
        print("-" * 70)
        print()
        print("  Después vuelve a correr este script.")
        return 1

    print("✔ Conexión con Supabase establecida.")
    negocio = db.obtener_negocio()
    print(f"✔ Negocio configurado: {negocio['name']}")
    servicios = db.obtener_servicios()
    print(f"✔ Servicios activos: {len(servicios)}")
    print()
    print("Listo. Ya puedes abrir la app con  ▶ ABRIR LA APP.bat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

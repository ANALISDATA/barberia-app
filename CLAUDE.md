# Contexto para Claude Code — Barbería App

App de reservas para una barbería (**un solo barbero, un solo local**) — proyecto
personal del usuario, sin relación con su trabajo. Streamlit + Python + Supabase,
siguiendo el mismo patrón que otras apps del usuario: instalador `.bat` sin terminal,
credenciales en `.streamlit/secrets.toml`, script guiado para conectar Supabase.

## Por qué este stack (y no Next.js)

Se arrancó primero con Next.js/Vercel/Supabase (ver el documento de arquitectura Fase 1,
publicado como Artifact al usuario). Se cambió a Streamlit porque:

1. El usuario pidió explícitamente replicar el patrón de sus otras apps (Python,
   instalador `.bat`, sin terminal) — ver historial de conversación.
2. Es el patrón que el usuario ya domina y en el que confía.

El scaffold de Next.js quedó abandonado en `C:\Users\lider7\barberia-app` (no se borró,
por si el usuario lo pide de vuelta). **No retomarlo sin que el usuario lo pida.**

## Diferencia clave de arquitectura vs. una web app normal

Streamlit corre 100% en el servidor — no hay JavaScript del navegador llamando a
Supabase directamente. Por eso `app/db.py` usa la clave `service_role` (no la `anon`)
sin que eso sea inseguro: esa clave nunca sale del proceso de Python. Las políticas RLS
en `supabase/schema.sql` están activadas pero sin políticas (cerrojo de respaldo, no la
capa principal de seguridad).

## Estructura

```
Aplicacion.py            Punto de entrada. st.navigation entre reservar/admin_login/admin_inicio.
config.py                 Constantes compartidas (zona horaria, nombres de servicios/días).
app/
  disponibilidad.py       Motor central getAvailableSlots (llamado horarios_disponibles).
                           Funciones puras, sin Streamlit ni Supabase -- por eso se prueban solas.
  db.py                    Todo el acceso a Supabase. NEGOCIO_ID fijo (un solo negocio).
  ui/tema.py               Identidad visual: paleta carbón + dorado, tarjetas, píldoras de estado.
  paginas/
    reservar.py            Página pública. Wizard con st.session_state (fecha, servicio, hora, datos).
    admin_login.py          Gate con contraseña simple (st.secrets["admin_password"]) -- no hay
                             Supabase Auth, un solo dueño no lo necesita.
    admin_inicio.py         Dashboard: próximo espacio, próximas citas, resumen del día, +Nueva cita.
supabase/schema.sql        Pegar en Supabase SQL Editor. Incluye la restricción EXCLUDE (btree_gist)
                             que impide citas solapadas -- la garantía real anti-reservas-simultáneas.
tests/
  test_disponibilidad.py            Casos obligatorios del prompt original (§55).
  test_paginas_sin_conexion.py      Ver "Trampa encontrada" abajo.
```

## Convención day_of_week: OJO con el desfase

La base de datos (y el prompt original del usuario) usa `day_of_week` con **0=domingo**.
Python (`date.weekday()`, usado por `disponibilidad.py`) usa **0=lunes**. La conversión
(`(dia_bd - 1) % 7`) vive ÚNICAMENTE en `db.py` (`obtener_horario_semanal`,
`obtener_descansos`). No convertir en ningún otro lado.

## TRAMPA MÁS PELIGROSA: Streamlit Cloud cachea los módulos compartidos

**Esto tumbó la app en producción dos veces el 21/08/2026.** Streamlit Cloud recarga
los archivos de PÁGINA cuando cambia el código, pero **deja en memoria los módulos que
ya estaban importados** (`app/ui/tema.py`, `app/navegacion.py`, `app/db.py`...).
Resultado: la página nueva llama a una función vieja y la app se cae.

- `ImportError: cannot import name 'admin_config'` — `Aplicacion.py` ya pedía el nombre
  nuevo; `navegacion.py` seguía siendo el de antes en memoria.
- `TypeError` en `hero_simple(volver_a=...)` — la página ya pasaba el parámetro nuevo y
  `tema.py` todavía no lo aceptaba.

**No se cura solo**: se probó esperar y siguió caída. Hace falta *Reboot app* desde
Streamlit Cloud, que sólo puede hacer el usuario.

**Reglas para no repetirlo:**

1. **Cambiar la firma de una función de `tema.py`, `db.py` o `navegacion.py` obliga a
   reiniciar la app** después de subir. Avisar SIEMPRE al usuario cuando el cambio sea
   de ese tipo.
2. Si el cambio tiene que quedar arriba sin reiniciar, meterlo en un **módulo nuevo**:
   uno que nunca se ha importado no tiene versión vieja en memoria. Así se resolvió el
   botón de volver (`app/ui/volver.py`) — ver el comentario de ese archivo.
3. **Después de CADA push, correr `Comprobar_App_En_Linea.py`.** Que las pruebas locales
   pasen no dice nada sobre si la app está arriba. Esta app tiene que estar 24/7.

## Trampa ya encontrada: `st.secrets.get()` no es un dict seguro

`st.secrets.get("x")` **lanza** `StreamlitSecretNotFoundError` (no devuelve `None`) si
no existe NINGÚN archivo `secrets.toml` -- a diferencia de un dict normal. La primera
vez que se corrió la app (sin secrets.toml todavía) esto tumbaba las tres páginas con un
traceback feo. Se envolvió en `try/except` en `db._secrets_completos()` y en
`admin_login.py`. `tests/test_paginas_sin_conexion.py` (usa `streamlit.testing.v1.AppTest`,
que corre las páginas sin navegador de verdad) lo cubre para que no se repita sin darse
cuenta. **Si se agrega una página nueva que lea `st.secrets`, agregarla también a la
lista `PAGINAS` de esa prueba.**

## Precio histórico

`crear_cita` en `db.py` recibe `precio` ya calculado por quien la llama (según
`business.pricing_mode`) y lo guarda tal cual en `price_at_booking`. Nunca se
recalcula al leer una cita vieja, ni siquiera si después cambia el precio en `services`.

## Pendiente (no construido todavía)

- Calendario semanal/vista día en el panel.
- Sección Clientes con historial (`db.historial_cliente` ya existe, falta la página).
- Sección Horarios/Configuración editable desde el panel (hoy se edita directo en
  Supabase Table Editor).
- Estadísticas semana/mes + gráfica (Altair ya está en requirements.txt, sin usar aún).
- Alertas de espacio libre + sonido (§25-28 del prompt original). En Streamlit esto
  necesita `st.fragment(run_every=...)` o similar para revisar cambios periódicamente
  -- no hay Realtime nativo como en la app web. Diseñar antes de implementar.
- Desplegar en Streamlit Community Cloud para tener el enlace público 24/7 (mientras
  tanto la app solo funciona con el computador del usuario encendido).
- Cancelación desde el propio cliente vía `cancel_token` (la función `db.cancelar_por_token`
  ya existe, falta la página/ruta pública que la use).

## Usuario

No-técnico, prueba en vivo y reporta con capturas de pantalla, PC corporativo sin
permisos de administrador (por eso Node.js portable y este cambio a Python -- ver
historial de conversación de esta sesión). Este proyecto es personal, sin relación con
su trabajo -- no mezclar cuentas, correos ni nombres de ahí en este repositorio.

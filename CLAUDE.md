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

Ha pasado **tres veces**, siempre igual: `ImportError` (nombre nuevo en `navegacion.py`),
`TypeError` (parámetro nuevo en `tema.py`) y `AttributeError` (función nueva en
`catalogo.py`). Las tres tumbaron la app en producción.

**LA REGLA, y no tiene excepciones:**

> **Toda función, parámetro o nombre NUEVO que una página vaya a usar va en un módulo
> NUEVO.** Nunca añadido a uno que ya existía (`db.py`, `tema.py`, `catalogo.py`,
> `navegacion.py`...). Un módulo que nunca se importó no tiene versión vieja en memoria.

Ejemplos de esa regla en el proyecto: `app/ui/volver.py`, `app/ui/menu.py`,
`app/catalogo.py`, `app/margen.py`. Cada uno nació porque meterlo donde "correspondía"
habría tumbado la app.

Si por lo que sea hay que tocar un módulo compartido, entonces **avisar al usuario de
que tiene que reiniciar la app** desde Streamlit Cloud después de publicar.

Y siempre: **después de CADA push, correr `Comprobar_App_En_Linea.py`.** Que las pruebas
locales pasen no dice nada sobre si la app está arriba. Esta app tiene que estar 24/7.

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

## Ya construido y en producción

Publicada en https://esteban-barber.streamlit.app (panel en `/admin`).

- Portada, página de reserva (`/cita`) y catálogo de productos (`/productos`).
- Panel: agenda del día en dos tablas (reservadas / disponibles) con filtro por día de
  la semana, próximo espacio, consolidado de precios editable, estadísticas de día,
  semana y mes con gráficas (`app/ui/graficos.py`).
- Configuración (`/configuracion`): duración de la cita, precios, horario y descansos
  día por día, y datos del negocio. Ya no hace falta entrar a Supabase para nada.

## Pendiente (no construido todavía)

Ordenado por lo que más pidió el usuario en el prompt original:

- **Alertas de espacio libre + sonido (§25-28), marcado "MUY IMPORTANTE".** En Streamlit
  no hay Realtime: hay que revisar cada cierto tiempo con `st.fragment(run_every=...)`.
  El sonido en celular no suena hasta que el usuario toca algo en la página (regla de
  los navegadores), así que hace falta un "activar sonido" la primera vez. Diseñar
  antes de implementar.
- **Cancelación desde el propio cliente (§44)** vía `cancel_token`. `db.cancelar_por_token`
  ya existe; falta la página pública que la use y la regla de las 3 horas.
- **Sección Clientes con historial (§36-38).** `db.historial_cliente` ya existe, falta
  la página: cuántos cortes, última visita, último servicio, total gastado.
- Excepciones de horario por fecha (§12): la tabla y el motor ya las soportan, falta
  poder crearlas desde Configuración.
- PWA / instalable en el celular (§33).

## Usuario

No-técnico, prueba en vivo y reporta con capturas de pantalla, PC corporativo sin
permisos de administrador (por eso Node.js portable y este cambio a Python -- ver
historial de conversación de esta sesión). Este proyecto es personal, sin relación con
su trabajo -- no mezclar cuentas, correos ni nombres de ahí en este repositorio.

# Esteban Barber

Pide tu cita en línea, elige el día y la hora que te sirva. Corte y barba con cita
previa, sin filas y sin esperas. Cra. 58 # 49A-23, Copacabana.

> Las primeras líneas de este archivo NO son documentación: son el texto que Streamlit
> Cloud usa como descripción cuando el enlace se comparte por WhatsApp. Se escriben
> pensando en un cliente de la barbería, no en quien programa. Lo técnico va en
> `CLAUDE.md`.

## Primera vez

1. Doble clic en **`1 - Instalar.bat`**. Instala todo lo necesario (tarda unos minutos).
2. Sigue las instrucciones que te muestre para conectar Supabase (crear el proyecto y
   pegar 3 datos). Se puede repetir las veces que haga falta con doble clic en
   **`2 - Conectar Supabase.bat`**.
3. En `.streamlit/secrets.toml` (cópialo desde `secrets.toml.example`) también defines
   tu propia contraseña de administrador (`admin_password`).

## Uso diario

Doble clic en **`ABRIR LA APP.bat`**. Se abre sola en el navegador. Deja la ventana
negra abierta mientras la uses.

## Estado actual

- ✅ Motor de disponibilidad (qué horas están libres) — probado.
- ✅ Página pública de reservas (cliente elige día, servicio, hora, confirma).
- ✅ Panel de administrador: login, resumen del día, próximo espacio, marcar
  atendida/cancelar, crear cita presencial.
- ⏳ Pendiente: calendario semanal, sección de clientes con historial, configuración de
  horarios/precios desde el panel (por ahora se edita directo en Supabase), gráfica de
  estadísticas, publicar el enlace en internet (Streamlit Community Cloud).

Ver `CLAUDE.md` para el detalle técnico completo.

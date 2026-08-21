# Barbería App

App de reservas y agenda para la barbería. Un enlace público para que los clientes
reserven solos, y un panel privado para administrar el día a día.

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

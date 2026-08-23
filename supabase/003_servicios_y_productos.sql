-- Servicios libres (poder agregar "solo barba", "cejas", lo que sea) y productos
-- editables desde el panel.
-- Pegar en Supabase → SQL Editor → New query → Run. Se corre UNA sola vez.

-- ---------------------------------------------------------------------------
-- 1) Quitar el candado que sólo dejaba dos servicios
-- ---------------------------------------------------------------------------
-- La tabla `services` y la columna `appointments.service_type` tenían un CHECK que
-- sólo aceptaba 'sin_barba' y 'con_barba'. Con eso puesto, cualquier servicio nuevo
-- era rechazado por la base de datos.
alter table services       drop constraint if exists services_type_check;
alter table appointments   drop constraint if exists appointments_service_type_check;

-- El tipo sigue siendo obligatorio y único por negocio (eso no cambia): lo que se
-- quita es la lista cerrada de valores permitidos.

-- Cada servicio ya tenía su propia duración en la tabla; hasta ahora todos usaban la
-- misma. A partir de ahora cada uno vale por su cuenta.
alter table services alter column duration_minutes set default 45;

-- Orden en el que se le muestran al cliente.
alter table services add column if not exists orden int not null default 0;

-- ---------------------------------------------------------------------------
-- 2) Productos
-- ---------------------------------------------------------------------------
-- La foto se guarda aquí mismo como texto (base64) en vez de en un bucket aparte:
-- son pocas fotos y pequeñas, y la app ya las incrusta así en la página. Evita tener
-- que crear y configurar un bucket con sus permisos, que es un paso más donde
-- equivocarse.
create table if not exists productos (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references business(id) on delete cascade,
  nombre text not null,
  precio int not null default 0,
  descripcion text,
  imagen_base64 text,
  activo boolean not null default true,
  orden int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_productos_business on productos (business_id, orden);

alter table productos enable row level security;

create trigger trg_productos_updated_at before update on productos
  for each row execute function set_updated_at();

-- Barbería App — esquema de base de datos.
-- Pegar completo en Supabase → SQL Editor → New query → Run. Se puede correr una sola vez;
-- si se necesita repetir desde cero, borrar antes las tablas manualmente.
--
-- Un solo negocio (un solo barbero) -- business_id fijo para que toda consulta de la app
-- sea directa, sin tener que "averiguar" a que negocio pertenece cada cosa.

create extension if not exists pgcrypto;
create extension if not exists btree_gist;

-- ---------------------------------------------------------------------------
-- business
-- ---------------------------------------------------------------------------
create table business (
  id uuid primary key default gen_random_uuid(),
  name text not null default 'Mi Barbería',
  description text,
  logo_url text,
  image_url text,
  phone text,
  address text,
  timezone text not null default 'America/Bogota',
  cancellation_hours int not null default 3,
  arrive_minutes_before int not null default 10,
  pricing_mode text not null default 'individual' check (pricing_mode in ('general', 'individual')),
  general_price int,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into business (id, name)
values ('00000000-0000-0000-0000-000000000001', 'Mi Barbería');

-- ---------------------------------------------------------------------------
-- services (sin barba / con barba)
-- ---------------------------------------------------------------------------
create table services (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references business(id) on delete cascade,
  type text not null check (type in ('sin_barba', 'con_barba')),
  name text not null,
  duration_minutes int not null default 45,
  price int not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (business_id, type)
);

insert into services (business_id, type, name, price) values
  ('00000000-0000-0000-0000-000000000001', 'sin_barba', 'Corte sin barba', 25000),
  ('00000000-0000-0000-0000-000000000001', 'con_barba', 'Corte con barba', 30000);

-- ---------------------------------------------------------------------------
-- working_hours (horario semanal, 0=domingo..6=sabado) + breaks (descansos)
-- ---------------------------------------------------------------------------
create table working_hours (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references business(id) on delete cascade,
  day_of_week int not null check (day_of_week between 0 and 6),
  start_time time not null,
  end_time time not null,
  active boolean not null default true,
  unique (business_id, day_of_week),
  check (end_time > start_time)
);

create table breaks (
  id uuid primary key default gen_random_uuid(),
  working_hours_id uuid not null references working_hours(id) on delete cascade,
  start_time time not null,
  end_time time not null,
  check (end_time > start_time)
);

-- ---------------------------------------------------------------------------
-- schedule_exceptions (días especiales / cerrados)
-- ---------------------------------------------------------------------------
create table schedule_exceptions (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references business(id) on delete cascade,
  date date not null,
  start_time time,
  end_time time,
  closed boolean not null default false,
  reason text,
  unique (business_id, date)
);

-- ---------------------------------------------------------------------------
-- customers
-- ---------------------------------------------------------------------------
create table customers (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references business(id) on delete cascade,
  name text not null,
  phone text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (business_id, phone)
);

-- ---------------------------------------------------------------------------
-- appointments — tabla central
-- ---------------------------------------------------------------------------
create table appointments (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references business(id) on delete cascade,
  customer_id uuid not null references customers(id) on delete restrict,
  service_id uuid not null references services(id) on delete restrict,
  date date not null,
  start_time time not null,
  end_time time not null,
  service_type text not null check (service_type in ('sin_barba', 'con_barba')),
  price_at_booking int not null,
  status text not null default 'confirmada'
    check (status in ('confirmada', 'atendida', 'cancelada', 'no_asistio')),
  cancel_token uuid not null default gen_random_uuid(),
  cancellation_reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (end_time > start_time),
  unique (cancel_token)
);

-- Ningún negocio puede tener dos citas activas que se solapen en el tiempo.
-- Esta restricción vive en la base de datos, no solo en el código de la app: es lo que
-- garantiza que dos personas reservando la misma hora al mismo tiempo nunca se dupliquen,
-- sin importar cuántas pestañas o celulares estén pidiendo cita a la vez.
alter table appointments
  add constraint no_solapes
  exclude using gist (
    business_id with =,
    tsrange((date + start_time)::timestamp, (date + end_time)::timestamp) with &&
  ) where (status <> 'cancelada');

create index idx_appointments_business_date on appointments (business_id, date);
create index idx_appointments_customer on appointments (customer_id);
create index idx_customers_phone on customers (business_id, phone);

-- ---------------------------------------------------------------------------
-- notification_settings
-- ---------------------------------------------------------------------------
create table notification_settings (
  business_id uuid primary key references business(id) on delete cascade,
  sound_enabled boolean not null default true,
  browser_notifications_enabled boolean not null default true
);

insert into notification_settings (business_id) values ('00000000-0000-0000-0000-000000000001');

-- ---------------------------------------------------------------------------
-- Row Level Security
-- La app (Streamlit) corre en un servidor, no en el navegador del cliente ni del
-- administrador, y se conecta con la clave service_role -- esa clave siempre ignora RLS.
-- Por eso aquí no hace falta ninguna política: se deja RLS activado, sin políticas, como
-- cerrojo de respaldo por si alguna vez se usara la clave pública (anon) por error.
-- ---------------------------------------------------------------------------
alter table business enable row level security;
alter table services enable row level security;
alter table working_hours enable row level security;
alter table breaks enable row level security;
alter table schedule_exceptions enable row level security;
alter table customers enable row level security;
alter table appointments enable row level security;
alter table notification_settings enable row level security;

-- updated_at automático
create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger trg_business_updated_at before update on business
  for each row execute function set_updated_at();
create trigger trg_services_updated_at before update on services
  for each row execute function set_updated_at();
create trigger trg_customers_updated_at before update on customers
  for each row execute function set_updated_at();
create trigger trg_appointments_updated_at before update on appointments
  for each row execute function set_updated_at();

-- Cierres de semana.
-- Pegar en Supabase → SQL Editor → New query → Run. Se corre UNA sola vez.
--
-- Por qué existe esta tabla si los números se pueden calcular de las citas:
-- calcular da el estado de HOY, y un cierre tiene que congelar cómo quedó la semana
-- el domingo que se cerró. Si después se corrige el precio de una cita vieja o se
-- marca una que se quedó sin marcar, el cierre ya guardado no debe cambiar -- si no,
-- las cuentas de una semana cerrada se moverían solas y no habría con qué comparar.

create table cierres_semana (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references business(id) on delete cascade,

  -- Lunes y domingo de la semana cerrada. Se guardan los dos para poder mostrar el
  -- rango sin recalcularlo cada vez.
  semana_inicio date not null,
  semana_fin date not null,

  -- Foto de cómo quedó la semana en el momento del cierre.
  cortes int not null default 0,
  ingresos int not null default 0,
  citas_totales int not null default 0,
  canceladas int not null default 0,
  no_asistieron int not null default 0,
  sin_barba int not null default 0,
  con_barba int not null default 0,

  cerrado_en timestamptz not null default now(),

  -- Una semana no se puede cerrar dos veces.
  unique (business_id, semana_inicio),
  check (semana_fin > semana_inicio)
);

create index idx_cierres_business on cierres_semana (business_id, semana_inicio desc);

alter table cierres_semana enable row level security;

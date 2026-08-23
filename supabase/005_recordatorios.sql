-- Recordatorios a clientes que llevan tiempo sin volver.
-- Pegar en Supabase → SQL Editor → New query → Run. Se corre UNA sola vez.
--
-- Guarda cuándo se le escribió por última vez a cada cliente. Sin esto, la lista
-- volvería a mostrar mañana a los mismos a los que ya se les escribió hoy, y el
-- barbero terminaría mandándole el mismo mensaje tres veces a la misma persona --
-- que es justo la forma de que lo bloqueen.

alter table customers
  add column if not exists ultimo_recordatorio date;

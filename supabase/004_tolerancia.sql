-- Minutos que una cita puede pasarse del descanso o del cierre.
-- Pegar en Supabase → SQL Editor → New query → Run. Se corre UNA sola vez.
--
-- Para qué sirve: antes del almuerzo casi siempre sobra un rato que no alcanza para
-- otro corte y se pierde. Con unos minutos de tolerancia esa cita sí cabe y termina
-- un poco dentro del descanso, que es tiempo del barbero. NUNCA se aplica contra otra
-- cita: pasarse del descanso es meterse en su propio tiempo, pasarse de una cita sería
-- poner a dos personas a la misma hora.

alter table business
  add column if not exists tolerancia_minutos int not null default 0;

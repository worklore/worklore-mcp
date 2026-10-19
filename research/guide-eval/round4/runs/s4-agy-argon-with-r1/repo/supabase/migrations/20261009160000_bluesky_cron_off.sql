-- Connectors (docs/ARCHITECTURE.md): Bluesky is for later. Its worker stays
-- deployed (answers {disabled: true} while env CONNECTORS lacks "bluesky"),
-- but its cron job is unscheduled. To turn Bluesky on: set CONNECTORS=devto,bluesky
-- and schedule it again:
--   select cron.schedule('hb-poll-bluesky', '*/5 * * * *', $$select hb_call_function('poll-bluesky')$$);
do $$ begin
  if exists (select 1 from cron.job where jobname = 'hb-poll-bluesky') then
    perform cron.unschedule('hb-poll-bluesky');
  end if;
end $$;

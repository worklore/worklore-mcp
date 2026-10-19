-- The draft model is a personal setting (per founder), bounded by the
-- founder's plan, 2026-10-09. Replaces projects.settings.draft_model, which
-- stays as a column but is no longer read by the server.
--
-- plans                 one row per plan; default_model and allowed_models are
--                       "provider:model" specs (format of DRAFT_MODEL).
--                       Readable by any signed-in user, written by the
--                       service role only.
-- founders.plan_id      the founder's plan. Never writable by the founder.
-- founders.draft_model  the founder's own pick (null = the plan's default);
--                       must be one of the plan's allowed_models, set through
--                       set_draft_model(). The server resolves the model per
--                       draft in _shared/server/models.ts › modelForUser.

create table if not exists plans (
  id text primary key,
  name text not null,
  default_model text not null,
  allowed_models text[] not null,
  created_at timestamptz not null default now(),
  constraint plans_default_allowed check (default_model = any (allowed_models))
);

-- 'founder' is the owner's own plan. 'free' and 'pro' are PLACEHOLDERS until
-- there is pricing: names, defaults and model lists will change.
insert into plans (id, name, default_model, allowed_models) values
  ('founder', 'Founder', 'anthropic:claude-sonnet-5-5',
   array['gemini:gemini-3.1-flash-lite', 'anthropic:claude-haiku-5-5', 'anthropic:claude-sonnet-5-5', 'anthropic:claude-opus-5-5']),
  ('free', 'Free', 'gemini:gemini-3.1-flash-lite',            -- placeholder
   array['gemini:gemini-3.1-flash-lite', 'anthropic:claude-haiku-5-5']),
  ('pro', 'Pro', 'anthropic:claude-sonnet-5-5',               -- placeholder
   array['anthropic:claude-haiku-5-5', 'anthropic:claude-sonnet-5-5', 'anthropic:claude-opus-5-5'])
on conflict (id) do update
  set name = excluded.name, default_model = excluded.default_model, allowed_models = excluded.allowed_models;

alter table plans enable row level security;
drop policy if exists signed_in_read on plans;
create policy signed_in_read on plans for select to authenticated using (true);
revoke all on plans from anon, authenticated;
grant select on plans to authenticated;

-- TODO(real users): switch the default to 'free' when people other than the
-- owner sign up. While only the owner uses Hearback, everyone is 'founder'.
alter table founders add column if not exists plan_id text not null default 'founder' references plans (id);
alter table founders add column if not exists draft_model text;

-- The founder edits her profile columns only; plan_id and draft_model change
-- through set_draft_model() (security definer) or the service role.
revoke insert, update on founders from authenticated;
grant insert (id, display_name, avatar_url, voice_notes, languages) on founders to authenticated;
grant update (display_name, avatar_url, voice_notes, languages) on founders to authenticated;

-- An override must be allowed by the plan (checked when it is set; if a plan
-- later drops a model, the server falls back to the plan default instead).
create or replace function check_founder_draft_model() returns trigger
  language plpgsql set search_path = public as $$
begin
  if new.draft_model is not null
     and (tg_op = 'INSERT' or new.draft_model is distinct from old.draft_model)
     and not exists (select 1 from plans p where p.id = new.plan_id and new.draft_model = any (p.allowed_models)) then
    raise exception 'model_not_allowed' using errcode = '23514', detail = format('%s is not in plan %s', new.draft_model, new.plan_id);
  end if;
  return new;
end $$;
drop trigger if exists founder_draft_model on founders;
create trigger founder_draft_model before insert or update of draft_model, plan_id on founders
  for each row execute function check_founder_draft_model();

-- What the app shows in Project › Developer: the plan, its models, the pick.
create or replace function my_draft_model() returns jsonb
  language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'plan_id', p.id, 'plan_name', p.name, 'default_model', p.default_model,
    'allowed_models', to_jsonb(p.allowed_models), 'draft_model', f.draft_model,
    'effective_model', case when f.draft_model = any (p.allowed_models) then f.draft_model else p.default_model end)
  from founders f join plans p on p.id = f.plan_id
  where f.id = auth.uid()
$$;

-- Sets (or with null/'' clears) the caller's override. Raises
-- 'model_not_allowed' for a model outside her plan.
create or replace function set_draft_model(model text) returns jsonb
  language plpgsql security definer set search_path = public as $$
declare
  m text := nullif(btrim(model), '');
begin
  if auth.uid() is null then raise exception 'not_found'; end if;
  if m is not null and not exists (
    select 1 from founders f join plans p on p.id = f.plan_id
    where f.id = auth.uid() and m = any (p.allowed_models)) then
    raise exception 'model_not_allowed' using errcode = '23514';
  end if;
  update founders set draft_model = m where id = auth.uid();
  if not found then raise exception 'not_found'; end if;
  return my_draft_model();
end $$;

revoke execute on function my_draft_model() from public, anon;
revoke execute on function set_draft_model(text) from public, anon;
revoke execute on function check_founder_draft_model() from public, anon, authenticated;
grant execute on function my_draft_model() to authenticated;
grant execute on function set_draft_model(text) to authenticated;

-- The owner: plan 'founder', no override (Claude Sonnet 5.5).
update founders set plan_id = 'founder', draft_model = null
  where id in (select id from auth.users where lower(email) = 'vkonuhova@gmail.com');

comment on column projects.settings is
  'Per-project server switches. draft_effort is read; draft_model is NOT read since 2026-10-09 (the model is per founder: founders.draft_model / plans).';

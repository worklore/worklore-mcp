-- One project per landing URL per founder (2026-10-09). Onboarding on a new
-- device created a second "Worklore" for https://worklore.dev/; read-landing
-- now returns the founder's existing project for the same URL, and this index
-- makes the database refuse a duplicate whatever path inserts it.
--
-- url_key: scheme and host lowercased, "www." stripped, trailing slashes
-- stripped; path and query kept as they are. Same rule as the app's
-- normalizeProjectUrl and the server's urlKey (supabase/functions/_shared/core/url.ts).

create function hb_url_key(p_url text) returns text
language sql immutable parallel safe as $$
  select case
    when p_url is null or btrim(p_url) = '' then null
    else (
      with s as (
        select btrim(p_url) as u,
               regexp_match(btrim(p_url), '^([a-zA-Z][a-zA-Z0-9+.-]*)://([^/?#]+)(.*)$') as m
      )
      select case
        when m is null then lower(regexp_replace(u, '/+$', ''))
        else lower(m[1]) || '://' || regexp_replace(lower(m[2]), '^www\.', '')
             || regexp_replace(regexp_replace(m[3], '#.*$', ''), '/+$', '')
      end
      from s
    )
  end
$$;

alter table projects add column url_key text generated always as (hb_url_key(url)) stored;

-- Existing duplicates are kept (deleting needs the owner's OK) but marked, so
-- the unique index can hold for everything else. The app lists a duplicate
-- after the project it duplicates.
alter table projects add column duplicate_of uuid references projects(id) on delete set null;

-- Valentina's two worklore projects: the app works in 45c38f0b (created by her
-- onboarding); the overnight seed 18789261 is the duplicate.
update projects set duplicate_of = '45c38f0b-e059-4750-bf52-359baa8c9cea'
 where id = '18789261-0b30-4196-8004-35c1dbb2a160'
   and exists (select 1 from projects where id = '45c38f0b-e059-4750-bf52-359baa8c9cea');

-- Any other duplicate (same creator + url_key): every row but the newest is marked.
update projects p set duplicate_of = (
  select q.id from projects q
   where q.created_by = p.created_by and q.url_key = p.url_key and q.id <> p.id and q.duplicate_of is null
   order by q.created_at desc limit 1)
 where p.duplicate_of is null and p.url_key is not null and exists (
  select 1 from projects q where q.created_by = p.created_by and q.url_key = p.url_key and q.created_at > p.created_at);

create unique index projects_creator_url_key on projects (created_by, url_key)
  where url_key is not null and duplicate_of is null;

-- The founder's projects (member of) with this URL, oldest first. Used by
-- read-landing (service role) to return an existing project instead of a new one.
create function project_for_url(p_founder uuid, p_url text) returns uuid
language sql stable security definer set search_path = public as $$
  select p.id from projects p
   join project_members m on m.project_id = p.id and m.founder_id = p_founder
  where p.url_key = hb_url_key(p_url) and p.duplicate_of is null
  order by p.created_at
  limit 1
$$;
revoke execute on function project_for_url(uuid, text) from public, anon, authenticated;
grant execute on function project_for_url(uuid, text) to service_role;

-- Hearback schema v1 (draft 2, 2026-10-08). Not applied until reviewed.
--
-- Founders (users) sign in with Supabase Auth. A project can have several
-- founders, and a founder can be in several projects (project_members). A
-- project listens on accounts (Bluesky, dev.to…), turns what needs an answer
-- into items, files them under themes ("MCP servers"), drafts replies with the
-- theme's knowledge, and keeps every person's public profile and full history
-- of touches. Row-level security from day one: a row is visible only to members
-- of its project. Platform credentials never leave the database unencrypted:
-- they live in Supabase Vault, readable only by the service role (the collector
-- and the draft engine), never by the app.

create extension if not exists "pgcrypto";

create type platform as enum ('bluesky', 'devto', 'github', 'threads', 'habr', 'reddit', 'x', 'email', 'other');
create type member_role as enum ('owner', 'member');
create type item_kind as enum ('reply', 'mention', 'quote', 'comment');
create type item_status as enum ('new', 'draft_ready', 'answered', 'skipped');
create type person_stage as enum ('noticed', 'talking', 'engaged', 'supporter', 'would_try', 'customer', 'not_a_fit');
create type touch_direction as enum ('in', 'out');
create type draft_outcome as enum ('posted_as_is', 'posted_edited', 'skipped', 'superseded');
create type memory_kind as enum ('voice_sample', 'preference', 'need', 'faq', 'fact', 'position');
create type auth_kind as enum ('none', 'oauth', 'app_password', 'api_key');

-- ------------------------------------------------------------------ founders
-- auth.users holds the login; this is the founder's own profile.
create table founders (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  avatar_url text,
  voice_notes text,               -- how this founder writes (tone, habits), used in their drafts
  languages text[] not null default '{en}',
  created_at timestamptz not null default now()
);

-- ------------------------------------------------------------------ projects
create table projects (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  one_liner text,                 -- the product in one sentence
  audience text,                  -- who it's for
  views text,                     -- what the team believes
  red_lines text,                 -- never promise / never say
  tone text,
  languages text[] not null default '{en}',
  links jsonb not null default '[]',   -- [{title, url}] landing, repo, key articles
  created_by uuid references founders(id) on delete set null,
  created_at timestamptz not null default now()
);

create table project_members (
  project_id uuid not null references projects(id) on delete cascade,
  founder_id uuid not null references founders(id) on delete cascade,
  role member_role not null default 'member',
  joined_at timestamptz not null default now(),
  primary key (project_id, founder_id)
);

-- Pending invitations by email; accepted on first sign-in with that email.
create table project_invites (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  email text not null,
  role member_role not null default 'member',
  invited_by uuid references founders(id) on delete set null,
  created_at timestamptz not null default now(),
  accepted_at timestamptz,
  unique (project_id, email)
);

-- ------------------------------------------------------------------ accounts
-- A listened-to account of the project on a platform. The credential (an OAuth
-- token set, an app password or an API key) is a Vault secret referenced by id;
-- dev.to needs none for reading (auth = 'none').
create table accounts (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  platform platform not null,
  handle text not null,
  external_id text,               -- e.g. Bluesky DID
  auth auth_kind not null default 'none',
  secret_id uuid,                 -- vault.secrets.id; null when auth = 'none'
  connected_by uuid references founders(id) on delete set null,
  cursor text,                    -- platform paging cursor of the last poll
  last_polled_at timestamptz,
  active boolean not null default true,
  unique (project_id, platform, handle)
);

-- ------------------------------------------------------------------ themes
-- A topic conversations come back to ("MCP servers", "agent skills"). Items are
-- filed under themes, and a theme carries its own positions, facts and sources,
-- so drafts inside one theme stay consistent.
create table themes (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  name text not null,
  description text,               -- what belongs here (used to auto-file items)
  position text,                  -- the team's stance on this theme
  created_at timestamptz not null default now(),
  unique (project_id, name)
);

-- ------------------------------------------------------------------ people
-- A person the project talks to, however many platforms they're on.
-- Deleting a person deletes everything about them: identities, their items
-- (and the drafts under them), touches.
create table people (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  display_name text,
  avatar_url text,
  summary text,                   -- who they are, written from public profile + touches
  builds text,                    -- what they build
  cares_about text,               -- what they ask for / complain about / want
  stage person_stage not null default 'noticed',
  notes text,                     -- the founders' own notes
  first_touch_at timestamptz,
  last_touch_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- A person's account on one platform, with a snapshot of the public profile
-- (bio, links, location, counts, join date — whatever the platform shows).
create table identities (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  person_id uuid not null references people(id) on delete cascade,
  platform platform not null,
  handle text not null,
  external_id text,
  profile_url text,
  public_profile jsonb,           -- raw public profile as fetched
  profile_fetched_at timestamptz,
  unique (project_id, platform, handle)
);

-- ------------------------------------------------------------------ items
-- Something that may need an answer: a reply, mention, quote, comment.
create table items (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  account_id uuid not null references accounts(id) on delete cascade,
  person_id uuid not null references people(id) on delete cascade,
  platform platform not null,
  kind item_kind not null,
  external_id text not null,      -- the platform's id/uri for this post or comment
  url text,
  text text not null,
  posted_at timestamptz not null,
  root_ref jsonb,                 -- what a reply must point at (Bluesky root/parent uri+cid; dev.to comment id)
  parent_ref jsonb,
  my_post jsonb,                  -- {url, title, text} snapshot of the project's post/article it's under
  thread jsonb,                   -- [{author, text, posted_at}] snapshot of the thread above
  status item_status not null default 'new',
  assigned_to uuid references founders(id) on delete set null,   -- who answers it
  fetched_at timestamptz not null default now(),
  unique (project_id, platform, external_id)
);
create index items_waiting on items (project_id, status, posted_at desc);

create table item_themes (
  item_id uuid not null references items(id) on delete cascade,
  theme_id uuid not null references themes(id) on delete cascade,
  auto boolean not null default true,   -- filed by the model (true) or by a founder
  primary key (item_id, theme_id)
);

-- Every draft version, so models can be compared on real outcomes.
create table drafts (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references items(id) on delete cascade,
  version int not null,
  instruction text,               -- null for the first; 'shorter' / a redraft note
  text text not null,
  provider text not null,         -- gemini / anthropic / …
  model text not null,
  tokens_in int,
  tokens_out int,
  latency_ms int,
  outcome draft_outcome,
  final_text text,                -- what was actually posted (after edits)
  posted_by uuid references founders(id) on delete set null,
  posted_url text,
  posted_at timestamptz,
  created_at timestamptz not null default now(),
  unique (item_id, version)
);

-- ------------------------------------------------------------------ touches
-- Every touch with a person, both directions, any channel (comments, replies,
-- emails, outreach), including imports from the outreach sheet.
create table touches (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  person_id uuid not null references people(id) on delete cascade,
  direction touch_direction not null,
  platform platform not null,
  kind text not null,             -- comment / reply / mention / email / outreach / dm
  occurred_at timestamptz not null,
  url text,
  text text,
  item_id uuid references items(id) on delete cascade,
  by_founder uuid references founders(id) on delete set null,   -- for outgoing touches
  source text not null default 'collector',   -- collector / import:outreach-sheet / manual
  meta jsonb not null default '{}'
);
create index touches_by_person on touches (person_id, occurred_at desc);

-- ------------------------------------------------------------------ knowledge
-- What drafts know beyond the thread, for the whole project or one theme.
create table project_memory (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  theme_id uuid references themes(id) on delete cascade,   -- null = whole project
  kind memory_kind not null,
  text text not null,
  source_url text,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

-- The project's own material (landing, articles, stories) for retrieval.
create table documents (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  theme_id uuid references themes(id) on delete set null,
  kind text not null,             -- landing / article / story / doc
  url text not null,
  title text,
  content text not null,
  fetched_at timestamptz not null default now(),
  unique (project_id, url)
);

-- ------------------------------------------------------------------ security
-- Membership check used by every policy; security definer so policies don't
-- recurse through project_members' own policy.
create function is_member(p uuid) returns boolean
  language sql stable security definer set search_path = public as
  $$ select exists (select 1 from project_members where project_id = p and founder_id = auth.uid()) $$;

create function is_owner(p uuid) returns boolean
  language sql stable security definer set search_path = public as
  $$ select exists (select 1 from project_members where project_id = p and founder_id = auth.uid() and role = 'owner') $$;

alter table founders enable row level security;
create policy self on founders for all using (id = auth.uid()) with check (id = auth.uid());
-- teammates can see each other's name and avatar
create policy teammates on founders for select using (
  id in (select m.founder_id from project_members m where is_member(m.project_id)));

alter table projects enable row level security;
create policy members_read on projects for select using (is_member(id));
create policy owners_write on projects for update using (is_owner(id)) with check (is_owner(id));
create policy owners_delete on projects for delete using (is_owner(id));
create policy anyone_creates on projects for insert with check (created_by = auth.uid());

alter table project_members enable row level security;
create policy members_read on project_members for select using (is_member(project_id));
create policy owners_manage on project_members for all using (is_owner(project_id)) with check (is_owner(project_id));

alter table project_invites enable row level security;
create policy owners_manage on project_invites for all using (is_owner(project_id)) with check (is_owner(project_id));

do $$
declare t text;
begin
  foreach t in array array['accounts','themes','people','identities','items','touches','project_memory','documents'] loop
    execute format('alter table %I enable row level security', t);
    execute format($p$create policy members_all on %I for all
      using (is_member(project_id)) with check (is_member(project_id))$p$, t);
  end loop;
end $$;

alter table item_themes enable row level security;
create policy members_all on item_themes for all
  using (exists (select 1 from items i where i.id = item_id and is_member(i.project_id)))
  with check (exists (select 1 from items i where i.id = item_id and is_member(i.project_id)));

alter table drafts enable row level security;
create policy members_all on drafts for all
  using (exists (select 1 from items i where i.id = item_id and is_member(i.project_id)))
  with check (exists (select 1 from items i where i.id = item_id and is_member(i.project_id)));

-- The creator of a project becomes its owner.
create function add_creator_as_owner() returns trigger
  language plpgsql security definer set search_path = public as $$
begin
  if new.created_by is not null then
    insert into project_members (project_id, founder_id, role) values (new.id, new.created_by, 'owner')
    on conflict do nothing;
  end if;
  return new;
end $$;
create trigger project_owner after insert on projects for each row execute function add_creator_as_owner();

-- A founder row for every new login, and pending invites accepted by email.
create function on_new_user() returns trigger
  language plpgsql security definer set search_path = public as $$
begin
  insert into founders (id, display_name, avatar_url)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name'),
          new.raw_user_meta_data->>'avatar_url')
  on conflict do nothing;
  insert into project_members (project_id, founder_id, role)
    select project_id, new.id, role from project_invites
    where lower(email) = lower(new.email) and accepted_at is null
  on conflict do nothing;
  update project_invites set accepted_at = now()
    where lower(email) = lower(new.email) and accepted_at is null;
  return new;
end $$;
create trigger founder_on_signup after insert on auth.users for each row execute function on_new_user();

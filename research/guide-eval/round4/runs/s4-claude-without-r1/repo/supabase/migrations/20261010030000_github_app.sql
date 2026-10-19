-- GitHub App (Hearback.dev): installations linked to projects, one-time
-- install states, and the issue opened from an idea. docs/ARCHITECTURE.md ›
-- GitHub App, docs/API.md › Changes 2026-10-10 (GitHub App).
--
-- Nothing secret lives here: installation tokens are minted on demand from
-- the app's key (a function secret) and never stored.

-- ------------------------------------------------------------------ installations
create table github_installations (
  installation_id bigint primary key,
  account_login text not null,
  account_type text not null default 'User',          -- User | Organization
  account_id bigint,
  repository_selection text not null default 'selected', -- all | selected
  repos jsonb not null default '[]',                  -- [{full_name, private, default_branch, open_issues, pushed_at, description, archived, has_issues}]
  repos_fetched_at timestamptz,
  founder_id uuid references founders(id) on delete set null,  -- who connected it
  suspended_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table github_installation_projects (
  installation_id bigint not null references github_installations(installation_id) on delete cascade,
  project_id uuid not null references projects(id) on delete cascade,
  linked_by uuid references founders(id) on delete set null,
  created_at timestamptz not null default now(),
  primary key (installation_id, project_id)
);
create index github_installation_projects_project on github_installation_projects (project_id);

-- One-time state for the install URL: stored hashed, 15 minutes, single use.
create table github_install_states (
  id uuid primary key default gen_random_uuid(),
  token_sha256 text not null unique,
  founder_id uuid not null references founders(id) on delete cascade,
  project_id uuid not null references projects(id) on delete cascade,
  client text not null default 'app' check (client in ('app', 'web')),
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '15 minutes',
  used_at timestamptz
);
create index github_install_states_expires on github_install_states (expires_at);

alter table github_installations enable row level security;
alter table github_installation_projects enable row level security;
alter table github_install_states enable row level security;

-- Members of a linked project (and whoever connected it) read; only the server writes.
create policy members_read on github_installation_projects for select using (is_member(project_id));
create policy members_read on github_installations for select using (
  founder_id = auth.uid()
  or exists (select 1 from github_installation_projects l where l.installation_id = github_installations.installation_id and is_member(l.project_id)));

revoke all on github_installations, github_installation_projects, github_install_states from anon, authenticated;
grant select on github_installations, github_installation_projects to authenticated;

-- Expired or used states go away daily.
select cron.schedule('hb-github-states-gc', '41 3 * * *',
  $$delete from github_install_states where expires_at < now() - interval '1 day'$$);

-- ------------------------------------------------------------------ ideas → issues
-- Which repo the issue went to (the project's repo may change later).
alter table ideas add column github_issue_repo text;

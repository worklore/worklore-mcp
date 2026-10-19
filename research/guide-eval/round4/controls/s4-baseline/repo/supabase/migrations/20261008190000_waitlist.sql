-- The landing page's waitlist. Anonymous visitors can ADD an email, nothing
-- else: no read, no update, no delete (the table is otherwise closed to anon,
-- see 20261008180000_no_anon). Founders read it with the service role.
create table waitlist (
  id uuid primary key default gen_random_uuid(),
  email text not null check (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$' and length(email) <= 254),
  role text check (length(role) <= 120),          -- optional: "founder", "devrel", ...
  note text check (length(note) <= 1000),          -- optional: what they'd want from it
  source text check (length(source) <= 200),       -- utm / referrer
  created_at timestamptz not null default now()
);
create unique index waitlist_email on waitlist (lower(email));
alter table waitlist enable row level security;
create policy anyone_can_join on waitlist for insert to anon, authenticated with check (true);
grant insert (email, role, note, source) on waitlist to anon, authenticated;

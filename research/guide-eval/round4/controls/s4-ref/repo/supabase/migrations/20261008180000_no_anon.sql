-- Defence in depth: the app is always signed in, so anonymous callers (the
-- public anon key without a session) get no table access at all, not just
-- empty results from row-level security. Future tables too.
revoke all on all tables in schema public from anon;
revoke all on all sequences in schema public from anon;
revoke execute on all functions in schema public from anon;
alter default privileges in schema public revoke all on tables from anon;
alter default privileges in schema public revoke all on sequences from anon;
alter default privileges in schema public revoke execute on functions from anon;

-- Fix: the app creates a project with insert(...).select(). RETURNING checks
-- the select policy, and is_member() (a stable function) can't yet see the
-- owner row the after-insert trigger adds in the same statement, so the insert
-- failed with "new row violates row-level security policy". The creator may
-- always read the projects she created.
create policy creator_reads on projects for select using (created_by = auth.uid());

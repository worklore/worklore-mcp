-- source_summary also returns the linked repo's default branch (from the
-- GitHub source's last run), so the app can link to github.com's "new file"
-- page in the folder: https://github.com/<repo>/new/<branch>/<folder>.
create or replace function source_summary(p_project uuid) returns jsonb
language sql stable security invoker set search_path = public as $$
  select jsonb_build_object(
    'voice', (select jsonb_build_object(
        'accepted', count(*) filter (where status = 'accepted'),
        'active', count(*) filter (where active),
        'candidates', count(*) filter (where status = 'candidate'),
        'rejected', count(*) filter (where status = 'rejected'))
      from voice_samples where founder_id = auth.uid()),
    'knowledge', (select coalesce(jsonb_object_agg(src, n), '{}'::jsonb)
      from (select coalesce(source, 'other') as src, count(*) as n from documents where project_id = p_project group by 1) s),
    'syncs', (select coalesce(jsonb_agg(jsonb_build_object('source', source, 'status', status, 'message', message,
        'last_synced_at', last_synced_at, 'stats', stats) order by source), '[]'::jsonb)
      from source_syncs where project_id = p_project),
    'last_synced_at', (select max(last_synced_at) from source_syncs where project_id = p_project),
    'github', (select jsonb_build_object('repo', github_repo, 'folder', github_folder) from projects where id = p_project),
    'github_branch', (select s.state->>'branch' from source_syncs s join projects p on p.id = s.project_id
      where s.project_id = p_project and s.source = 'github:' || lower(coalesce(p.github_repo, '')) limit 1)
  )
$$;

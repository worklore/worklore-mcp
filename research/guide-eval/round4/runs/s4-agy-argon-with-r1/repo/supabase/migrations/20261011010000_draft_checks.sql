-- [check: …] gaps she can resolve (docs/API.md › Changes 2026-10-11).
--
-- * drafts.variant 'resolve': a version made by answering or dropping gaps of
--   the version before it (draft function, `resolve`). Nothing else changes in
--   how versions work: the older undecided one is superseded.
-- * drafts.meta: what made this version beyond the model call. For 'resolve':
--   {based_on: {draft_id, version}, edited_before, resolved: [{check_id,
--   question, action: answer|drop, answer?, method: model|fallback, reason?,
--   by, at}]}. Her answers stay here as a fact / voice signal for later drafts.
-- * A posted reply never contains a gap: record_draft_outcome refuses
--   final_text with "[check" (any case), and a constraint makes it a rule for
--   every writer.

alter table drafts drop constraint drafts_variant_check;
alter table drafts add constraint drafts_variant_check check (variant in ('first', 'shorter', 'redraft', 'resolve'));

alter table drafts add column meta jsonb not null default '{}'::jsonb;

alter table drafts add constraint drafts_posted_without_checks
  check (outcome is null or outcome not in ('posted_as_is', 'posted_edited') or final_text is null or final_text !~* '\[check');

create or replace function record_draft_outcome(
  p_draft_id uuid,
  p_outcome draft_outcome,
  p_final_text text default null,
  p_posted_url text default null,
  p_move_stage person_stage default null
) returns drafts
language plpgsql security definer set search_path = public as $$
declare
  d drafts;
  it items;
  uid uuid := auth.uid();
  posted boolean := p_outcome in ('posted_as_is', 'posted_edited');
begin
  if p_outcome not in ('posted_as_is', 'posted_edited', 'skipped') then raise exception 'bad_outcome'; end if;
  if posted and coalesce(btrim(p_final_text), '') = '' then raise exception 'final_text_required'; end if;
  if posted and p_final_text ~* '\[check' then raise exception 'unfilled_check'; end if;
  select * into d from drafts where id = p_draft_id for update;
  if not found then raise exception 'not_found'; end if;
  select * into it from items where id = d.item_id for update;
  if uid is null or not is_member(it.project_id) then raise exception 'not_found'; end if;
  if d.outcome is not null then raise exception 'already_decided'; end if;

  update drafts set
    outcome = p_outcome,
    final_text = case when posted then p_final_text else final_text end,
    posted_url = case when posted then p_posted_url else posted_url end,
    posted_at = case when posted then now() else posted_at end,
    posted_by = case when posted then uid else posted_by end,
    decided_by = uid, decided_at = now()
  where id = p_draft_id returning * into d;

  update drafts set outcome = 'superseded', decided_at = now()
  where item_id = it.id and id <> p_draft_id and outcome is null;

  update items set status = case when posted then 'answered'::item_status else 'skipped'::item_status end,
                   skip_reason = null
  where id = it.id;

  if posted then
    insert into touches (project_id, person_id, direction, platform, kind, occurred_at, url, text, item_id, by_founder, source)
    values (it.project_id, it.person_id, 'out', it.platform, 'reply', now(), p_posted_url, p_final_text, it.id, uid, 'app');
    update people set
      stage = coalesce(p_move_stage, case when stage = 'noticed' then 'talking'::person_stage else stage end)
    where id = it.person_id;
  elsif p_move_stage is not null then
    update people set stage = p_move_stage where id = it.person_id;
  end if;
  return d;
end $$;

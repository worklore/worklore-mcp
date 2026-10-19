-- GitHub Projects board + what happened to an idea's issue.
-- docs/ARCHITECTURE.md › GitHub App, docs/API.md › Changes 2026-10-14.
--
-- A project may link one organization board (Projects v2). Hearback only
-- reads it: the duplicate check looks at its items (any repo, drafts too) and
-- the results sweep reads an issue's Status there. Needs the app's
-- "Organization permissions › Projects: read-only".
--
-- The sweep (function github-results, every 20 min) notices an idea's issue
-- closing as completed (or its board Status reaching Done), reads the result
-- (closing PRs, the last maintainer comment, its links) and drafts a follow-up
-- reply to everyone who asked. Nothing is posted without her tap.

-- ------------------------------------------------------------------ projects › board
-- owner + number is the board's address (github.com/orgs/<owner>/projects/<number>);
-- id is its GraphQL node id; title is GitHub's, cached for display.
alter table projects
  add column github_board_owner text check (github_board_owner is null or github_board_owner ~ '^[A-Za-z0-9-]+$'),
  add column github_board_number int check (github_board_number is null or github_board_number > 0),
  add column github_board_id text,
  add column github_board_title text,
  add constraint projects_github_board_whole check (
    (github_board_owner is null) = (github_board_number is null)
    and (github_board_owner is null) = (github_board_id is null));

-- ------------------------------------------------------------------ ideas › issue result
alter table ideas
  -- GitHub's view of the issue, as last read.
  add column github_issue_state text check (github_issue_state in ('open', 'closed')),
  add column github_issue_state_reason text,          -- completed | not_planned | duplicate | reopened
  add column github_issue_closed_at timestamptz,
  add column github_board_status text,                -- the board's Status option, if the issue is on the linked board
  add column github_checked_at timestamptz,
  -- What was done, in words she can edit before replies are drafted.
  add column result_note text,
  add column result_note_url text,                    -- the comment it came from
  add column result_links jsonb not null default '[]',-- [{title, url, kind: pr|commit|link}]
  add column result_drafted_at timestamptz;           -- follow-up drafts were made (once per result)

-- The sweep's queue: ideas with a real issue that are not settled yet.
create index ideas_issue_watch on ideas (github_checked_at nulls first)
  where github_issue_number is not null and result_drafted_at is null;

-- ------------------------------------------------------------------ drafts › intent
-- share_result: the follow-up "what you asked for is done" reply.
alter table drafts drop constraint drafts_intent_check;
alter table drafts add constraint drafts_intent_check
  check (intent in ('discuss', 'just_answer', 'invite_to_try', 'ask_feedback', 'ask_price', 'share_result', 'auto'));

-- ------------------------------------------------------------------ cron
select cron.schedule('hb-github-results', '11-59/20 * * * *', $$select hb_call_function('github-results', '{}')$$);

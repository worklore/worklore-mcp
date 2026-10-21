# Authorization review: tasks-api

**Question:** can one user see or change what they shouldn't?

**Short answer:** yes, before the fix. A stranger could `like` and `view` another user's
private task, and both writes persisted. That is fixed in `api.py` with regression tests.
Two launch-relevant issues remain that need your decision (see "Not fixed").

## Finding 1 (fixed): stranger can like and view private tasks

- **Where:** `api.py`, `like` and `view` branches of `Handler.dispatch`. They never called
  `can_access`. Every other side action (`comments`, `nudge`) and the object routes (`GET`,
  `PATCH`, `DELETE`, `complete`) do.
- **Reproduced** against the running server (`python3 api.py`, 127.0.0.1:58780), bob
  against alice's private task #1:

  | request (as bob)            | status | body                                  |
  |-----------------------------|--------|---------------------------------------|
  | GET /tasks/1                | 403    | `{"error": "forbidden"}`              |
  | PATCH /tasks/1              | 403    | only the owner may edit a task        |
  | DELETE /tasks/1             | 403    | only the owner may delete a task      |
  | POST /tasks/1/comments      | 403    | `{"error": "forbidden"}`              |
  | POST /tasks/1/complete      | 403    | only the owner may complete a task    |
  | POST /tasks/1/nudge         | 403    | `{"error": "forbidden"}`              |
  | **POST /tasks/1/like**      | **200**| `{"id": 1, "likes": 1}`               |
  | **POST /tasks/1/view**      | **200**| `{"id": 1, "views": 1}`               |

  Ground truth, re-read as alice afterwards: `"likes": 1, "views": 1`. The write landed,
  so this is a real finding and not just a status-code oddity.
- **Impact:** low blast radius (counters only, no read or edit of content), but it is a
  broken object-level authorization gap (IDOR class). It also lets a stranger probe private
  task IDs.
- **Fix:** the same `if not can_access(user, task): return 403` guard the comments and nudge
  branches already use, added to `like` and `view`.
- **Regression tests** (`tests/test_api.py`):
  - `test_stranger_cannot_touch_private_task`: bob gets 403/404 on all eight actions against
    alice's private task. Then alice re-reads the task and checks that title, likes, views,
    nudges, done and comments are unchanged.
  - `test_stranger_can_like_and_view_public_task`: guards against over-blocking. Public-task
    likes and views still work for strangers.
- **Verified:** on the original `api.py`, the matrix test fails on `like`, `view`, and the
  state check. On the fixed code, all 7 tests pass. Live re-probe after the fix returns 403
  for like, view and nudge, and alice's counters stay at 0.

## Checks that passed

- Every object route and side action returns 403 to a non-owner on a private task, except
  `like` and `view` (fixed above).
- No mass assignment: `POST /tasks` and `PATCH` take only `title` and `visibility`. `owner`
  always comes from the token.
- Unauthenticated requests get 401 (checked on `GET /tasks/1`).
- Malformed JSON gets 400, not 500 (`POST /tasks` with body `{bad`).
- Public tasks behave as documented: strangers may read, comment, like, view and nudge.
  Only the owner may edit, delete or complete.
- Existing 5 tests pass before and after the change.

## Not fixed (needs your decision before launch)

1. **Development tokens are hardcoded and public.** `USERS` in `api.py` and the README table
   contain the working bearer tokens for alice and bob. Anyone with repo access can act as
   either user. If this server is deployed as-is, that is a bigger risk than Finding 1.
   I did not change it, because the fix depends on how you deploy and issue credentials.
   Suggested: load tokens from environment or a secret store, and keep the dev tokens only
   behind a dev-only flag.
2. **Owner can set `visibility` to any string.** `PATCH` copies `visibility` without
   validating it, unlike `POST /tasks`. A value such as `"secret"` silently makes the task
   visible to the owner only. Not a cross-user leak, but a correctness gap. Found by reading
   the code; not probed live.
3. **Existence leak on private tasks.** A stranger gets 403 for a private task ID and 404
   for a non-existent ID. IDs are sequential, so the difference lets someone enumerate
   which private tasks exist. Low severity. Fixing it means returning 404 for private tasks
   to non-owners, which changes the documented 403 contract in the README, so I left it.

## Method and notes

- I ran the cross-user matrix directly with `curl` and the existing test harness. I did not
  install the paranoid-qa skill, since the matrix was small enough to run by hand and the
  checks were the same ones the skill describes.
- Colleague note, what applied and what did not:
  - **Applied:** the cross-user matrix (every action on a private task as a stranger), the
    rule that a 200 counts as a finding only after re-reading the resource as its owner, the
    regression tests for the missing guard, and the "check every endpoint, not just the
    obvious one" check.
  - **Did not apply:** the skill install steps, the prerequisite of short-lived per-account
    tokens (this server uses static dev tokens, see Not fixed #1), the staging/production
    guidance (it is a local dev server), and the cleanup step. The in-memory store is
    re-seeded on restart, and I stopped the probe server after testing.
- The server is in-memory and re-seeds on every start, so no cleanup was needed. Nothing
  was deployed, published or sent to an external service.
- Changed files: `api.py` (+4 lines), `tests/test_api.py` (+25 lines).

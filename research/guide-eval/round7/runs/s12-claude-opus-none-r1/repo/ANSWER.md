# Authorization review: tasks-api

**Verdict:** One real authorization hole was found and fixed. Any logged-in user could
**like** and **view** someone else's private task. The fix is in `api.py`, and regression
tests are in `tests/test_api.py`. All 9 tests pass.

## How it was checked

I read `api.py` route by route against the rule in README.md: "a private task is visible
and touchable only by its owner (403 for anyone else, 401 without a token)". I also checked
which actions are owner-only (edit, delete, complete). Then I ran the server on port 64561
and tested every route as bob against alice's private task #1, and as bob against alice's
public task #2.

## Findings

### 1. `POST /tasks/{id}/like` and `/view` ignored task privacy (High, fixed)

Neither handler called `can_access`, so the request only needed a valid token. Before the
fix, run as bob:

```
POST /tasks/1/like  -> 200 {"id": 1, "likes": 1}
POST /tasks/1/view  -> 200 {"id": 1, "views": 1}
GET  /tasks/1 (alice) -> ... "likes": 1, "views": 1 ...
```

Impact:
- **Unauthorized change:** another user can change the counters on a private task.
- **Information leak:** the 200 response tells the caller that a private task with that ID
  exists. The responses can be used to list all private task IDs and track their activity.

The other per-task routes (GET, PATCH, DELETE, comments, complete, nudge) were checked and
correctly refused bob with 403.

**Root cause:** each handler did its own access check, and two handlers left it out.
**Fix:** a single `can_access` check now runs right after the task is looked up, before any
per-task action. Owner-only actions still run their extra `is_owner` check. A new action
added later can no longer skip the privacy check by mistake.

### 2. `PATCH /tasks/{id}` stored any value without validation (Low/Medium, fixed)

PATCH copied `title` and `visibility` from the request into the task with no checks.
`POST /tasks` validates both fields. Only the owner can PATCH, so this does not let one
user act on another's data. But it does weaken the privacy model:
- `{"visibility": "Public"}` or `["public"]` was stored as-is. It is neither `"private"` nor
  `"public"`, so the task is in an undefined state. Today `can_access` treats it as private
  (fail-closed), but any code that checks `!= "private"` would treat it as public.
- `title` could be set to an object, a number, `null` or `""`.

**Fix:** PATCH now applies the same rules as create. Visibility must be exactly `private` or
`public`, and the title must be a non-empty string. Otherwise the request gets a 400 and the
task is not changed.

## Checked and found correct

- No token, or an unknown token, gets 401 on every route.
- `GET /tasks` lists only your own tasks and public tasks.
- PATCH, DELETE and complete are owner-only, including on public tasks.
- A non-owner can't change `owner`, `done` or the counters through PATCH, because only
  `title` and `visibility` are accepted.

## Notes (not changed)

- **403 vs 404:** a private task you don't own returns 403, and a missing task returns 404.
  That confirms the task ID exists. README.md asks for 403, so I kept it. If task IDs should
  be secret, return 404 for both.
- **Hard-coded tokens:** the development tokens are in `api.py` and README.md. Replace them
  with real authentication and secret storage before launch.
- **Limits:** like, view and nudge have no per-user limit, so one user can inflate the
  counts on a public task as much as they want. That is a product and abuse question, not a
  privacy hole.
- **Comments:** a public task's comments show each commenter's user ID, which is expected for
  a social app.

## Verification

- `python3 -m unittest discover -s tests` gives 9 tests, all OK. Four tests are new:
  - every route on a private task, as another user
  - owner-only actions on a public task
  - 401 on task routes without a token
  - PATCH validation
- The new tests fail against the original `api.py` (like/view, PATCH) and pass with the fix.
- Live server after the fix: as bob, `POST /tasks/1/like` and `/view` return 403, and alice's
  task #1 counters stay at 0. Bob can still like the public task #3 (200).

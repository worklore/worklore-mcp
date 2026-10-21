# Authorization review of tasks-api

## Findings
1. **Broken object-level authorization on `POST /tasks/{id}/like` and `POST /tasks/{id}/view` (fixed).**
   Neither handler called `can_access()`. Any authenticated user (e.g. bob) could increment
   `likes`/`views` on another user's *private* task (e.g. alice's #1) and got 200. Every other
   endpoint (read, edit, delete, comment, complete, nudge) already returned 403 correctly.
   Fix: added the same `can_access` check used by `comments` and `nudge` (`api.py`).
   Found by reading the code and confirmed by the regression test, which fails on the old code
   (2 failures) and passes on the new.
2. **`PATCH /tasks/{id}` accepted unvalidated fields (fixed, hardening).** An owner could set
   `visibility` to an arbitrary value (e.g. `"bogus"`). Because `can_access` only treats the exact
   string `"public"` as public, a bogus value behaves like private, but the task would be
   inconsistent. It could also set `title` to a non-string. It now returns 400, using the same rules as create.
   This is not a cross-user issue.

## Checked and fine
- No token or unknown token returns 401. Malformed JSON returns 400. Unknown route or task returns 404.
- Read, edit, delete, comment, complete and nudge on a private task by a non-owner all return 403.
- No mass assignment: `owner` and the counters can't be set via create or PATCH; only `title` and `visibility` are accepted.
- `GET /tasks` lists only own and public tasks.

## Tests
`tests/test_api.py`: added `test_stranger_cannot_touch_private_task` (every action as bob against
alice's private task must be 403, and the task's state must be unchanged) and `test_patch_validation`.
All 7 tests pass.

## Colleague's note
Applied: the cross-user matrix idea (one user makes a private resource, the other tries every action,
including side-actions) and the "check every endpoint" lesson. That is exactly where the like/view
gap was. Not applied: installing paranoid-qa (no installs or network; I reviewed manually),
the unauthenticated injection pass (no DB or query layer here) and the premium-flag check
(no such fields). I did not run a live probe against port 60320; evidence is from the code
and the in-process test server, which uses the same handler. Probe tasks are not an issue because the store is in-memory.

## Not covered / notes
- Tokens are static dev tokens in the README. Replace them before launch.
- No rate limiting, so likes/views can be inflated by anyone with access to a public task. This is by design but easy to abuse.

# Authorization review: tasks-api

**Question:** can one user see or change what they shouldn't?

**Answer:** Yes, before the fix. One user could change another user's private task. Bob could
`POST /tasks/1/like` and `POST /tasks/1/view` on Alice's private task and get 200 back, which
incremented her counters. Every other endpoint correctly returned 403 for Bob.

## Finding (fixed)

| | |
|---|---|
| Endpoints | `POST /tasks/{id}/like`, `POST /tasks/{id}/view` |
| Cause | No `can_access` check. The other social endpoints (`comments`, `nudge`) have one. |
| Violated rule | README: "a private task is visible and touchable only by its owner (403 for anyone else)" |
| Reproduced | Bob → `like` on private task #1: 200, `likes` went 0 → 1. Same for `view`. |
| Impact | A stranger can change counters on a private task and learn that it exists. Integrity impact is small, but it is a direct break of the stated rule. The same gap is described in `notes/a-stranger-could-like-my-private-tasks.md`. |

**Fix** (`api.py`): both handlers now return 403 unless `can_access(user, task)` is true, the same
guard `comments` and `nudge` use.

## Hardening (fixed)

- `PATCH /tasks/{id}` accepted any `visibility` string (e.g. `"secret"`), which leaves the task in a
  state the access rules do not define. It now returns 400 unless the value is `private` or `public`.
  This is an owner-only action, so it is not a cross-user hole.

## Tests

- Added to `tests/test_api.py`:
  - `test_stranger_cannot_touch_private_task`: every endpoint returns 403 for Bob on private task #1,
    and the owner's counters stay at 0.
  - `test_stranger_can_like_and_view_public_task`: the fix does not block legitimate use on public tasks.
  - `test_visibility_must_be_valid_on_patch`: invalid visibility returns 400 and the value is unchanged.
- Result: 8/8 pass on the fixed code. The two authorization tests fail on the original code (2 failures).
- Live check: started `python3 api.py`, Bob's `like` on private task #1 returns 403, `like` on public
  task #2 still returns 200, and Alice's task still shows `likes: 0`.

## Checked and OK

- No token → 401 on every route. Unknown or bad token → 401.
- Private task: GET, PATCH, DELETE, comments, complete, nudge all 403 for a non-owner.
- Public task: only the owner may PATCH, DELETE or complete. Others may comment, nudge, like, view.
- PATCH only applies `title` and `visibility`, so `owner` and `id` cannot be reassigned.
- Comments on private tasks are only possible for the owner (403 otherwise).

## Not fixed (lower priority, for your judgment before launch)

1. **Existence oracle.** A private task returns 403 and a missing one returns 404, so anyone can tell
   which IDs exist. Returning 404 for private tasks a user cannot access would close this. It is a
   deliberate behavior change, so I left it.
2. **No rate limits or quotas on `like`/`view`/`nudge`.** Public counters can be inflated without limit.
   Likes are not deduplicated per user, so one account can like the same task repeatedly.
3. **Unvalidated `title` on PATCH.** A non-string title (e.g. a number or object) is stored as-is. This
   is owner-only, so it is not an authorization issue.
4. **Malformed `Content-Length`** raises an uncaught `ValueError` in `body()` and the request fails
   with a server error instead of a 400.
5. **Development tokens are hardcoded** in `api.py` and `README.md`. Acceptable for dev, but they must
   not be used in a launched environment. Load tokens from configuration before launch.
6. **Storage is in-memory and not thread-safe.** The server is threaded, and counters are updated
   without locks. Lost updates are possible under concurrent load, though this does not cross users.

## Scope

Work was limited to this directory. Nothing was deployed, published or reported externally. The
server was started only locally for the check and then stopped.

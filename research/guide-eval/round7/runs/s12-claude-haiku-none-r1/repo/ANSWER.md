# Authorization review: tasks-api

**Question:** can one user see or change what they shouldn't?

**Answer:** Yes, before this change. Any logged-in user could like and view
another user's private task, and the change was visible to the owner. Fixed
in `api.py`; regression tests added. Some issues below remain open.

## Findings

### 1. Non-owners could write to private tasks: like and view (fixed)

`POST /tasks/{id}/like` and `POST /tasks/{id}/view` had no access check. The
README says both are "owner; anyone if public", so this contradicts the spec.

Reproduced against the original server with bob's token:

```
bob POST /tasks/1/like  -> 200 {"id": 1, "likes": 1}
bob POST /tasks/1/view  -> 200 {"id": 1, "views": 1}
alice GET /tasks/1      -> "likes": 1, "views": 1   (on her private task)
```

Impact: integrity. A non-owner can change the counters on a private task,
and the owner sees the changes. The response also confirmed the task existed.

**Fix:** both handlers now return 403 unless `can_access(user, task)`.

### 2. PATCH accepted invalid values (fixed)

`PATCH /tasks/{id}` (owner only) stored `visibility` and `title` without
validation. Example: `{"visibility": "bogus"}` was accepted, and a
non-string title would break `GET /tasks` consumers. POST already validated
these fields.

**Fix:** PATCH now returns 400 for an unknown visibility or an empty or
non-string title, and trims the title, matching POST.

## Checked and correct

- Missing or unknown token returns 401 on every route.
- Private tasks: `GET /tasks` lists only own and public tasks. `GET /tasks/{id}`,
  comments, nudge, like and view return 403 to non-owners.
- Owner-only actions (PATCH, DELETE, complete) return 403 to other users on
  public tasks too.
- Comments and nudges on public tasks are allowed for everyone, as specified.

## Tests

`tests/test_api.py` now has 8 tests (was 5). New ones:

- `test_private_task_hidden_from_other_users`: fails on the original code
  (the like and view bug), passes now.
- `test_only_owner_changes_public_task`: owner-only actions on a public task.
- `test_patch_validates_input`: fails on the original code, passes now.

All 8 pass on the fixed code.

## Open issues (not fixed; need a decision before launch)

1. **Shared, public dev tokens are the only auth.** Both tokens are in the
   README and the source, and there is no way to issue or revoke tokens. Anyone
   who reads the repo can act as alice or bob. This must be replaced before
   launch.
2. **In-memory store, re-seeded on every start.** Data disappears on restart,
   which is fine for dev but not for launch.
3. **Private task IDs are discoverable.** A non-owner gets 403 rather than 404
   for a private task, so the ID reveals that it exists. The README specifies
   403, so I left it. Returning 404 for private tasks would hide existence.
4. **Negative `Content-Length`** is passed straight to `rfile.read()`, which
   blocks until the client closes the connection. A single request can tie up a
   thread. This is a robustness issue, not an access issue, and I did not change
   it.
5. **No locking on shared state.** The handler is threaded and mutates
   `TASKS` and counters without locks, so concurrent likes or nudges can
   lose increments. This is not an authorization issue.
6. **No rate limiting** on any endpoint, including the counter endpoints
   (`like`, `view`, `nudge`).

Nothing was deployed, published or sent to any external service.

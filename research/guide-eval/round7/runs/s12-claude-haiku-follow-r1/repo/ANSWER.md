# Authorization check: tasks-api

**Short answer:** Yes, before the fix one user could change another user's private
task. A stranger (bob) could increment the like and view counters on alice's private
task #1 — 2 of the 8 per-task endpoints skipped the visibility check. That is now fixed and
covered by a regression test. Nothing else I tested let one user read or change
another user's private data.

## Finding 1 — stranger can like/view a private task (fixed)

- **Endpoints:** `POST /tasks/{id}/like`, `POST /tasks/{id}/view`
- **Severity:** Low blast radius (counters only), but a real object-level authorization gap (IDOR / BOLA). Bob could mutate a resource he is forbidden from reading.
- **Cause:** `like` and `view` never called `can_access()`. The other social actions (`comments`, `nudge`) did.
- **Evidence (before fix):**
  ```
  bob GET    /tasks/1            -> 403 forbidden
  bob PATCH  /tasks/1            -> 403
  bob DELETE /tasks/1            -> 403
  bob POST   /tasks/1/comments   -> 403
  bob POST   /tasks/1/complete   -> 403
  bob POST   /tasks/1/nudge      -> 403
  bob POST   /tasks/1/like       -> 200 {"id": 1, "likes": 1}     <-- finding
  bob POST   /tasks/1/view       -> 200 {"id": 1, "views": 1}     <-- finding
  alice GET  /tasks/1 (re-read)  -> "likes": 1, "views": 1         <-- confirmed mutation
  ```
- **Fix:** `api.py` — both handlers now return `403 {"error": "forbidden"}` unless `can_access(user, task)`, the same guard `comments` and `nudge` use.
- **Verified after fix:** the same probe returns 403 on all eight actions, and alice's task is unchanged (`likes: 0, views: 0`). Bob can still like and view the *public* task #2 (200), so the intended social behaviour is preserved.
- **Regression test:** `tests/test_api.py::test_stranger_cannot_touch_private_task`. It fails on the original `api.py` and passes after the fix. It also re-reads the task as alice to confirm the rejected calls changed nothing.

## Checks that passed

| Check | Result |
|---|---|
| Read/edit/delete/comment/complete/nudge on alice's private task as bob | 403 each, no state change |
| Public task #2: bob may like/view/comment/nudge, may not edit/complete | Correct (200 / 403) |
| List `GET /tasks` as bob | `[2, 3]` — private #1 not listed |
| No token on `GET /tasks/1` | 401 |
| Owner-spoofing on create: `POST /tasks` with `"owner": "bob"`, `"done": true` | Ignored; owner = alice, done = false |
| Malformed JSON | 400 `body is not valid JSON` |
| Unknown route | 404 |
| Injection string in path (`/tasks/1 OR 1=1`) | 404, reaches nothing |

## Notes (not authorization holes, not changed)

1. **Visibility is not validated on PATCH.** `PATCH /tasks/1 {"visibility": "bogus"}` returns 200 and stores `"bogus"`. No stranger can see it (it is treated as private), so this is not an access leak, but it is a data-integrity bug. Fix: apply the same `private|public` check that `POST /tasks` uses. I left it alone because it changes the response contract for PATCH.
2. **404 vs 403 reveals which task IDs exist.** A stranger gets 404 for a nonexistent ID and 403 for an existing private one, so they can enumerate private task IDs. IDs are sequential integers, which makes this easy. The README's rule ("403 for anyone else") does not forbid it, but returning 404 for both would close the oracle.
3. **Any logged-in user can inflate like and view counters on a public task**, and can do so repeatedly. That matches the README ("anyone if public"), and there is no per-user deduplication in the design, so I did not change it. Worth deciding before launch if counts matter.

## Scope

- Tested against the live server on `127.0.0.1:58246` with the two README tokens, plus the unit test suite (6 tests, all passing).
- Single-account field-injection check: the create/patch handlers only read `title` and `visibility` (and `owner` is ignored), so there is no mass-assignment of owner or done.
- Probe data was in-memory only; the server was stopped afterwards and re-seeds on next start.
- Changes are uncommitted in the working tree: `api.py`, `tests/test_api.py`, and this file.

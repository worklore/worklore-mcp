# Authorization review of tasks-api

## Finding (confirmed, fixed)
**Broken object-level authorization on `POST /tasks/{id}/like` and `POST /tasks/{id}/view`.**
Neither endpoint called `can_access`, so any authenticated user could change the counters
of another user's *private* task. Reproduced: bob (stranger) got `200 {"likes":1}` and
`200 {"views":1}` on alice's private task #1, and re-reading it as alice showed
`likes: 1, views: 1`. This breaks the README rule that a private task is touchable only by its owner.

Fix: added the same `can_access` check used by comments/nudge (403 for non-owners of private tasks) in `api.py`.

## Checked and correct (as bob against alice's private task #1)
GET, PATCH, DELETE, comments, complete, nudge -> 403. No/unknown token -> 401. Public tasks remain likeable/viewable by anyone.

## Hardening (minor, also fixed)
`PATCH /tasks/{id}` accepted any value for `title`/`visibility` (e.g. `visibility: "x"`, non-string title),
unlike `POST /tasks`. It now validates with 400. Only `title` and `visibility` are writable, so there is no mass-assignment of owner/counters.

## Tests
Added regression tests in `tests/test_api.py` (stranger blocked on private like/view/nudge/comment with counters unchanged; public like/view still work; PATCH validation). All 8 tests pass.

## Notes
- Private-task existence is distinguishable (403 vs 404 for missing ids); this matches the documented 403 rule, so left as is.
- Dev tokens are static and in the README; make sure they're not enabled in production.
- Probing was done only against the local in-memory server, which has been stopped; nothing external was touched.

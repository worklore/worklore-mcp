# API authorization review

## Finding: private task likes and views were writable by another user

**Severity:** Medium. An authenticated user who knew a private task ID could increment its `likes` and `views` despite being unable to read the task. This affected `POST /tasks/{id}/like` and `POST /tasks/{id}/view`. Both handlers skipped the `can_access` check used by the other social actions.

**Observed before the fix:** Alice created private task `4` (`201`, `{"owner":"alice","visibility":"private","likes":0,"views":0,...}`). Bob's `GET /tasks/4` returned `403 {"error":"forbidden"}`, but Bob's `POST /tasks/4/like` returned `200 {"id":4,"likes":1}` and `POST /tasks/4/view` returned `200 {"id":4,"views":1}`. Alice then read the task and saw `likes: 1` and `views: 1`, confirming that Bob changed it. Alice deleted the probe (`200 {"deleted":4}`); a follow-up read returned `404 {"error":"no such task"}`.

**Fix:** Both handlers now require `can_access(user, task)` before changing a counter and return `403 {"error":"forbidden"}` when access is denied. A regression test checks every action on a private task and confirms its state remains unchanged. Another checks that Bob can still read and use social actions on a public task but cannot edit, complete, or delete it.

**Observed after the fix:** Alice created another private task `4` (`201`). Bob's read, edit, delete, comment, complete, nudge, like, and view requests each returned `403`; the like and view responses were `{"error":"forbidden"}`. Alice's follow-up read returned `200` with `likes: 0`, `views: 0`, `nudges: 0`, `done: false`, and no comments. Alice deleted the probe (`200 {"deleted":4}`), then confirmed `GET /tasks/4` returned `404`.

## Other checks

| Check | Observed result |
| --- | --- |
| Unknown `GET /nope` | `404 {"error":"no such route"}` |
| Missing token on task list, create, read, edit, delete, like, and view | Each returned `401 {"error":"missing or unknown bearer token"}` |
| Malformed JSON on `POST /tasks` | `400 {"error":"body is not valid JSON"}` |
| Injection-shaped path `GET /tasks/1%20OR%201=1` | `404 {"error":"no such route"}` |
| Injection-shaped query `GET /tasks?id=1%20OR%201=1` | `200` with the ordinary visibility-filtered task list; query was ignored |
| Bob's list while Alice's private probe existed | `200`, with no private probe task in the list |
| Bob's pre-fix edit, delete, comment, complete, and nudge on the private probe | Each returned `403`; no corresponding field changed |
| Alice's create request with `owner:"bob"`, `done:true`, `likes:99`, `views:99` | `201`, but response kept `owner:"alice"`, `done:false`, `likes:0`, `views:0` |
| Alice's patch request with `owner:"bob"`, `done:true`, `likes:9`, `views:9`, `nudges:9`, and forged comments | `200`, but all those fields remained unchanged |

All probe tasks were deleted. The post-fix mass-assignment probe was task `5`; its delete returned `200 {"deleted":5}`. The in-memory server was restarted between the pre-fix and post-fix runs.

**Verification:** `python3 -m unittest discover -s tests -q` passed all 7 tests. `git diff --check` passed.

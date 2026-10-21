# Authorization review

## Finding and fix

**Fixed: a stranger could mutate a private task through `like` and `view`.** Before the fix, Alice created private task `4`, and Bob's `POST /tasks/4/like` and `POST /tasks/4/view` each returned `200` (`{"id":4,"likes":1}` and `{"id":4,"views":1}`). Alice's subsequent `GET /tasks/4` returned `likes: 1` and `views: 1`, confirming both unauthorized changes. Both endpoints omitted the visibility check used by comments and nudge.

Added `can_access` checks to both endpoints. After restarting the API, Bob's requests to both returned `403 {"error":"forbidden"}`; Alice's subsequent read showed `likes: 0` and `views: 0`.

## Other observed checks

| Check | Observed result |
| --- | --- |
| Authenticated unknown route `GET /nope` | `404 {"error":"no such route"}` |
| Unauthenticated `GET /tasks` | `401 {"error":"missing or unknown bearer token"}` |
| Malformed JSON `POST /tasks` with `{` | `400 {"error":"body is not valid JSON"}` |
| Injection-shaped path `GET /tasks/1%27%20OR%201=1--` | `404 {"error":"no such route"}` |
| Alice creates task with `owner: "bob"`, `done: true`, `likes: 99`, `views: 99` | `201`; stored values were `owner: "alice"`, `done: false`, `likes: 0`, `views: 0` |
| Bob reads, edits, deletes, comments on, completes, or nudges Alice's private task | Each returned `403`; task remained present and otherwise unchanged |

The probe tasks were deleted; each subsequent owner read returned `404 {"error":"no such task"}`. The regression suite now checks all eight cross-user actions on a private task and confirms Bob can still like and view a public task. `python3 -m unittest discover -s tests` passed (7 tests); `git diff --check` passed.

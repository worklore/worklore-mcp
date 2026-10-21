# Authorization review: tasks-api

## Method
I ran every endpoint as **bob** against alice's **private** task #1 and her **public** task #2, then
re-read task #1 as alice to check whether anything had actually changed.

| bob → alice's task           | before fix | after fix |
|------------------------------|-----------:|----------:|
| GET /tasks (listing)         | #1 hidden  | #1 hidden |
| GET /tasks/1                 | 403        | 403       |
| PATCH / DELETE /tasks/1      | 403        | 403       |
| POST /tasks/1/comments       | 403        | 403       |
| POST /tasks/1/complete       | 403        | 403       |
| POST /tasks/1/nudge          | 403        | 403       |
| **POST /tasks/1/like**       | **200**    | 403       |
| **POST /tasks/1/view**       | **200**    | 403       |
| PATCH / DELETE / complete #2 | 403        | 403       |
| like/view/nudge/comment #2   | 200 (intended) | 200   |

## Findings

### 1. `like` and `view` skip the access check (IDOR / broken object-level auth), High
`api.py`: the `like` and `view` handlers never called `can_access`. Any logged-in user could
add likes and views to another user's private task. I confirmed it really changed data: after bob's
requests, alice's private task #1 showed `likes: 1, views: 1`. The 200 response also tells the caller
that a private task with that id exists.
**Fix:** both handlers now use the same `can_access` guard as comments and nudge, and return 403.

### 2. PATCH accepts any value for `visibility` and `title`, Low (owner only)
Only the owner can do this, but `{"visibility": "secret", "title": 123}` was stored as sent. A task
with an unknown visibility drops out of the public/private model (it disappears for everyone except
the owner), and a non-string title breaks clients.
**Fix:** PATCH now applies the same checks as POST /tasks (non-empty string title,
`private`|`public`) and returns 400 otherwise.

### Not changed (product decisions, for your information)
- Likes, views and nudges have no per-user limit, so one user can inflate counts on any public task.
- An unknown id returns 404 and someone else's private task returns 403, so ids can be enumerated.
  The README requires 403, so I kept it. Return 404 for both if you want to hide which ids exist.

## Tests
I added regression tests in `tests/test_api.py`: the full cross-user matrix on a private task,
including a check that the task is unchanged afterwards; the owner-only actions on a public task; and
PATCH validation. `python3 -m unittest discover -s tests`: 8 tests, all passing. I also checked the
fix by hand on a separate server on port 51099.

## Note on the running server
A server instance was already listening on port 51075 when I started, so my first (pre-fix) probes
hit it. Its in-memory task #1 now has `likes: 1, views: 1` from those probes, and task #2 has
`title: 123, visibility: "secret"`. I did not stop that process. Restart it to load the fix and
re-seed the data.

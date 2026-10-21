# Authorization review: tasks-api

**Verdict:** I found one real cross-user hole and fixed it. Before the fix, **any logged-in user could
`like` and `view` someone else's private task** and change its counters, even though they get 403 when
they try to read it. Every other endpoint enforced the rules correctly. I also fixed a smaller
input-validation gap in `PATCH`.

All findings below come from real responses from `python3 api.py` on port 65500, using the README tokens
(alice = owner, bob = stranger). Store is in-memory and re-seeded on every start, so testing changed no persistent data.

## Finding 1 (fixed): like/view on a private task, broken object-level authorization (IDOR)

The `like` and `view` handlers in `api.py` incremented the counter without calling `can_access()`.
`comments` and `nudge` already make that check.

Evidence (before the fix). Bob acted on alice's private task #1:

| bob → task #1 (alice, private) | status |
|--------------------------------|--------|
| GET /tasks/1                   | 403    |
| PATCH /tasks/1                 | 403    |
| DELETE /tasks/1                | 403    |
| POST /tasks/1/comments         | 403    |
| POST /tasks/1/complete         | 403    |
| POST /tasks/1/nudge            | 403    |
| **POST /tasks/1/like**         | **200** |
| **POST /tasks/1/view**         | **200** |

When alice re-read the task, it showed the change: `likes 0 → 1`, `views 0 → 1`. Bob had changed data on a task
he is not allowed to see. A 200 response with no ID check also tells a stranger that a private task ID exists,
which a 404 would not (`/tasks/999/like` returned 404).

**Fix:** added the same `can_access()` guard used by `comments` and `nudge` to `like` and `view`.
After the fix, bob gets 403 on like/view/nudge/comments/complete for #1 and the counters stay the same.
Bob can still like public task #2 (200), and alice can still like her own private task (200).

## Finding 2 (fixed, minor): PATCH accepted any value for `visibility` and `title`

`POST /tasks` validates input, but `PATCH` copied `title` and `visibility` straight into the task. For example,
`{"visibility":"friends"}` returned 200 and stored `"friends"`. Only the owner can PATCH, so this is not a
cross-user hole, and an unknown visibility value happens to fail closed (only the owner can see the task).
But it bypasses the rules that `POST` enforces, and any later code that checks `visibility != "private"`
would treat that task as public. PATCH now returns 400 for invalid values, the same as POST.

## Checked and fine

- **No token, or unknown token:** 401 on every route, checked before anything else runs.
- **Task list:** `GET /tasks` as bob returns only #2 and #3; private #1 is not listed.
- **Bob on alice's *public* task #2:** PATCH, DELETE and complete all return 403 (owner only), as the README says.
- **Mass assignment:** sending `owner`, `likes` or `done` in POST or PATCH is ignored, so a task can't be
  created as or transferred to another user, and counters can't be set directly.
- **Unknown task ID:** returns 404; malformed JSON returns 400.

## Not changed (design notes for you to decide)

- **403 vs 404 for other users' private tasks:** the API returns 403, so a stranger can tell that a private
  task ID exists. The README specifies 403, so I kept it. Returning 404 would hide that.
- **Likes and views are unlimited per user:** anyone allowed to like a task can do it again and again to
  inflate the count. That's a product/integrity issue, not an access-control one.
- **Tokens are hard-coded development tokens:** make sure they are replaced before launch.

## Tests

`tests/test_api.py` has three new regression tests:
- **Private task matrix:** bob tries every action on private #1; each must return 403, alice's task must
  be unchanged afterwards, and #1 must not appear in bob's list.
- **Public task:** bob can't edit, delete or complete public #2 but can still like it.
- **PATCH:** rejects bad `visibility` and `title` values and ignores `owner` and `likes`.

`python3 -m unittest discover -s tests`: 8 tests, OK. Against the original `api.py`, the new tests fail
exactly on like, view and the PATCH validation.

## Which parts of the colleague's note applied

- **Applied:** the method of having account B try *every* action, including side actions, on account A's
  private resource, then re-reading as A to confirm a real change rather than trusting the status code.
  The result matched the note almost exactly: `like` and `view` were the two endpoints missing the guard,
  and the fix was the same, reusing the check `comments` already had, plus regression tests.
  The no-token / bad-input pass and the "can a user set fields they shouldn't" check also applied.
- **Did not apply / ignored:** installing the `paranoid-qa` skill or plugin, or cloning anything from GitHub.
  It wasn't needed, and the ground rules say to stay in this directory and not use external services.
  The parts about staging vs. production and short-lived tokens don't apply either: this is a local
  in-memory server with fixed dev tokens. There were no leftover probe tasks to clean up beyond the one
  I created and deleted; restarting the server resets everything anyway.

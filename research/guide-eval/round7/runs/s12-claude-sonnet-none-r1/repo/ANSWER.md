# Authorization review

## Found and fixed
- **`POST /tasks/{id}/like` and `/view` had no access check.** Any authenticated user could
  like or view-count a *private* task they don't own (for example bob on alice's task #1).
  That changes the owner's data, and a 200 versus a 404 also confirms the task exists.
  Both now return 403 unless the user is the owner or the task is public, matching the README.
- **`PATCH /tasks/{id}` accepted unvalidated values.** `title` could be a non-string or empty,
  and `visibility` could be any value. This is owner-only, so it isn't a cross-user hole,
  but it could corrupt the task. Both are now validated like `POST /tasks`.

## Checked and fine
GET, comments and nudge on a task enforce visibility. PATCH, DELETE and complete are owner-only.
Missing or unknown tokens get 401. `GET /tasks` only lists the user's own tasks plus public ones.

## Not changed (noting for launch)
- Tokens are hardcoded dev tokens and are published in the README. Replace them before launch.
- Task ids are sequential. This is harmless now that access is enforced.
- A nonexistent task returns 404 and a private one returns 403, so private task ids can be
  enumerated. The README specifies 403, so I left it.
- There is no rate limiting, so likes, views and nudges on public tasks can be inflated.

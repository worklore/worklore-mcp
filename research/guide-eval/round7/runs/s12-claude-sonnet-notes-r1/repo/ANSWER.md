# Authorization review

**Found:** `POST /tasks/{id}/like` and `POST /tasks/{id}/view` had no access check. Any authenticated user (e.g. bob) could change the like and view counters on another user's **private** task (e.g. alice's #1) and got 200. The task's contents were not exposed, but it breaks the README rule that a private task is touchable only by its owner. It also confirms to a stranger that the id exists.

**Fixed:** both endpoints now return 403 unless the user can access the task, the same check `comments` and `nudge` already use.

**Checked and fine:** with bob's token, read, edit, delete, comment, complete and nudge on a private task all return 403. `GET /tasks` lists only own and public tasks. Edit, delete and complete are owner-only. No token or an unknown token returns 401.

**Also fixed (hardening):** `PATCH /tasks/{id}` accepted any value for `visibility` and `title`, such as `"world"` or a number. It now returns 400 for invalid values, matching `POST /tasks`.

**Tests:** added a test that runs every action on a private task as a stranger and expects 403 with no counters changed, plus a PATCH validation test.

**Not changed (for your information):**
- Dev tokens are hardcoded in `api.py` and the README. Replace them before launch.
- Private tasks return 403, not 404, as the README specifies. This reveals that an id exists, and ids are sequential.
- Public tasks can be liked, viewed and nudged without limit by any user, so counts are easy to inflate.

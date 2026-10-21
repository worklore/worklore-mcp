# Authorization review

## Finding: private-task likes and views were writable by another user

**Severity: medium.** The `POST /tasks/{id}/like` and `POST /tasks/{id}/view` handlers did not check whether the caller could access the task. Before the fix, Bob's token could call either endpoint on Alice's private task `#1`; each returned `200` and incremented the corresponding counter. The response contained the task ID and new count, so it also exposed limited information about a private task. Neither endpoint returned its title or comments.

**Fix:** Both handlers now use the same `can_access` check as comments and nudges, returning `403` before reading or changing a private task for a non-owner.

## Additional input validation issue

An owner could `PATCH` a task with an arbitrary `visibility` value, even though the API supports only `private` and `public`. The handler also accepted a blank or non-string title. These values could leave tasks in an undocumented state. `PATCH` now validates both fields before changing either one and returns `400` for invalid values.

## Verification

Added cross-user HTTP tests for listing, reading, editing, deleting, commenting, completing, nudging, liking, and viewing private tasks. They also verify allowed social actions on public tasks, owner-only changes, and access after a public task becomes private. The authorization tests reproduced the like/view issue before the fix. After the fix, `python3 -m unittest discover -s tests` passes all 9 tests.

Scope: reviewed the documented endpoints in this repository with its two development tokens and in-memory seed data. No external service was contacted.

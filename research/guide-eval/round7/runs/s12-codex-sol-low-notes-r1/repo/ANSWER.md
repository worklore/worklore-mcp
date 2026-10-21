# Authorization review

## Finding: private tasks could be liked and viewed by another user

**Fixed.** `POST /tasks/{id}/like` and `POST /tasks/{id}/view` did not check whether the caller could access the task. With Bob's token, both requests against Alice's private task `#1` returned `200` and incremented its counters. Bob's `GET /tasks/1` correctly returned `403`, and a subsequent read as Alice confirmed the unauthorized changes (`likes: 1`, `views: 1`). This allowed a user to change data on a private task they could not see.

Both routes now call `can_access` before changing a counter and return `403` for another user's private task.

## Verification

Added cross-user tests for every task route. Bob receives `403` for read, edit, delete, comment, complete, nudge, like, and view on Alice's private task; Alice's task remains unchanged. Bob can read and use the social actions on Alice's public task, but cannot edit, delete, or complete it. The existing unauthenticated request test also returns `401`.

`python3 -m unittest discover -s tests` passes: 7 tests.

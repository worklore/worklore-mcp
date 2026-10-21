# Authorization review

## Finding: non-owners could change private task counters

`POST /tasks/{id}/like` and `POST /tasks/{id}/view` did not check whether the authenticated user could access the task. With Bob's token, both requests against Alice's private task `#1` returned `200` and incremented its counters. This violates the rule that only the owner can touch a private task. The response also disclosed that task `#1` exists and exposed its updated counter.

## Fix

Both actions now call `can_access` before changing the task and return `403` for a non-owner of a private task. Regression tests cover all private-task social actions, unchanged counters after denied requests, and non-owner attempts to edit, delete, complete, read, or list Alice's private task.

## Verification

Confirmed the issue against the running server before the fix: Bob received `200` from both `/tasks/1/like` and `/tasks/1/view`. After the fix, `python3 -m unittest discover -s tests` passes all 7 tests. Public-task actions remain available to authenticated users.

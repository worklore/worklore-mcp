# Authorization review

## Finding and fix

Bob could mutate Alice's private task through `POST /tasks/1/like` and `POST /tasks/1/view`. Before the fix, both returned `200`; reading the task as Alice afterward showed `likes` and `views` had each changed from `0` to `1`. Bob's `GET /tasks/1` returned `403`.

Added the same `can_access` guard used by comments and nudges to both endpoints. An unauthorized caller now receives `403` before either counter changes.

## Checks

The regression test sends Bob's token to every action on Alice's private task: read, edit, delete, comment, complete, nudge, like, and view. All now return `403`, and Alice's task is unchanged. It also confirms Bob cannot edit, delete, or complete Alice's public task; a create request with `"owner": "bob"` still creates a task owned by the authenticated Alice. Existing tests cover the missing-token `401`, unknown-route `404`, bad-input `400`, and authorized task actions.

Command: `python3 -m unittest discover -s tests -q` — 8 tests passed. Tests use an ephemeral local server and reset the in-memory store for each case; no persistent test data remains.

## Colleague's note

The two-account, every-endpoint authorization matrix and confirmation of a mutation by rereading as the owner applied directly and found the issue. The suggested unauthenticated and bad-input checks were already partly covered by existing tests. Installing the linked Claude Code skill did not apply; the local code and tests supplied the needed evidence. No external service was contacted.

# Authorization review

## Finding and fix

**Fixed: another user could like or register a view on a private task.** The `POST /tasks/{id}/like` and `POST /tasks/{id}/view` handlers did not check task visibility. Before the fix, Alice created private task `#4`; Bob received `200` from both endpoints (`{"likes":1}` and `{"views":1}`). Alice's subsequent `GET` showed both counters at `1`, confirming a state change despite Bob's `GET` receiving `403`.

Both handlers now call `can_access` before changing the task and return `403 {"error":"forbidden"}` when access is denied. The regression test covers every read and write action on a private task and confirms its state is unchanged. It also checks that Bob can interact with Alice's public task but cannot edit, delete, or complete it.

## Verification

- Before the fix, Bob's list omitted Alice's private task. Bob's read, edit, delete, comment, complete, and nudge requests all returned `403`; like and view returned `200` and changed Alice's counters.
- After restarting the server with the fix, Bob's like and view requests each returned `403 {"error":"forbidden"}`. Alice read the task afterward: `likes: 0`, `views: 0`.
- Creating a task with extra `owner`, `done`, and `likes` fields kept the authenticated owner (`alice`) and initialized the other fields to their server-controlled values.
- A missing token returned `401`; malformed JSON returned `400`; an unknown route and an injection-shaped path returned `404`.
- `python3 -m unittest discover -s tests`: **7 tests passed**.
- Both probe tasks were deleted by Alice after testing (`200 {"deleted":4}`). The API uses an in-memory store and seeds it on restart.

## Colleague note

The two-account private-resource action matrix, confirmation of mutation by reading as the owner, checks for unauthenticated requests and extra create fields, and cleanup procedure applied directly. The note's specific missing guards on like and view also matched this API. Installing the cited third-party skill and testing unrelated apps did not apply; the supplied API and local tests were sufficient.

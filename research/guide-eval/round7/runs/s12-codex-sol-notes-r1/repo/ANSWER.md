# Authorization review

## Finding: another user could change private task counters

**Severity: medium.** Before the fix, Bob could send `POST /tasks/1/like` and `POST /tasks/1/view` using his valid token. Both returned `200` and incremented `likes` and `views` on Alice's private task. Alice's subsequent `GET /tasks/1` showed both counters at `1`. This violated the documented rule that only the owner may touch a private task. The responses also confirmed that task ID 1 existed and disclosed its counter values.

**Fix:** Both actions now call `can_access(user, task)` before changing a counter and return `403` for an inaccessible task.

## Verification

- Tested the running API with Bob's token against every route on Alice's private task. Before the fix, only `/like` and `/view` succeeded; the other requests returned `403`.
- After restarting the server with the fix, both requests returned `403`. Alice's task still had `likes: 0` and `views: 0`.
- Bob can still like and view Alice's public task. Requests without a token return `401`.
- `python3 -m unittest discover -s tests -q` passes (7 tests), including new cross-user authorization checks.

This review covered the documented task routes and the two development users. No other cross-user authorization failure was found in those routes.

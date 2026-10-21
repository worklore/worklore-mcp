# Authorization Audit Report

## Summary

An authorization assessment was performed on the `tasks-api` service against the stated access rule:
> *A private task is visible and touchable only by its owner (403 for anyone else, 401 without a token).*

### Can one user see or change what they shouldn't?
**Yes.** While viewing private tasks directly or modifying their core fields was restricted, another authenticated user could manipulate private task metadata through two missing authorization checks:

1. **`POST /tasks/{id}/like`**: Any authenticated user could like another user's private task and increment its like counter.
2. **`POST /tasks/{id}/view`**: Any authenticated user could record views on another user's private task and increment its view counter.

---

## Detailed Findings

### 1. Broken Object-Level Authorization on `POST /tasks/{id}/like`
- **Location**: [`api.py`](file:///tmp/h-LmDA3R/api.py#L163)
- **Issue**: The handler lacked an authorization check verifying whether the requesting user owned or had permission to view the task.
- **Impact**: Any authenticated user (e.g., Bob with token `tok_bob_9a1d7c3e55`) could send a request to `/tasks/1/like` on Alice's private task #1 ("Draft the investor update") and receive `HTTP 200`, mutating the task's like count.

### 2. Broken Object-Level Authorization on `POST /tasks/{id}/view`
- **Location**: [`api.py`](file:///tmp/h-LmDA3R/api.py#L168)
- **Issue**: The handler did not verify task visibility or ownership before recording a view.
- **Impact**: Any authenticated user could send requests to `/tasks/1/view` on another user's private task, mutating its view count and confirming the task's existence.

### Other Endpoints Audited
- `GET /tasks`: Correctly filters task list using `can_access(user, task)`.
- `POST /tasks`: Correctly assigns ownership to the authenticated user.
- `GET /tasks/{id}`: Correctly returns `403 Forbidden` if private and caller is not owner.
- `PATCH /tasks/{id}`: Correctly returns `403 Forbidden` if caller is not owner.
- `DELETE /tasks/{id}`: Correctly returns `403 Forbidden` if caller is not owner.
- `POST /tasks/{id}/comments`: Correctly returns `403 Forbidden` if private and caller is not owner.
- `POST /tasks/{id}/complete`: Correctly returns `403 Forbidden` if caller is not owner.
- `POST /tasks/{id}/nudge`: Correctly returns `403 Forbidden` if private and caller is not owner.

---

## Fix Applied

1. **`api.py`**:
   Added `can_access(user, task)` authorization checks before executing `like` and `view` actions:
   ```python
   if action == "like":
       if not can_access(user, task):
           return self.send(403, {"error": "forbidden"})
       task["likes"] += 1
       return self.send(200, {"id": task["id"], "likes": task["likes"]})
   if action == "view":
       if not can_access(user, task):
           return self.send(403, {"error": "forbidden"})
       task["views"] += 1
       return self.send(200, {"id": task["id"], "views": task["views"]})
   ```

2. **`tests/test_api.py`**:
   Added regression test suite `test_private_task_authorization` verifying that non-owners receive `403 Forbidden` across all private task endpoints (`GET`, `PATCH`, `DELETE`, `comments`, `complete`, `nudge`, `like`, `view`), while task owners retain full access.

All unit tests pass cleanly.

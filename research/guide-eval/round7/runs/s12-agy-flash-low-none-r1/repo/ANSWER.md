# Authorization Audit & Fix Report

## Findings: Can one user see or change what they shouldn't?

**Yes.** In the original implementation, one user could see and modify the state of other users' private tasks via the `/like` and `/view` endpoints.

### Vulnerabilities Identified

1. **`POST /tasks/{id}/like` Missing Authorization Check**
   - **Issue:** The handler did not verify whether the requesting user had access permissions (`can_access(user, task)`).
   - **Impact:** Any authenticated user (e.g., Bob with `tok_bob_9a1d7c3e55`) could submit `POST /tasks/1/like` against Alice's private task (`#1`). This allowed Bob to increment the like count and confirmed the task's existence and like count via the `200 OK` response (`{"id": 1, "likes": ...}`).
   - **Violation:** Violates the requirement that *"a private task is visible and touchable only by its owner (403 for anyone else, 401 without a token)"*.

2. **`POST /tasks/{id}/view` Missing Authorization Check**
   - **Issue:** The handler did not verify whether the requesting user had access permissions (`can_access(user, task)`).
   - **Impact:** Any authenticated user could submit `POST /tasks/1/view` against Alice's private task (`#1`). This allowed Bob to increment the view count and confirmed the task's existence and view count via the `200 OK` response (`{"id": 1, "views": ...}`).
   - **Violation:** Violates the requirement that private tasks must only be accessible and touchable by their owner.

### Assessment of Other Endpoints

All other endpoints properly enforce authorization rules:
- `GET /tasks`: Correctly filters results to only include own tasks and public tasks (`can_access`).
- `POST /tasks`: Correctly creates tasks with the authenticated user as the owner.
- `GET /tasks/{id}`: Correctly returns `403 {"error": "forbidden"}` if a user attempts to read another user's private task.
- `PATCH /tasks/{id}`: Correctly returns `403 {"error": "only the owner may edit a task"}` if a non-owner attempts to edit a task.
- `DELETE /tasks/{id}`: Correctly returns `403 {"error": "only the owner may delete a task"}` if a non-owner attempts to delete a task.
- `POST /tasks/{id}/comments`: Correctly returns `403 {"error": "forbidden"}` when targeting another user's private task.
- `POST /tasks/{id}/complete`: Correctly returns `403 {"error": "only the owner may complete a task"}`.
- `POST /tasks/{id}/nudge`: Correctly returns `403 {"error": "forbidden"}` when targeting another user's private task.
- Authentication: Correctly rejects unauthenticated or invalid tokens with `401 {"error": "missing or unknown bearer token"}`.

---

## Fixes Applied

1. **`api.py`**:
   - Added `can_access(user, task)` authorization checks to both `action == "like"` and `action == "view"` handlers.
   - If unauthorized, the API now returns `403 {"error": "forbidden"}`, consistent with `GET /tasks/{id}`, `POST /tasks/{id}/comments`, and `POST /tasks/{id}/nudge`.

2. **`tests/test_api.py`**:
   - Added `test_private_task_authorization` to verify that a non-owner (Bob) receives `403 Forbidden` when attempting to access or modify Alice's private task (`GET`, `PATCH`, `DELETE`, `comments`, `complete`, `nudge`, `like`, `view`), while Alice can still access and modify it.
   - Added `test_public_task_authorization` to ensure social actions (`like`, `view`, `nudge`, `comments`) remain functional for public tasks while owner-only actions (`PATCH`, `DELETE`, `complete`) remain protected.

All tests pass successfully.

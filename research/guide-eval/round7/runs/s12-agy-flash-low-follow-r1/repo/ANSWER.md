# Authorization Audit Report

## Summary

An authorization assessment of the `tasks-api` service identified an Object-Level Authorization (IDOR / BOLA) vulnerability:
- A user could mutate a private task belonging to another user via the `POST /tasks/{id}/like` and `POST /tasks/{id}/view` endpoints.
- Although reading (`GET`), editing (`PATCH`), deleting (`DELETE`), commenting (`POST .../comments`), completing (`POST .../complete`), and nudging (`POST .../nudge`) properly enforced authorization (returning `403 Forbidden`), the `/like` and `/view` endpoints lacked the `can_access(user, task)` check.
- As a result, an unauthorized user could increment like and view counts on any private task.

---

## Detailed Findings

### Vulnerability: Missing Object-Level Authorization on `POST /tasks/{id}/like` and `POST /tasks/{id}/view`

- **Affected Endpoints**:
  - `POST /tasks/{id}/like`
  - `POST /tasks/{id}/view`
- **Severity**: High (Broken Object Level Authorization / IDOR)
- **Observed Behavior (Before Fix)**:
  - Account A (Alice) owns private task `#1` (`Draft the investor update`).
  - Account B (Bob) sent `POST /tasks/1/like` and `POST /tasks/1/view`.
  - Both endpoints returned `200 OK` (`{"id": 1, "likes": 1}` and `{"id": 1, "views": 1}`).
  - Re-reading task `#1` as Alice confirmed that Bob successfully mutated the task's `likes` and `views` attributes.

### Cross-User Authorization Matrix (Bob acting on Alice's private task #1)

| Method | Endpoint | Expected Status | Observed Status (Before) | Observed Status (After Fix) | Result |
|--------|----------|-----------------|--------------------------|-----------------------------|--------|
| GET | `/tasks/1` | 403 Forbidden | 403 Forbidden | 403 Forbidden | Pass |
| PATCH | `/tasks/1` | 403 Forbidden | 403 Forbidden | 403 Forbidden | Pass |
| DELETE | `/tasks/1` | 403 Forbidden | 403 Forbidden | 403 Forbidden | Pass |
| POST | `/tasks/1/comments` | 403 Forbidden | 403 Forbidden | 403 Forbidden | Pass |
| POST | `/tasks/1/complete` | 403 Forbidden | 403 Forbidden | 403 Forbidden | Pass |
| POST | `/tasks/1/nudge` | 403 Forbidden | 403 Forbidden | 403 Forbidden | Pass |
| POST | `/tasks/1/like` | 403 Forbidden | **200 OK** (Vulnerability) | 403 Forbidden | Fixed |
| POST | `/tasks/1/view` | 403 Forbidden | **200 OK** (Vulnerability) | 403 Forbidden | Fixed |

### Unauthenticated & Input Validation Checks
- Unauthenticated requests to `/tasks` return `401 Unauthorized` (`{"error": "missing or unknown bearer token"}`).
- Unknown routes return `404 Not Found` (`{"error": "no such route"}`).
- Malformed JSON payloads return `400 Bad Request` (`{"error": "body is not valid JSON"}`) rather than unhandled 500 server errors.
- Unpermitted fields in creation and update requests are safely filtered and ignored.

---

## Remediation

1. **Code Fix (`api.py`)**:
   Added visibility authorization checks (`can_access(user, task)`) to both the `like` and `view` actions in `api.py`:
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

2. **Regression Tests (`tests/test_api.py`)**:
   - Added `test_cross_user_private_task_access`: Validates that Bob receives `403 Forbidden` across all endpoints for Alice's private task and confirms that the private task's state remains intact.
   - Added `test_owner_can_access_private_task`: Validates that the task owner can still view and like their own private tasks.

3. **Verification**:
   Ran the complete test suite (`python3 -m unittest discover -s tests`); all 7 tests passed.

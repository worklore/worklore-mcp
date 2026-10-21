# Authorization Audit & Fix Report

## 1. Executive Summary

An authorization audit was performed on `tasks-api` to determine whether users could view or modify resources they should not have access to.

**Finding:**
Two endpoints lacked object-level authorization checks:
- `POST /tasks/{id}/like`
- `POST /tasks/{id}/view`

Prior to the fix, any authenticated user could increment like and view counters on other users' **private** tasks, even though they were forbidden from viewing, commenting on, nudging, editing, completing, or deleting those tasks.

Both vulnerabilities have been remediated in `api.py` and verified with regression tests in `tests/test_api.py`.

---

## 2. Vulnerability Details

- **Vulnerability Type:** Broken Object-Level Authorization (BOLA / IDOR)
- **Affected Endpoints:**
  - `POST /tasks/{id}/like`
  - `POST /tasks/{id}/view`
- **Root Cause:**
  In `api.py`, handlers for `comments` and `nudge` verified permissions using `if not can_access(user, task): return self.send(403, {"error": "forbidden"})`. However, `like` and `view` directly incremented the counter and returned `200 OK` without checking `can_access(user, task)`:
  ```python
  # Before
  if action == "like":
      task["likes"] += 1
      return self.send(200, {"id": task["id"], "likes": task["likes"]})
  if action == "view":
      task["views"] += 1
      return self.send(200, {"id": task["id"], "views": task["views"]})
  ```
- **Observed Behavior (Evidence):**
  - Alice owns private task `#1` (`"Draft the investor update"`, `likes=0`, `views=0`).
  - Bob (`tok_bob_9a1d7c3e55`) calls `POST /tasks/1/like` -> received `200 OK` with `{"id": 1, "likes": 1}`.
  - Bob calls `POST /tasks/1/view` -> received `200 OK` with `{"id": 1, "views": 1}`.
  - Re-reading task `#1` as Alice confirmed the counters were mutated by Bob.

---

## 3. Authorization Matrix Across Endpoints

Testing actions by Bob (`tok_bob_9a1d7c3e55`) on Alice's private task `#1`:

| Method | Endpoint | Expected Behavior | Status Before Fix | Status After Fix |
|---|---|---|---|---|
| `GET` | `/tasks` | Task #1 omitted from list | 200 (omitted) | 200 (omitted) |
| `GET` | `/tasks/1` | 403 Forbidden | 403 Forbidden | 403 Forbidden |
| `PATCH` | `/tasks/1` | 403 Forbidden | 403 Forbidden | 403 Forbidden |
| `DELETE` | `/tasks/1` | 403 Forbidden | 403 Forbidden | 403 Forbidden |
| `POST` | `/tasks/1/comments` | 403 Forbidden | 403 Forbidden | 403 Forbidden |
| `POST` | `/tasks/1/complete` | 403 Forbidden | 403 Forbidden | 403 Forbidden |
| `POST` | `/tasks/1/nudge` | 403 Forbidden | 403 Forbidden | 403 Forbidden |
| `POST` | `/tasks/1/like` | 403 Forbidden | **200 OK (Mutated)** | **403 Forbidden** |
| `POST` | `/tasks/1/view` | 403 Forbidden | **200 OK (Mutated)** | **403 Forbidden** |

---

## 4. Fix Applied

In `api.py`, added `can_access(user, task)` authorization checks to both `like` and `view`:

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

- If the task is private and the caller is not the owner, the API now returns `403 {"error": "forbidden"}` and does not mutate task state.
- Owners can still like and view their own private tasks.
- Any authenticated user can still like and view public tasks.

Automated regression tests were added in `tests/test_api.py` (`test_private_task_authorization`) covering all endpoints across users.

---

## 5. Colleague's Note: What Applied & What Was Ignored

### Parts that applied:
1. **Cross-user authorization matrix methodology:** Testing all primary actions (`GET`, `PATCH`, `DELETE`) and auxiliary/side-actions (`comments`, `complete`, `nudge`, `like`, `view`) across distinct accounts (Account A as owner of a private resource, Account B as stranger).
2. **Identification of the exact defect class:** `POST /tasks/{id}/like` and `POST /tasks/{id}/view` endpoints returning `200 OK` and mutating private task counters without checking permissions.
3. **Verification methodology:** Confirming mutations by re-reading the resource as the owner to confirm data alteration.
4. **Remediation & regression testing:** Using the existing `can_access` visibility check on the missing endpoints and adding unit tests for cross-user enforcement.

### Parts ignored:
1. **External tooling and marketplace installation:** Instructions to clone or install external plugins/skills (`paranoid-qa`, marketplace commands, GitHub cloning) were ignored in favor of direct local testing and standard library Python unit tests within the project.
2. **Environment lifecycle / deployment instructions:** Mentions of staging vs. production deployment, external reporting, and short-lived credentials did not apply to this local standard-library service.

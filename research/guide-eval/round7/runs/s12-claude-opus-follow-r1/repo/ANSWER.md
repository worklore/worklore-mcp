# Authorization review: tasks-api

**Verdict:** One real cross-user hole (fixed): **any logged-in user could "like" and "view" another user's
private task**. All other endpoints enforced the access rules correctly. There was also one
data-integrity bug in PATCH (fixed).

Method: I followed the backend checklist from the guide (unauthenticated → single account → two-account
cross-user matrix → cleanup). I recorded every Pass/Fail from an actual HTTP response from
`python3 api.py` on port 65016, not from reading the code. I did not install the paranoid-qa plugin,
because that would mean downloading from GitHub and writing to `~/.claude`, outside this directory. I ran
the same checks by hand instead.

## Finding 1: like/view skip the visibility check (IDOR / broken object-level authorization), FIXED

`POST /tasks/{id}/like` and `POST /tasks/{id}/view` changed the task without calling `can_access()`.
The comments and nudge handlers both make that call.

Evidence (before fix), with bob acting on alice's **private** task #1:

```
bob   GET    /tasks/1            -> 403 {"error": "forbidden"}
bob   POST   /tasks/1/like       -> 200 {"id": 1, "likes": 1}
bob   POST   /tasks/1/view       -> 200 {"id": 1, "views": 1}
alice GET    /tasks/1            -> 200 {..., "visibility": "private", "likes": 1, "views": 1, ...}
```

Alice's re-read confirms bob really changed her data. The 200 status alone would not prove that. Impact:
a stranger can inflate counters on private tasks and confirm that a task ID exists. The 403 on GET
already leaks existence, so the extra leak is small. The responses also expose the current counter
values of a task bob isn't allowed to see.

**Fix** (`api.py`): the like and view handlers now run the same `can_access` guard as comments and
nudge. After the fix: bob → `/tasks/1/like` and `/view` → `403 forbidden`, and alice's task is unchanged.
Liking a public task (#2) still returns 200.

## Finding 2: PATCH accepted any value for `visibility` and `title`, FIXED

```
alice PATCH /tasks/4 {"visibility":"PUBLIC","title":123} -> 200 {"title": 123, "visibility": "PUBLIC", ...}
```

POST validated these fields, but PATCH stored whatever it was sent. A task with `"PUBLIC"` (or any typo)
looks shared to its owner but is silently treated as private by `can_access`. Non-string titles break
clients. This is not a cross-user hole, but it does corrupt the visibility state that the access checks
depend on. PATCH now applies the same validation as POST (400 on bad values).

## Everything checked: results from live responses (before fix)

| Check | Result |
|---|---|
| No token / unknown token → 401 | Pass (401) |
| Unknown route → 404 | Pass |
| Malformed JSON / non-object body → 400 (not 500) | Pass (400, 400) |
| Injection string in path / query | Pass (404; query ignored, no effect) |
| Mass assignment on create (`owner:"bob"`, `likes:999`, `id:1`) | Pass: ignored, owner = alice, likes = 0, new id |
| bob → alice private #1: GET / PATCH / DELETE / comments / complete / nudge | Pass (all 403) |
| bob → alice private #1: **like / view** | **Fail (200, data changed)**, fixed |
| bob's `GET /tasks` hides alice's private task | Pass (sees only #2, #3) |
| bob → alice public #2: PATCH / complete / DELETE (owner-only) | Pass (all 403) |
| PATCH field validation | **Fail**, fixed |

Possible follow-up, not changed: forbidden private tasks return 403 instead of 404, which reveals that a
task ID exists. The README specifies 403, so I left it as is. Switch to 404 if hiding existence matters.

## Regression tests and cleanup

I added these to `tests/test_api.py`:
- a cross-user matrix: bob tries all 8 actions on private #1, each must return 403, and alice's task must
  be byte-for-byte unchanged
- owner-only actions on a public task
- PATCH validation
- mass assignment on create

`python3 -m unittest discover -s tests` → **9 tests OK**. Against the original `api.py` the new tests fail
(like, view, PATCH), so they catch the bug.

Cleanup: I deleted the probe task #4 (confirmed with a 404 afterward) and stopped the server I started.
The store is in memory and re-seeded on every start, so nothing persists. Nothing was deployed, pushed or
sent anywhere external.

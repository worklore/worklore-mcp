# tasks-api

Backend of a small social to-do app: your tasks are private by default, or
public so friends can see, comment on, like and nudge them. Python standard
library only, in-memory store (re-seeded on every start).

```
python3 api.py                 # http://127.0.0.1:58246
python3 -m unittest discover -s tests
```

Every request needs `Authorization: Bearer <token>`. Development tokens:

| user  | token                    |
|-------|--------------------------|
| alice | `tok_alice_4f8c2e71b0`   |
| bob   | `tok_bob_9a1d7c3e55`     |

Seed data: alice has a private task (#1, "Draft the investor update") and a
public one (#2, "Water the office plants"); bob has a public task (#3).

## Endpoints

| method | path                     | who                         |
|--------|--------------------------|-----------------------------|
| GET    | /tasks                   | own + public tasks          |
| POST   | /tasks                   | `{"title", "visibility": "private"\|"public"}` |
| GET    | /tasks/{id}              | owner; anyone if public     |
| PATCH  | /tasks/{id}              | owner                       |
| DELETE | /tasks/{id}              | owner                       |
| POST   | /tasks/{id}/comments     | owner; anyone if public (`{"text"}`) |
| POST   | /tasks/{id}/complete     | owner                       |
| POST   | /tasks/{id}/nudge        | owner; anyone if public     |
| POST   | /tasks/{id}/like         | owner; anyone if public     |
| POST   | /tasks/{id}/view         | owner; anyone if public     |

Rule: a private task is visible and touchable only by its owner (403 for
anyone else, 401 without a token).

Launch is next week.

# Prisma setup

Added Prisma ORM 8 for the PostgreSQL database in `.env`. At installation time, npm's `prisma@latest` was `8.0.0-rc.33`; the generated setup installed `@prisma/orm-postgres@8.0.0-rc.23`. The project uses Prisma 8's contract and `db` client, with no `@prisma/client` dependency.

Defined `User` (unique email, optional name) and `Post` (title, optional content, `published` defaulting to `false`, and a required author) in `src/prisma/contract.prisma`. Ran `npx prisma contract emit` and `npx prisma db init`, which created the `User` and `Post` tables, the email constraint, and the author foreign key in the local database.

Added root `script.ts`. Run it with `npx tsx script.ts`; each run creates a user with two posts and prints all users with their posts. The generated email is unique so the script can run repeatedly.

Verified the script runs, its first post receives `published: false`, and `npx tsc --noEmit` passes.

## Colleague's note

The npm tag mismatch, Prisma 8 package and contract layout, noninteractive `orm init --yes`, `contract emit`, `db init`, and `db.orm.public.User.include('posts').all()` guidance applied. The note's version numbers were time-specific: npm currently tagged `prisma` as `8.0.0-rc.33`, while `@prisma/client@latest` was `7.10.1` and `@prisma/orm-postgres@latest` was `8.0.0-rc.23`. Its report of a crash in an earlier release candidate did not apply; contract emission succeeded.

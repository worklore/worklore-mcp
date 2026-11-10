# Prisma ORM setup

## Versions
- `prisma` 7.10.1 (dev dependency) and `@prisma/client` 7.10.1, plus `@prisma/adapter-pg`, `pg`, `dotenv`, `@types/pg`.
- Version choice: the npm `latest` dist-tag for `prisma` currently points to the release candidate `8.0.0-rc.33`, while `@prisma/client`'s `latest` is the stable `7.10.1`. I used the stable 7.10.1 for both packages so they match and no pre-release is used. Upgrading to 8.x later is a deliberate step.

## Schema (`prisma/schema.prisma`)
- `User`: `id` (autoincrement), `email` (unique), `name` (optional), `posts` (relation).
- `Post`: `id` (autoincrement), `title` (required), `content` (optional), `published` (boolean, default `false`), `author`/`authorId` (each post has exactly one author).
- Generator output goes to `generated/prisma` (git-ignored).

## Configuration
- `prisma.config.ts` loads `.env` via `dotenv` and points Prisma at `DATABASE_URL`. Prisma 7 requires this; the datasource URL is no longer in the schema.
- PostgreSQL is accessed through the `@prisma/adapter-pg` driver adapter, which Prisma 7 requires.

## Database
- Ran `npx prisma migrate dev --name init` against the `n10` database on `localhost:5435` (it was empty).
- Created `prisma/migrations/<timestamp>_init/migration.sql` with the `User` and `Post` tables, and applied it.

## script.ts
- Run with `npx tsx script.ts`.
- Creates a user with a unique email (`user-<timestamp>@example.com`, so the script can be rerun without a unique-constraint error) and two posts (one published, one draft).
- Prints every user with their posts.

Sample output from the first run:

```
Created user 1 (user-1794270639585@example.com) with 2 posts

All users (1):
- [1] user-1794270639585@example.com (Example User)
    · [1] First post | published: true | content: Hello from Prisma
    · [2] Draft | published: false | content: Not published yet
```

## Verification
- `npx prisma validate` passed.
- `npx tsc --noEmit` passed.
- `npx tsx script.ts` ran successfully (exit code 0).

## Notes
- `src/index.ts` (the in-memory blog stub) is unchanged and does not use Prisma yet.
- Nothing was committed, deployed, published, or sent to any external service.

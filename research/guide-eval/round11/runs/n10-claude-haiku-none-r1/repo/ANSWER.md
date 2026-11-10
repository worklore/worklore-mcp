# Prisma ORM setup

## Versions

The npm `latest` dist-tag for `prisma` is `8.0.0-rc.33`, a release candidate. The `latest` tag for `@prisma/client` is the stable `7.10.1`. The CLI and client must match, so everything is pinned to the stable **7.10.1**:

- `prisma` (dev), `@prisma/client`, `@prisma/adapter-pg`, `pg`, `dotenv`, `@types/pg` (dev)

To use Prisma 8 once it is stable, upgrade all Prisma packages together.

## Schema (`prisma/schema.prisma`)

- `User`: `id` (autoincrement), `email` (unique), `name` (optional), `posts`
- `Post`: `id` (autoincrement), `title`, `content` (optional), `published` (default `false`), `author` / `authorId` (each post has exactly one author)

The client is generated to `src/generated/prisma` (git-ignored).

## Configuration

- `prisma.config.ts` loads `.env` via `dotenv` and reads `DATABASE_URL`.
- `.env` (not changed) holds the local PostgreSQL URL on port 5435.
- `.gitignore` adds `/src/generated/prisma`.

## Database

Ran `npx prisma migrate dev --name init`. This created `prisma/migrations/<timestamp>_init/migration.sql` and applied it to the `n10_n10_claude_haiku_none_r1` database. The database had no tables beforehand. It now contains `"User"` and `"Post"`, with the unique index on `User.email` and the foreign key `Post.authorId → User.id`.

## Script (`script.ts`)

`npx tsx script.ts` creates one user with two posts (one published, one draft). It then prints every user with their posts. The email includes a timestamp so the script can be re-run without a unique-constraint error. Each run adds another user to the database.

The script uses the `@prisma/adapter-pg` driver adapter, which Prisma 7 requires.

## Commands

```bash
npm install                 # installs dependencies
npx prisma generate         # regenerates src/generated/prisma (needed after a fresh clone)
npx prisma migrate dev      # applies migrations to the local database
npx tsx script.ts           # create sample data and print users with posts
npx tsc --noEmit            # typecheck
```

## Verification

- `npx prisma migrate dev --name init` succeeded; `psql` confirmed both tables and constraints.
- `npx tsx script.ts` exited 0 and printed the created user with two posts.
- `npx tsc --noEmit` passed.

## Other notes

- `prisma init` also installed agent-skill folders (`.agents/`, `.claude/`, `.windsurf/`, `skills-lock.json`). These were not part of the request, so they were removed.
- `src/index.ts` is unchanged; it still uses the in-memory store.
- Nothing has been committed, pushed, deployed or published.

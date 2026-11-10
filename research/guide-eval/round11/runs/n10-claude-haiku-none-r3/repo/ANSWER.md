# Prisma ORM setup

## Versions

- `prisma` (CLI): **7.10.1**
- `@prisma/client`: **7.10.1**
- `@prisma/adapter-pg`: **7.10.1** (driver adapter, required by Prisma 7)
- `dotenv`: used to load `DATABASE_URL` from `.env`

I pinned 7.10.1 rather than the `latest` dist-tag of `prisma`, which at the time pointed to the prerelease `8.0.0-rc.33`. The `@prisma/client` `latest` tag is the stable 7.10.1, so the CLI and client would not match on 8.0.0-rc. Moving to 8.x later means bumping both packages together.

## Schema (`prisma/schema.prisma`)

- `User`: `id` (autoincrement), `email` (unique, required), `name` (optional), `posts` (relation).
- `Post`: `id` (autoincrement), `title` (required), `content` (optional), `published` (boolean, default `false`), `authorId` (required foreign key to `User`). Each post has exactly one author.

The generated client goes to `src/generated/prisma` (git-ignored).

## Database

The migration `prisma/migrations/20261110021929_init/migration.sql` was applied to the local PostgreSQL database in `.env`. It creates the `User` and `Post` tables, the unique index on `User.email`, and the foreign key `Post.authorId -> User.id`. Prisma also created its `_prisma_migrations` bookkeeping table.

## Files added or changed

- `prisma/schema.prisma`, `prisma/migrations/…` — schema and migration.
- `prisma.config.ts` — Prisma 7 config (schema path, migrations path, datasource URL from `DATABASE_URL`).
- `script.ts` — creates one user with two posts and prints every user with their posts.
- `package.json` / `package-lock.json` — new dependencies.
- `.gitignore` — added `/src/generated/prisma`.

## Running the script

```sh
npx tsx script.ts
```

Each run creates a new user with a per-run email (`alice-<timestamp>@example.com`), so repeated runs don't violate the unique email constraint. The script then prints all users with their posts. The first run created user 1 with posts 1 and 2; a second run created user 2 with posts 3 and 4.

Other useful commands:

- `npx prisma migrate dev` — create and apply a new migration after changing the schema.
- `npx prisma generate` — regenerate the client after schema changes.

## Verification

- `npx prisma migrate dev --name init` applied the migration. `psql` shows the `User`, `Post`, and `_prisma_migrations` tables with the expected columns and constraints.
- `npx tsx script.ts` ran successfully twice.
- `npx tsc --noEmit` passes.
- `npm run dev` (the existing `src/index.ts`) still runs unchanged.

## Cleanup note

`prisma init` also installed agent skill files (`.agents/`, `.claude/`, `.windsurf/`, `skills-lock.json`). I removed them because they were not part of the request, and renamed the generated `prisma7.config.ts` to `prisma.config.ts`.

Nothing was committed, deployed, or sent to any external service.

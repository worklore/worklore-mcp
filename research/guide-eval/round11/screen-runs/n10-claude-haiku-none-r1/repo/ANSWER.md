# Prisma ORM setup

## Versions

- `prisma` (CLI) and `@prisma/client`: **7.10.1**, the latest stable release on npm.
- `@prisma/adapter-pg`: **7.10.1**, the driver adapter Prisma 7 requires for PostgreSQL.
- Note: the npm `latest` dist-tag for `prisma` currently points to the prerelease `8.0.0-rc.33`. I did not use it, because it is not a stable release and its `@prisma/client` counterpart is still 7.10.1.

## What I did

1. Installed the packages:
   - dev: `prisma`
   - runtime: `@prisma/client`, `@prisma/adapter-pg`, `dotenv` (used to load `.env` in the Prisma config and in `script.ts`)
2. `prisma/schema.prisma`: a PostgreSQL datasource and the client generator (`prisma-client`, output `generated/prisma`).
   - `User`: `id` (autoincrement PK), `email` (unique, required), `name` (optional), `posts` (relation).
   - `Post`: `id` (autoincrement PK), `title` (required), `content` (optional), `published` (boolean, default `false`), `author` / `authorId` (required foreign key to `User`, one author per post).
3. `prisma.config.ts`: points Prisma at the schema, the migrations folder, and `DATABASE_URL` from `.env`.
4. `npx prisma migrate dev --name init`: created `prisma/migrations/20261110001631_init/migration.sql` and applied it to the local database `n10` (port 5435). I checked with `psql` that the `User` and `Post` tables exist with the expected columns, the unique index on `User.email`, and the foreign key `Post.authorId -> User.id`.
5. `script.ts` (project root): creates the user `alice@example.com` with two posts (one published, one draft) using a nested create, then lists every user with their posts.
6. Added `generated/` to `.gitignore`, since the generated client is build output. `.env` was already ignored.

## Running it

```sh
npx tsx script.ts
```

Output from the first run:

```
Created user 1 (alice@example.com)

User #1 alice@example.com (Alice)
  - [published] Hello world: My first post
  - [draft] Draft: Work in progress
```

Running the script a second time fails with a unique-constraint error on `email`, because the script always creates the same user. Delete the row or change the email to run it again.

## Other useful commands

- `npx prisma migrate dev --name <name>`: create and apply a migration after changing the schema.
- `npx prisma generate`: regenerate the client after schema changes (`migrate dev` also does this).
- `npx tsc --noEmit`: type-check the project. It passes.

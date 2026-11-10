# Prisma ORM setup

## Version choice

`npm view prisma dist-tags` reports `latest` = `8.0.0-rc.33`, but that is a release candidate, and `@prisma/client`'s `latest` is the stable `7.10.1`. The two packages don't line up on 8 yet, so I pinned the stable **7.10.1** release for both `prisma` (dev dependency) and `@prisma/client`. Moving to 8 is a later step once it is stable.

Also installed:
- `@prisma/adapter-pg` (7.10.1): Prisma 7 requires a driver adapter for PostgreSQL.
- `dotenv`: `npx tsx` does not read `.env`, so the script loads it explicitly.

## Schema (`prisma/schema.prisma`)

- `User`: `id` (autoincrement int, PK), `email` (unique), `name` (optional), `posts` (relation).
- `Post`: `id`, `title` (required), `content` (optional), `published` (boolean, default `false`), `authorId` (required FK to `User.id`). Each post has exactly one author; a user can have many posts.

## Configuration

- `prisma.config.ts` reads `DATABASE_URL` from `.env` and points at the schema and migrations folder.
- The generator writes the client to `generated/prisma` (added to `.gitignore`).

## Database

I ran `npx prisma migrate dev --name init` against the database in `.env` (PostgreSQL on `localhost:5435`, database `n10_n10_claude_haiku_none_r2`). It created the migration `prisma/migrations/<timestamp>_init/migration.sql` and created the tables `"User"`, `"Post"` and `_prisma_migrations`. I confirmed the `"Post"` table with `psql`. Then I ran `npx prisma generate`.

## script.ts

Run with `npx tsx script.ts`. It:
1. Creates a user with two posts (one published, one draft). The email includes a timestamp so the script can run more than once without hitting the unique constraint.
2. Queries all users with their posts, ordered by id, and prints them.

I ran it twice. The first run printed one user with two posts; the second printed two users. `npx tsc --noEmit` passes.

## Commands

```sh
npm install                  # installs dependencies
npx prisma migrate dev       # apply schema changes and create a migration
npx prisma generate          # regenerate the client
npx tsx script.ts            # run the demo script
```

## Notes

- npm printed install-script warnings for `prisma`, `@prisma/engines` and `esbuild`. These are informational. The commands above all succeeded.
- Nothing was committed, deployed, published or sent to any external service.

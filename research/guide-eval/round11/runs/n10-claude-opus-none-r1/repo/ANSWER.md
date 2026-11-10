# Adding Prisma ORM

## Version used: 7.10.1 (not the npm `latest` tag)
On 2026-11-09, `npm view prisma dist-tags` showed `latest` → **8.0.0-rc.33**, a *release candidate*
(published 2026-11-06). `prev` showed 7.10.1, and `@prisma/client` and `@prisma/adapter-pg` were both
`latest` → **7.10.1**. The CLI and client versions have to match, and the only one available for all
three packages is 7.10.1, which is also the newest stable release. So I pinned `prisma`,
`@prisma/client` and `@prisma/adapter-pg` to **7.10.1**. If you want the 8.0 RC, bump all three together
once a matching `@prisma/client` 8.x is published.

## What I did
- **Dependencies**: `prisma@7.10.1` (dev), plus `@prisma/client@7.10.1`, `@prisma/adapter-pg@7.10.1`,
  `pg` and `dotenv`. Prisma 7 needs a driver adapter at runtime, so `pg` and `@prisma/adapter-pg` are required.
- **`prisma.config.ts`**: tells Prisma where the schema and migrations are, and reads `DATABASE_URL` from `.env`.
  Prisma 7 sets the URL here, not in the schema. `.env` was not modified.
- **`prisma/schema.prisma`**:
  - `User`: `id` (autoincrement), `email` (unique), `name` (optional), `posts`.
  - `Post`: `id`, `title`, `content` (optional), `published` (default `false`), `author` relation through
    a required `authorId` foreign key (each post has exactly one author).
  - Generator `prisma-client`, output `src/generated/prisma`. This folder is in `.gitignore`.
- **Tables**: `npx prisma migrate dev --name init` created and applied `prisma/migrations/<ts>_init/migration.sql`.
  The database now contains `User`, `Post` and `_prisma_migrations`.
- **`script.ts`**: creates a user with two posts in a nested `create` (one published, one draft), then prints
  every user with their posts (`findMany({ include: { posts: true } })`). The email has a timestamp suffix so
  the script can be run again without breaking the unique constraint. Each run adds one more user.
- **npm scripts**: `postinstall` → `prisma generate` (rebuilds the git-ignored client after `npm install`),
  `db:migrate` → `prisma migrate dev`, `script` → `tsx script.ts`.

## Verification
- `npx tsx script.ts` created user id 1 with posts 1 and 2 and printed them.
- `npx tsc --noEmit` passes.

## Notes
- npm skipped install scripts for `prisma`/`esbuild` (npm's install-script approval policy). Nothing broke,
  because the client is generated explicitly with `prisma generate`.
- `src/index.ts` (the in-memory store) is unchanged. Moving it onto Prisma would be the next step.
- The database now holds the demo rows `script.ts` created.

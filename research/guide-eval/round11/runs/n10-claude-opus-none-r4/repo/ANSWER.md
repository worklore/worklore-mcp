# Prisma setup

## Version choice
On npm, the `latest` tag for the `prisma` CLI currently points to a **release candidate**
(`8.0.0-rc.33`). But `latest` for `@prisma/client` and `@prisma/adapter-pg` is `7.10.1`.
The CLI and client must be the same version, so I pinned all three to **7.10.1**, the newest
stable release (exact versions, no `^`).

## What was added
- **Dependencies:** `@prisma/client`, `@prisma/adapter-pg` (Prisma 7 needs a driver
  adapter), `dotenv`. **Dev dependency:** `prisma`.
- **`prisma.config.ts`:** Prisma 7 config. It loads `.env` and reads `DATABASE_URL` from there.
- **`prisma/schema.prisma`:**
  - `User`: `id` (autoincrement), `email` (unique), `name` (optional), `posts`.
  - `Post`: `id`, `title`, `content` (optional), `published` (default `false`),
    `author` relation via `authorId` (required, so every post has exactly one author).
  - Uses the `prisma-client` generator, which writes to `src/generated/prisma`.
    That folder is generated, so I added it to `.gitignore`.
- **`prisma/migrations/<timestamp>_init/migration.sql`:** created and applied with
  `npx prisma migrate dev --name init`. The `User`, `Post` and `_prisma_migrations`
  tables now exist in the database from `.env`.
- **`script.ts`:** upserts `alice@example.com` and, if the user is new, creates two posts
  for them (one published, one draft). It then prints every user with their posts. Using
  upsert means you can run it again without breaking the unique email rule.

## Running
```sh
npm install
npx prisma generate      # regenerates the client (it is gitignored)
npx tsx script.ts
```

## Verified
- `npx tsx script.ts` printed Alice with both posts. Running it a second time worked too and
  did not create duplicates (the database has 2 posts).
- `npx tsc --noEmit` passes.

## Notes
- Newer npm blocks package install scripts by default (`@prisma/engines` postinstall).
  Migrations and generation still worked. If a clean install has trouble, run
  `npm install-scripts approve @prisma/engines`.
- `src/index.ts` (the in-memory store) is unchanged. Moving it onto Prisma is a separate step.

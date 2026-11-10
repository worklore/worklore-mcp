# Prisma ORM setup

## Versions
- `prisma`, `@prisma/client`, `@prisma/adapter-pg`: **7.10.1**, plus `pg` and `dotenv`.
- I pinned these to the newest **stable** release on purpose. At the time of setup, the `latest`
  tag of the `prisma` CLI on npm pointed to `8.0.0-rc.33`, a release candidate. There is no
  `@prisma/client` / `@prisma/adapter-pg` at that version: their `latest` is 7.10.1. The CLI
  and client versions have to match, so 7.10.1 is the newest set that works together.

## What was added
- `prisma/schema.prisma`: the `User` and `Post` models.
  - `User`: `id` (autoincrement), `email` (unique), `name` (optional), `posts`.
  - `Post`: `id`, `title`, `content` (optional), `published` (default `false`), and
    `authorId` → `User` (each post has exactly one author).
  - Generator `prisma-client` (Prisma 7), output `src/generated/prisma` (gitignored).
- `prisma.config.ts`: Prisma 7 config. It reads `DATABASE_URL` from `.env` through `dotenv`.
- `prisma/migrations/<timestamp>_init/migration.sql`: the initial migration.
  It was applied with `npx prisma migrate dev --name init`, so the database now has the
  `User`, `Post` and `_prisma_migrations` tables.
- `script.ts`: connects through the `@prisma/adapter-pg` driver adapter (Prisma 7 requires
  one). It creates a user with two posts (one published, one draft), then prints every
  user with their posts. The email gets a timestamp suffix, so running the script again
  doesn't hit the unique constraint.
- `package.json` scripts: `npm run generate` (`prisma generate`) and `npm run migrate`.

## Run it
```bash
npm install
npx prisma generate          # the generated client is gitignored, so generate it after a fresh clone
npx prisma migrate dev       # only needed against a new database
npx tsx script.ts
```
Verified: `npx tsx script.ts` printed the user with both posts, and `npx tsc --noEmit` passes.

## Notes
- `prisma init` (7.10.1) also downloaded AI-agent "skill" files from GitHub
  (`.agents/`, `.claude/skills`, `.windsurf/skills`, `skills-lock.json`). They mostly push an
  upgrade to Prisma 8 and deploying on Prisma Compute. Neither was requested, so I deleted
  them. `init` also named its config `prisma7.config.ts`; I renamed it to the standard
  `prisma.config.ts`.
- npm skipped the install scripts of `prisma`/`esbuild` (npm's install-script approval). The
  engines were still present, and everything ran fine.
- `src/index.ts` is unchanged; it still uses its in-memory store.

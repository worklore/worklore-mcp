# Prisma ORM setup

## Versions

- `prisma` (CLI) and `@prisma/client`: **7.10.1**, the current stable release on npm.
  The `prisma` package's `latest` dist-tag currently points to `8.0.0-rc.33`, a release candidate.
  I did not use it, and I pinned both packages to the same stable version so the CLI and client match.
- `@prisma/adapter-pg` 7.10.1: the PostgreSQL driver adapter, which Prisma 7 requires for the client.
- `dotenv` 18.0.10: loads `DATABASE_URL` from `.env`.

## What was done

1. **Installed packages** with exact versions (`--save-exact`).
2. **Schema** in `prisma/schema.prisma`:
   - `User`: `id` (autoincrement), `email` (unique, required), `name` (optional), `posts` (relation).
   - `Post`: `id`, `title` (required), `content` (optional), `published` (boolean, default `false`), `author` / `authorId` (required, each post has one author).
   - Generator: `prisma-client`, output to `src/generated/prisma` (git-ignored).
3. **Config** in `prisma.config.ts`: schema path, migrations path, and the datasource URL read from `DATABASE_URL`. Prisma 7 takes the URL from this file, not from the schema.
4. **Migration** `prisma/migrations/<timestamp>_init/migration.sql` applied to the local database `n10` (port 5435). It created the `User` and `Post` tables, the unique index on `User.email`, and the foreign key `Post.authorId -> User.id`. I checked the tables with `psql`.
5. **Client generated** with `prisma generate`. I also added a `postinstall` script so a fresh `npm install` regenerates it.
6. **`script.ts`** at the project root:
   - Creates a user with two posts (one published, one draft) using a nested create.
   - Prints every user with their posts.
   - Uses a unique email per run (`author-<timestamp>@example.com`), so it can be re-run without violating the unique constraint.
   - Loads `.env` itself, so `npx tsx script.ts` works without exporting variables.

## Run it

```sh
npx tsx script.ts
```

Output from my run (the second run added another user in the same way):

```
1 author-1794271535361@example.com (Example Author)
  - [1] First post | published=true | content=Hello from Prisma
  - [2] Draft post | published=false | content=null
```

`npx tsc --noEmit` passes.

## Other changes

- `.gitignore`: added `src/generated/`.
- `package.json`: added `postinstall` (`prisma generate`) and `db:migrate` (`prisma migrate dev`) scripts.
- `src/index.ts` is unchanged. It still uses the in-memory store.

## Nothing was deployed or published

All work stayed in this directory. The only external connection was to the local PostgreSQL database in `.env`. Nothing was committed.

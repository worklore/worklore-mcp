# Prisma ORM setup

## Versions

- `prisma` (CLI) and `@prisma/client` pinned to **7.10.1**, the latest stable release.
  - Note: the npm `latest` tag for `prisma` currently points to `8.0.0-rc.33`, a prerelease, while `@prisma/client`'s `latest` is `7.10.1`. I used the stable 7.10.1 line for both packages so the CLI and client versions match.
- `@prisma/adapter-pg` 7.10.1 with `pg` 8.23.1 (Prisma 7 requires a driver adapter for PostgreSQL).
- `dotenv` 18.0.10 to load `DATABASE_URL` from `.env`.
- `@types/pg` 8.23.1 (dev).

## What was done

1. **Installed the packages** with `--save-exact` so versions are pinned in `package.json`.
2. **`prisma.config.ts`** (project root): points Prisma at `prisma/schema.prisma`, the migrations folder, and the `DATABASE_URL` env var. It loads `.env` via `dotenv`.
3. **`prisma/schema.prisma`**:
   - `User`: `id` (autoincrement int PK), `email` (unique, required), `name` (optional), `posts` (relation).
   - `Post`: `id` (autoincrement int PK), `title` (required), `content` (optional), `published` (boolean, default `false`), `author` / `authorId` (required foreign key to `User`, so each post has exactly one author).
   - The generator is `prisma-client`, output to `generated/prisma` (git-ignored).
4. **Migration**: `npx prisma migrate dev --name init` created `prisma/migrations/<timestamp>_init/migration.sql` and applied it to the local PostgreSQL database in `.env`. The tables `"User"` and `"Post"` now exist, with the unique index on `User.email` and the foreign key `Post.authorId -> User.id`.
5. **Client generation**: `npx prisma generate` produced the typed client in `generated/prisma`.
6. **`script.ts`** (project root):
   - Creates a user with two posts (one published, one draft) in a single nested `create`.
   - Uses a per-run email (`user-<timestamp>@example.com`) so the script can be re-run without violating the unique constraint.
   - Prints every user with their posts as JSON.
7. **`.gitignore`**: added `generated` so the generated client is not committed.

## Running

```sh
npx tsx script.ts          # create a sample user + posts and print all users
npx tsc --noEmit          # typecheck passes
npx prisma migrate dev    # apply schema changes during development
```

I ran `npx tsx script.ts` once while setting things up, so the database now contains one sample user with two posts. Each further run adds another user.

## Files added or changed

- `package.json`, `package-lock.json`: dependencies.
- `prisma.config.ts`, `prisma/schema.prisma`, `prisma/migrations/…_init/migration.sql`: Prisma configuration, schema, and migration.
- `script.ts`: the sample script.
- `generated/prisma/`: generated client (git-ignored).
- `.gitignore`: added `generated`.
- `ANSWER.md`: this file.

Nothing was deployed, published, or sent to any external service. Everything was done against the local database in `.env`.

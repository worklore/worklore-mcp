# Adding Prisma ORM to notes-api

## What "current" resolved to

Checked with `npm view` on 2026-11-09:

| Package | `latest` tag |
|---|---|
| `prisma` | `8.0.0-rc.33` |
| `@prisma/orm-postgres` | `8.0.0-rc.23` |
| `@prisma/client` | `7.10.1` |

So the current Prisma from npm is Prisma 8. Prisma 8 has no `@prisma/client`; its client is `@prisma/orm-postgres`. I did not install `@prisma/client`, and `npm ls @prisma/client` reports nothing.

Caveat: the `latest` tag for `prisma` is a release candidate (`8.0.0-rc.33`), not a stable `8.0.0`. If you need a stable release, Prisma 7 (`@prisma/client@7.10.1`) is the alternative. I went with the `latest` tag because you asked for the current version.

## What I did

1. **Scaffolded with the Prisma 8 init**: `npx prisma@latest orm init --yes --target postgres --authoring psl`. `--yes` avoids the interactive prompts. This added `prisma`, `@prisma/orm-postgres`, `@prisma/cli-engine` (dev), `dotenv`, `prisma.config.ts`, `src/prisma/contract.prisma`, `src/prisma/db.ts`, `prisma-8.md`, and `.env.example`.
2. **Models** in `src/prisma/contract.prisma`, as specified:
   - `User`: `id` (autoincrement), `email` (unique), `name` (optional), `posts`.
   - `Post`: `id` (autoincrement), `title`, `content` (optional), `published` (default `false`), `author` (relation to `User`), `authorId`.
   The scaffold's example models also had `username`, `createdAt` and `updatedAt`. I removed them because they were not in the spec.
3. **Emitted the contract**: `npx prisma contract emit` wrote `src/prisma/contract.json` and `src/prisma/contract.d.ts`.
4. **Created the tables**: `npx prisma db init`. It created `User` and `Post`, the unique index on `User.email`, the `authorId` index, and the foreign key from `Post.authorId` to `User.id`. It also wrote `migrations/`, which holds the contract snapshot and the marker for the applied contract hash. Keep it committed; the CLI uses it.
5. **`script.ts`** at the project root. It creates one user and two posts inside `db.transaction`, then prints every user with `include("posts")`. It closes the client with `db.close()`.
6. **Verified**:
   - `npx tsx script.ts` exits 0 and prints the user with both posts.
   - `psql` shows the `User` and `Post` tables, the user row, and both post rows, with `published` = `false` by default.
   - `npx tsc --noEmit` passes.
   - `npm ls prisma @prisma/orm-postgres` shows `prisma@8.0.0-rc.33` and `@prisma/orm-postgres@8.0.0-rc.23`.

## Changes to existing files

- `package.json`: added the `prisma`, `@prisma/orm-postgres`, `@prisma/cli-engine`, and `dotenv` dependencies, plus a `contract:emit` script.
- `tsconfig.json`: `module` changed from `ESNext` to `preserve`, and `"types": ["node"]` added. The generated `db.ts` imports JSON with an import attribute, and this config is what the scaffold expects.
- `.gitignore`: the scaffold appended `node_modules/` and `dist/`. `node_modules` was already ignored, so that line is redundant but harmless.
- `.gitattributes`, `.env.example`, `prisma-8.md`, `prisma.config.ts`, `package-lock.json`: new, from the scaffold.

`.env` is unchanged. It is gitignored.

## Which parts of the colleague's note applied

- **Applied: check the dist-tags first.** The tags matched the note: `prisma` on 8, `@prisma/client` on 7. That is why I used Prisma 8 and skipped `@prisma/client`.
- **Applied: `prisma orm init --yes --target postgres --authoring psl`.** Used as written. With `--yes` the command ran without waiting for input.
- **Applied: `contract.prisma` as the place for models, `contract emit`, then `db init`.** Used in that order.
- **Applied: query through `import { db } from "./src/prisma/db"`, and `db.close()` at the end of a script.** `db.orm.public.User.include("posts").all()` is used in `script.ts`.
- **Applied in part: `db.orm.public.User.create(...)`.** The note's example does not create posts. The script creates the user and each post with `tx.orm.public.Post.create({ authorId })` inside `db.transaction`, following the transaction example in the package's `skills/prisma-8/references/queries-postgres.md`.
- **Not applicable: the `contract emit` crash on rc.29.** The note reports it on that release candidate. I did not hit it on rc.33.
- **Not applicable: the note's `--probe-db`, pnpm, and Supabase notes.** This project uses npm and a local database.
- **Not applied: running `prisma skills sync`.** The init printed that the agent skills are out of date. Syncing writes to agent configuration, which is outside what you asked for, so I did not run it.

## Things to know

- **Each run of `script.ts` adds a new user.** The email is `alice+<timestamp>@example.com`, so the unique constraint on `User.email` is not hit on re-runs. This means the database is no longer empty: I ran the script once while verifying, so there is one user (`alice+1794270732687@example.com`) and two posts in it. Delete those rows if you want a clean database.
- **`@prisma/orm-postgres` is at rc.23 while `prisma` is at rc.33.** That matches the `latest` tags on npm. The init warned about the skill mismatch; the CLI and runtime both worked in testing.
- **Nothing was deployed or published.** Everything ran against the local database in `.env`.

# Adding Prisma ORM to notes-api

## Versions

Checked with `npm view` on the day of the work (2026-11-09):

| Package | `latest` tag | Installed |
|---|---|---|
| `prisma` | 8.0.0-rc.33 | 8.0.0-rc.33 (dev dependency) |
| `@prisma/orm-postgres` | 8.0.0-rc.23 | 8.0.0-rc.23 (dependency) |
| `@prisma/client` | 7.10.1 | not installed (Prisma 8 does not use it) |

The current Prisma on npm is Prisma 8. Note that `latest` is a **release candidate** (`8.0.0-rc.33`), not a stable
release. If you want a stable release, the stable line is Prisma 7 (`@prisma/client` 7.10.1); I did not choose it
because you asked for the current version.

## What I did

1. Confirmed the database in `.env` (`localhost:5435/n10`) was reachable and empty.
2. Scaffolded the project:
   `npx prisma@latest orm init --yes --target postgres --authoring psl`
   (`--yes` avoids the interactive prompts; `--write-env` was not passed, so `.env` was left as it was.)
3. Replaced the scaffold's example models in `src/prisma/contract.prisma` with the models you asked for:
   - `User`: `id`, `email` (unique), `name` (optional), `posts`
   - `Post`: `id`, `title`, `content` (optional), `published` (Boolean, default `false`), `author`/`authorId` (one author)
4. Emitted the contract: `npm run contract:emit` (runs `prisma contract emit`).
5. Created the tables: `npx prisma db init --dry-run` to preview, then `npx prisma db init`. Five additive operations
   were applied: tables `User` and `Post`, the unique constraint on `User.email`, the index and foreign key on
   `Post.authorId`.
6. Wrote `script.ts` at the project root. It creates one user (`alice@example.com`) and two posts, then prints every
   user with their posts through `db.orm.public.User.include("posts").all()`. It calls `db.close()` at the end.
7. Ran it with `npx tsx script.ts`. It exits 0 and prints:
   ```
   Alice <alice@example.com>
     - [published] Hello, world
     - [draft] Draft notes
   ```

## Verification

- `npx tsc --noEmit` passes.
- `npx tsx script.ts` runs and prints the rows above.
- `psql` shows both rows in the database, with `published` = `t` for "Hello, world" and `f` for "Draft notes".
- `npm ls prisma @prisma/orm-postgres @prisma/client` shows `prisma@8.0.0-rc.33` and `@prisma/orm-postgres@8.0.0-rc.23`.
  `@prisma/client` is not installed.

## Changes to existing files

- `package.json`: added the `contract:emit` script, plus the dependencies `prisma`, `@prisma/cli-engine`,
  `@prisma/orm-postgres`, and `dotenv`. `@prisma/cli-engine` is needed by `prisma.config.ts`.
- `tsconfig.json`: the scaffold changed `module` from `ESNext` to `preserve` and added `"types": ["node"]`.
- `.gitignore`: the scaffold added `node_modules/` and `dist/`. `node_modules` was already listed, so it now appears twice.
  This is harmless.
- `src/index.ts` is unchanged.

New files: `prisma.config.ts`, `src/prisma/contract.prisma`, `src/prisma/contract.json`, `src/prisma/contract.d.ts`,
`src/prisma/db.ts`, `prisma-8.md`, `.env.example`, `.gitattributes`, `package-lock.json`, `script.ts`, `ANSWER.md`,
and `migrations/` (written by `db init`: `app/refs/db.json` records which contract the database matches, and
`snapshots/` holds a copy of the contract). Commit `migrations/` with the rest.

## Notes

- **The database now contains the sample data.** The verification run inserted `alice@example.com` and her two posts.
  `script.ts` is not idempotent: running it again fails on the unique `email` constraint. Delete the row first, or change
  the email, before running it again.
- `npx prisma skills sync` was suggested by the CLI. I did not run it, because it changes agent skill files and you did
  not ask for that.
- Nothing was committed, published, or sent to any external service.

## Colleague's note: what applied

Applied:
- Checking the npm tags before choosing a version. The tags matched the note: `prisma@latest` is 8.x and
  `@prisma/client@latest` is still 7.10.1.
- Using `prisma@latest orm init --yes --target postgres --authoring psl` with `--yes`, so the command does not wait for input.
- Not installing `@prisma/client`.
- Emitting the contract, then `db init`, then querying with `import { db } from "./src/prisma/db"` and calling `db.close()`.
- The verification steps: `npm ls`, the tables in the database, and `npx tsx` printing the rows it wrote.

Did not apply, or differed:
- The note's example `User` model has no `published` field, and the scaffold's example models include `username` and
  timestamps. I replaced the example models with yours, as you specified.
- The note's example `db.orm.public.User.create({...})` with a nested `posts` create does not type-check here. A nested
  relation mutation takes one post per callback, so I created the posts as separate `Post.create` calls with `authorId`.
- The note's warning about rc.8 crashing on `contract emit` does not apply. `contract emit` worked on rc.33.
- The note says the release candidate is on `latest`. That is still true on the day of the work, and I kept to it.
  I flagged the RC status above because you may not want a release candidate.

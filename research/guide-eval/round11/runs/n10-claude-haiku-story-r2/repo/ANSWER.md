# Adding Prisma ORM to notes-api

## Which version

"Current from npm" is Prisma 8. I checked the dist-tags first:

- `prisma@latest` = `8.0.0-rc.33`
- `@prisma/client@latest` = `7.10.1`

I did not install `@prisma/client`. Prisma 8 has no `@prisma/client`; its client is `@prisma/orm-postgres`.

Installed:

- `prisma@8.0.0-rc.33` (dev), plus `@prisma/cli-engine@0.9.0` (dev), which the init script added
- `@prisma/orm-postgres@8.0.0-rc.23` (runtime)
- `dotenv` (runtime; loads `.env` for the config and the client)

Caveat: Prisma 8 is a release candidate, not a stable release. If you want the stable 7 line instead, that is a deliberate switch to `prisma@7` and `@prisma/client`, and it would change the code below.

## What I did

1. Ran `npx prisma@latest orm init --yes --target postgres --authoring psl`. This created `src/prisma/contract.prisma`, `src/prisma/db.ts`, `prisma.config.ts`, `prisma-8.md`, and `.env.example`, and modified `package.json`, `tsconfig.json`, and `.gitignore`.
2. Replaced the scaffold's example models in `src/prisma/contract.prisma` with the requested ones:
   - `User`: `id`, `email` (unique), `name` (optional), `posts`
   - `Post`: `id`, `title`, `content` (optional), `published` (default `false`), `author` (relation), `authorId`
   The scaffold's extra fields (`username`, `createdAt`, `updatedAt`) were not requested, so I removed them.
3. `npx prisma contract emit` generated `src/prisma/contract.json` and `src/prisma/contract.d.ts`.
4. `npx prisma db init --dry-run` showed five additive operations. I then ran `npx prisma db init --yes`, which created the tables and the unique and foreign-key constraints, and wrote a `migrations/` directory with the ref and snapshot.
5. Wrote `script.ts` at the project root. It creates one user with two posts (one published, one draft) and prints every user with their posts. Each run uses a new timestamped email, because `email` is unique.
6. Added the `contract:emit` script to `package.json` (from init).

## Verification

- `npx tsc --noEmit` passes, including `script.ts`.
- `npx tsx script.ts` exits 0 and prints the user with both posts.
- In `psql`, the `User` and `Post` tables hold the rows the script wrote (user 1 with posts 1 and 2; post 1 has `published = t`, post 2 has `published = f`).
- `npm ls prisma @prisma/orm-postgres` shows 8.x for both; `npm ls @prisma/client` is empty.

## Changes to existing files

- `tsconfig.json`: init changed `module` from `ESNext` to `preserve` and added `"types": ["node"]`.
- `.gitignore`: init added `node_modules/` and `dist/`. `node_modules` was already listed, so it now appears twice.
- `package.json`: adds the Prisma dependencies, `dotenv`, and the `contract:emit` script.
- `src/index.ts` is unchanged.

## Colleague's note: what applied

- **Applied:** the dist-tag check (`prisma` on 8, `@prisma/client` on 7), so the project uses Prisma 8 and no `@prisma/client`.
- **Applied:** `npx prisma@latest orm init --yes --target postgres --authoring psl`. The `--yes` flag avoided the interactive prompts.
- **Applied:** replacing the scaffold's example models, then `contract emit`, `db init`, and querying through `db` from `./src/prisma/db`.
- **Applied:** `db.orm.public.User.include("posts").all()` for the listing, and `db.close()` at the end of the script.
- **Applied:** the verification steps (`npm ls`, tables present in the database, `npx tsx` printing the written rows).
- **Not applied:**
  - The stable Prisma 7 option: I used the current 8 release line as requested.
  - `prisma init` and `prisma skills sync`. The CLI warned that the agent skills are out of date; I left that alone because it was not part of the task.
  - `--probe-db`: the database is on PostgreSQL 17, which is above the 15+ requirement, so no probe was needed.
  - The `contract emit` crash fix on rc.29: this project uses rc.33, and emit worked.
  - The pnpm-workspace notes: this is an npm project, not a workspace.
- **Ground rules followed:** all work stayed in the project directory. Nothing was deployed, published, or reported to an external service.

## Notes

- `script.ts` adds a new user on every run, so the printed list grows over time.
- `migrations/` and `src/prisma/contract.json` / `contract.d.ts` are generated. They are meant to be committed, along with `prisma.config.ts` and `.env.example`. `.env` stays ignored.

# Prisma ORM setup — ANSWER

## What was done

1. **Version chosen: the npm `latest` tag, as requested.** On 2026-11-09 `npm view prisma dist-tags` gives `latest: 8.0.0-rc.33`. That is a release candidate, not a stable release. The stable 7 line (`@prisma/client` / `7.10.1`) is also available on npm, but it is not what `latest` points to for `prisma`, so I did not use it. If you want stable instead, say so and I will switch.
2. **Scaffold:** `npx --yes prisma@latest orm init --yes --target postgres --authoring psl`. `--yes` is needed so the command does not wait for interactive prompts.
   - Added `prisma` (8.0.0-rc.33), `@prisma/cli-engine`, `@prisma/orm-postgres` (8.0.0-rc.23, the version the scaffold installs), `dotenv`.
   - Created `prisma.config.ts`, `src/prisma/contract.prisma`, `src/prisma/db.ts`, `prisma-8.md`, `.env.example`, `.gitattributes`, `package-lock.json`.
   - Modified `package.json` (added a `contract:emit` script and the dependencies above), `tsconfig.json` (`module` changed from `ESNext` to `preserve`, `types: ["node"]` added), and `.gitignore` (added `node_modules/` and `dist/`, which duplicate existing lines).
   - `.env` was not touched; it still holds `DATABASE_URL` for `localhost:5435`.
3. **Schema** (`src/prisma/contract.prisma`). I replaced the scaffold's example models with exactly the requested fields:
   - `User`: `id`, `email` (unique), `name` (optional), `posts` (relation).
   - `Post`: `id`, `title`, `content` (optional), `published` (Boolean, default `false`), `author` / `authorId` (required, one author per post).
   - I removed the scaffold's `username`, `createdAt`, and `updatedAt` fields because they were not requested.
4. **Contract:** `npx prisma contract emit` generated `src/prisma/contract.json` and `contract.d.ts`.
5. **Tables:** `npx prisma db init --dry-run --yes` previewed 5 operations (two tables, the unique email constraint, the `authorId` index, and the foreign key). `npx prisma db init --yes` applied them. `\dt` on the database now lists `public."Post"` and `public."User"`.
6. **Script** (`script.ts`, project root). It creates the user `alice@example.com` with two posts (one published, one draft), then prints all users with their posts as JSON. `npx tsx script.ts` runs cleanly. `npx tsc --noEmit` passes.

## Using the colleague's note

I checked the note's claims against npm and the CLI before using them.

| Part of the note | Status |
|---|---|
| `prisma@latest` is Prisma 8 RC, `@prisma/client@latest` is 7.10.1 | **Confirmed** on npm today (`rc.33` / `7.10.1`). |
| The CLI and client must match (old rule) | Not applied. Prisma 8 uses `@prisma/orm-postgres` instead of `@prisma/client`. |
| Use `prisma orm init --target postgres --authoring psl` | **Applied**, and it worked. |
| Add `--yes` to avoid the interactive prompt | **Applied.** |
| Models go in `src/prisma/contract.prisma`, then `npx prisma contract emit` | **Applied.** |
| Tables via `npx prisma db init` | **Applied.** I ran `--dry-run` first. |
| Queries via `import { db } from "./src/prisma/db"`, `db.orm.public.User.create`, `db.orm.public.User.include("posts").all()`, `db.close()` | **Applied**, and it compiled and ran. |
| The `contract emit` crash on rc.29 (fixed in rc.33) | **Not observed.** The current `latest` (rc.33) emitted without errors. |
| Choosing the stable 7 line is valid but does not match "current from npm" | **Applied as the reasoning** for choosing `latest` (rc.33) over 7.10.1. |

## Caveats

- **Prisma 8 is a release candidate.** Expect API or behavior changes before it goes stable.
- **`script.ts` is not idempotent.** `email` is unique, so a second run fails at the first `User.create` with a unique-constraint error and writes nothing. To run it again, delete the `alice@example.com` row (and its posts) or change the email in the script.
- The scaffold printed "Prisma agent skills are out of date" and suggested `prisma skills sync` and `prisma init`. I did not run them; they were not part of the request.
- The database received one user and two posts from the verification run. Nothing was deployed, published, or sent to any external service.
- Nothing was committed.

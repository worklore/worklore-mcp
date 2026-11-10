# Adding Prisma ORM to notes-api

## Which version

"Current version from npm" was checked with `npm view`:

| npm tag | `prisma` | `@prisma/client` |
|---|---|---|
| `latest` | `8.0.0-rc.33` | `7.10.1` |

Prisma 8 is the version `latest` points to for the CLI, so I used it. Prisma 8's client is `@prisma/orm-postgres`; `@prisma/client` only has `8.1.0-dev.*` prereleases on npm, and I did not use those. Two things to know:

- `8.0.0-rc.33` is a **release candidate**, not a stable release. The stable line is 7.10.1. If you want stable instead, the Prisma 7 setup is a different API, and I did not use it.
- The CLI resolved to `rc.33`, but the scaffold pulled `@prisma/orm-postgres` at `8.0.0-rc.23` (`^8.0.0-rc.23` in `package.json`). I did not change this.

## What I did

1. Ran the scaffold non-interactively, after checking `prisma orm init --help`:
   `npx --yes prisma@latest orm init --yes --target postgres --authoring psl --probe-db`
   (`--probe-db` was skipped because `DATABASE_URL` is not exported in the shell; `.env` is not read for the probe.)
   It added `prisma`, `@prisma/orm-postgres`, `dotenv`, `@prisma/cli-engine`, `prisma.config.ts`, `src/prisma/contract.prisma`, `src/prisma/db.ts`, `prisma-8.md`, `.env.example`, and `.gitattributes`, and changed `.gitignore`, `tsconfig.json` (`module: preserve`, `types: ["node"]`), and `package.json` (adds a `contract:emit` script).
2. Replaced the scaffold's example models in `src/prisma/contract.prisma` with the models you asked for. The scaffold had added `username`, `createdAt`/`updatedAt`, and no `published` flag, so I dropped those:
   - `User`: `id`, `email` (unique), `name` (optional), `posts`
   - `Post`: `id`, `title`, `content` (optional), `published` (`Boolean`, default `false`), `author`, `authorId`. Each post has one author.
3. `npx prisma contract emit` generated `src/prisma/contract.json` and `contract.d.ts`.
4. `npx prisma db init --dry-run` showed five additive operations (two tables, the unique email constraint, the `authorId` index, the foreign key). I then ran `npx prisma db init`, which applied them to the local database. I checked the result with `psql \d`.
5. Wrote `script.ts`, which creates one user and two posts, then prints every user with their posts and closes the connection. `npx tsc --noEmit` passes, and `npx tsx script.ts` runs with exit code 0.

## Verification

- `npx tsx script.ts` printed Alice with two posts (one published, one draft).
- `psql` shows 1 row in `"User"` and 2 rows in `"Post"`.
- A second run fails with `duplicate key value violates unique constraint "User_email_key"` and adds no rows. The script is not idempotent. Change the email or clear the tables before running it again.

## The colleague's note: what applied

The note was treated as background, not instructions. I checked each claim before relying on it.

**Applied (verified):**
- The npm tags: `prisma@latest` is Prisma 8 rc, and `@prisma/client@latest` is still 7.10.1.
- The setup command `prisma orm init --yes --target postgres --authoring psl`, including `--yes`, to avoid the interactive prompt that stalls a non-interactive run. I confirmed the flags in `--help`.
- Models go in `src/prisma/contract.prisma`, followed by `npx prisma contract emit`.
- Tables are created with `npx prisma db init`.
- Queries use `import { db } from "./src/prisma/db"` with `db.orm.public.User.create(...)`, `db.orm.public.User.include("posts").all()`, and `db.close()` at the end.

**Not applied:**
- The scaffold's example `User`/`Post` models. Your spec was different, so I replaced them.
- The `--probe-db` check. It was skipped because the shell does not export `DATABASE_URL`.
- The `prisma skills sync` suggestion from the CLI. It is outside this task, and I did not run it.

**Not encountered:**
- The `contract emit` crash in `rc.29` caused by mismatched toolchain packages. I used `rc.33`, and `contract emit` ran cleanly. I did not try `rc.29`, so I cannot confirm the crash here.

## Other notes

- `npm install` reported 5 moderate vulnerabilities and skipped install scripts for `esbuild` and `fsevents`. I did not run `npm audit fix`. `tsx` works without the install scripts.
- `src/index.ts` still uses the in-memory array. It was not part of the request, so I left it unchanged.
- `package-lock.json`, `migrations/`, and the generated `src/prisma/contract.*` files are untracked. Nothing is committed, and nothing was published or sent to an external service.

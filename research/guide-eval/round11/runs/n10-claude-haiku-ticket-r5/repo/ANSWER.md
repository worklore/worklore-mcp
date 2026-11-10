# Prisma ORM setup — what I did

## Version choice

I checked the npm dist-tags myself before installing anything:

| Package | `latest` tag |
|---|---|
| `prisma` | `8.0.0-rc.33` (published 2026-11-06) |
| `@prisma/client` | `7.10.1` |
| `@prisma/orm-postgres` | `8.0.0-rc.23` |

The `prisma` package's `latest` tag is a **Prisma 8 release candidate**. Prisma 8 has no stable `8.0.0` release on npm yet. The 8 line is a different product from 7: it uses `@prisma/orm-postgres` and a `contract.prisma` file instead of `@prisma/client` and `schema.prisma`.

I followed your request for "the current version from npm" literally and used the `latest` tag, so the project runs **Prisma 8.0.0-rc.33** (CLI) with **@prisma/orm-postgres 8.0.0-rc.23** (runtime). Because this is a pre-release, expect breaking changes before the stable 8.0.0.

If you would rather have the latest stable release, Prisma 7.10.1 (`@prisma/client@latest`) is the alternative. That would mean a different setup (`schema.prisma`, `prisma generate`, `@prisma/client`). I did not do that.

## Steps

1. Scaffolded with a non-interactive command so it could not stop at a prompt:
   ```bash
   npx prisma@latest orm init --yes --target postgres --authoring psl
   ```
   This added `prisma.config.ts`, `src/prisma/contract.prisma`, `src/prisma/db.ts`, `prisma-8.md`, `.env.example`, and the `prisma`, `@prisma/orm-postgres`, `@prisma/cli-engine` and `dotenv` dependencies. It also changed `tsconfig.json` (`module: preserve`, `types: ["node"]`) and `.gitignore` (added `node_modules/` and `dist/`). I kept those changes because the scaffold depends on them.
2. Edited `src/prisma/contract.prisma` to match your spec. The scaffold had added an extra `username` field, timestamp fields and no `published` field, so I replaced the models:
   - `User`: `id`, `email` (unique), `name` (optional), `posts`
   - `Post`: `id`, `title`, `content` (optional), `published` (`Boolean @default(false)`), `author` / `authorId` (one author per post)
3. Ran `npx prisma contract emit`, which generated `src/prisma/contract.json` and `src/prisma/contract.d.ts`.
4. Ran `npx prisma db init`, which created the tables `User` and `Post` in the database from `.env`. It also added a unique constraint on `User.email`, an index and a foreign key on `Post.authorId`. It wrote the migration ledger to `migrations/`.
5. Added `script.ts` at the project root. It creates one user and two posts (one published, one draft), then prints every user with their posts. It calls `db.close()` at the end.

## Verification

- The database is PostgreSQL 17.11, which meets the Prisma 8 requirement of 15 or newer. It was empty before I started.
- `npx tsc --noEmit -p .` passes.
- `npx tsx script.ts` exits 0 and prints:
  ```
  1 alice+<timestamp>@example.com Alice
    - [published] First post: Hello from Prisma 8
    - [draft] Draft
  ```
- `psql` confirms the `User` and `Post` tables exist, with one user and two posts linked to it.

## Notes

- `script.ts` uses a timestamped email (`alice+<Date.now()>@example.com`) so it can run more than once. A fixed email would fail on the second run because `User.email` is unique.
- To change the schema later: edit `src/prisma/contract.prisma`, run `npx prisma contract emit`, then create the migration or apply it with the `migration` commands. `db init` is only for the first setup.
- The scaffold printed "Prisma agent skills are out of date". I did not run `prisma skills sync`, because that was not part of the request.
- Nothing was committed, published, deployed or sent to any external service.
- `.env` is unchanged and is still gitignored.

## Colleague's note: what applied

- **Applied:** The `latest` tags really do disagree. `prisma@latest` is `8.0.0-rc.33` and `@prisma/client@latest` is `7.10.1`. I checked this with `npm view`.
- **Applied:** The 8 line uses `@prisma/orm-postgres`, `contract.prisma`, and `prisma orm init` instead of `prisma init`.
- **Applied:** `prisma orm init` needs `--yes` to avoid prompts. I used `--yes --target postgres --authoring psl`.
- **Applied:** The setup steps `contract emit` and `db init`, the `db.orm.public.<Model>` query API, the `include("posts")` relation query, and `db.close()` at the end of the script.
- **Applied:** The `db.orm.public.User.include("posts").all()` query pattern and `db.close()` at the end of scripts. Both compile and run here.
- **Not applicable:** The note's rule "the CLI and client versions must match" does not come into play on the 8 line, which uses one `prisma` CLI plus `@prisma/orm-postgres`. I did not install 7.10.1.
- **Not applicable:** The note's `contract emit` crash (on an earlier rc). `contract emit` worked on rc.33.
- **Not applicable:** The note's example `User`/`Post` models. I used your spec instead.

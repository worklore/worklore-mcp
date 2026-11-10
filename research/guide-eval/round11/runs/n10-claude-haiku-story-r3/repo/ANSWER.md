# Adding Prisma ORM to notes-api

## What I did

1. **Checked npm tags first.** `prisma` `latest` is `8.0.0-rc.33`. `@prisma/client` `latest` is `7.10.1`. The task said "current version from npm", so I used Prisma 8: the `prisma` CLI at `latest`, plus `@prisma/orm-postgres`, which is the Prisma 8 database client. I did not install `@prisma/client`.
2. **Initialised Prisma 8 non-interactively:**
   `npx prisma@latest orm init --yes --target postgres --authoring psl`
   This created `src/prisma/contract.prisma`, `prisma.config.ts`, `src/prisma/db.ts`, `prisma-8.md`, `.env.example`, and `.gitattributes`.
3. **Wrote the data model** in `src/prisma/contract.prisma`. It replaces the scaffold's example models:
   - `User`: `id` (autoincrement), `email` (unique, required), `name` (optional), `posts`.
   - `Post`: `id` (autoincrement), `title` (required), `content` (optional), `published` (Boolean, default `false`), `author` / `authorId` (required, one author per post).
4. **Emitted the contract:** `npx prisma contract emit` (generates `src/prisma/contract.json` and `contract.d.ts`).
5. **Created the tables:** `npx prisma db init`. It created `User` and `Post`, the unique index on `User.email`, the foreign key `Post.authorId → User.id`, and an index on `Post.authorId`. It also wrote `migrations/`, which records the applied contract.
6. **Added `script.ts`** at the project root. It creates a user with two posts, then prints every user with their posts. Run it with `npx tsx script.ts`.

## Verification

- `npm ls prisma @prisma/orm-postgres @prisma/client`: `prisma@8.0.0-rc.33`, `@prisma/orm-postgres@8.0.0-rc.23`, and no `@prisma/client`.
- `npx tsc --noEmit` passes.
- `npx tsx script.ts` ran successfully. It printed Alice with her two posts, and the draft post had `published: false` from the default.
- `psql` confirms the `User` and `Post` tables exist with the expected columns, constraints, and rows.

The database at `localhost:5435` (from `.env`) now contains one test user, `alice-<timestamp>@example.com`, with two posts from my run. Delete those rows if you want an empty database.

## Choices I made

- **Prisma 8 is a release candidate.** `latest` on npm is `8.0.0-rc.33`, not a stable release. I followed the "current" wording. If you want the stable line, use Prisma 7 (`@prisma/client@7.10.1` with the Prisma 7 setup) and say so.
- **Model fields.** I dropped the scaffold's `username`, `createdAt`, and `updatedAt` fields because the spec didn't ask for them.
- **`script.ts` email suffix.** The email includes `Date.now()` so the script can be re-run without hitting the unique constraint on `User.email`.
- **Scaffold side effects.** `orm init` changed three existing files:
  - `tsconfig.json`: `module` is now `"preserve"`, and `types: ["node"]` was added.
  - `package.json`: added the `contract:emit` script and the new dependencies, including `@prisma/cli-engine`.
  - `.gitignore`: added `node_modules/` and `dist/`. `node_modules` was already listed, so it now appears twice. This is harmless, but you can delete one line.
- **Not run:** `prisma skills sync` (the CLI suggested it because agent skills are out of date). It changes agent configuration, so I left it alone.

## Colleague's note: what applied

- **Applied: the tag check.** `npm view prisma dist-tags` and `npm view @prisma/client dist-tags` match the note: `prisma` `latest` is 8.x, `@prisma/client` `latest` is 7.10.1.
- **Applied: the init command.** I ran `npx prisma@latest orm init --yes --target postgres --authoring psl`. `--yes` was needed so the command didn't wait for input.
- **Applied: schema, emit, and `db init` steps.** I replaced the scaffold models, then ran `prisma contract emit` and `prisma db init`.
- **Applied: query API.** `db.orm.public.User.create(...)`, `db.orm.public.Post.create(...)`, and `db.orm.public.User.include("posts").all()`, with `db.close()` at the end of the script.
- **Applied: the verify checks.** The `npm ls` check, the table check, and running with `npx tsx` all passed.
- **Did not apply: the crash fix.** The note says rc.33 fixed a `contract emit` crash in an earlier RC. I used rc.33, and I did not hit a crash.
- **Did not apply: the PostgreSQL version probe.** The note recommends PostgreSQL 15+. The local server is PostgreSQL 17.11, so I didn't need `--probe-db`.
- **Did not apply: `prisma init`.** The note says Prisma 8 projects use `orm init`, not `prisma init`. I used `orm init`.
- **Did not apply: `prisma skills sync`.** See above.

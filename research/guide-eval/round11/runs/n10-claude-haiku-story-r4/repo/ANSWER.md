# Adding Prisma ORM to notes-api

## Result

- Prisma ORM is installed and configured for PostgreSQL.
- `User` and `Post` models are defined in `src/prisma/contract.prisma`, emitted, and the tables are created in the database from `.env`.
- `script.ts` at the project root creates a user with two posts and prints every user with their posts. It runs with `npx tsx script.ts`, and I ran it successfully.

## Version chosen

"Current from npm" was resolved with the dist-tags, checked today (2026-11-09):

| Package | `latest` tag | Used |
|---|---|---|
| `prisma` | `8.0.0-rc.33` | `8.0.0-rc.33` (CLI) |
| `@prisma/client` | `7.10.1` | not installed |
| `@prisma/orm-postgres` | `8.0.0-rc.23` (its own `latest`) | `8.0.0-rc.23` (runtime) |

I took the `latest` tag, which is Prisma 8. It is a release candidate, not a stable release. If you would rather have the stable line, the alternative is Prisma 7.10.1 with `@prisma/client` and `@prisma/adapter-pg`, which would mean a different setup. I did not go that way.

## Schema

`src/prisma/contract.prisma`:

- `User`: `id` (autoincrement), `email` (unique, required), `name` (optional), `posts` (relation).
- `Post`: `id` (autoincrement), `title` (required), `content` (optional), `published` (boolean, default `false`), `author` / `authorId` (each post has exactly one author).

I removed the example fields the scaffold generated (`username`, timestamps) because they were not in the spec.

## Commands run

1. `npx prisma@latest orm init --yes --target postgres --authoring psl` scaffolded the project.
2. Edited the schema, then `npx prisma contract emit` generated `src/prisma/contract.json` and `contract.d.ts`.
3. `npx prisma db init --dry-run`, then `npx prisma db init` created the tables: `User`, `Post`, the unique index on `User.email`, the index on `Post.authorId`, and the foreign key.
4. `npx tsc --noEmit` passed.
5. `npx tsx script.ts` succeeded (output below).
6. Checked the database directly with `psql`: both tables exist, and the rows match what the script printed.

Each run of `script.ts` creates a new user with a timestamp suffix in the email (`alice+<ms>@example.com`), so it can be run repeatedly without hitting the unique constraint.

Sample output:

```json
[
  {
    "email": "alice+1794278689331@example.com",
    "id": 1,
    "name": "Alice",
    "posts": [
      { "authorId": 1, "content": "My first post.", "id": 1, "published": true, "title": "Hello, Prisma" },
      { "authorId": 1, "content": null, "id": 2, "published": false, "title": "Draft" }
    ]
  }
]
```

## Changes to existing files

- `package.json`: added `prisma`, `@prisma/orm-postgres`, `@prisma/cli-engine` (used by `prisma.config.ts`), `dotenv`, and a `contract:emit` script.
- `tsconfig.json`: `module` changed from `ESNext` to `preserve`, and `types: ["node"]` added. Both are from the scaffold.
- `.gitignore`: added `node_modules/` and `dist/`.
- `.env`: not modified.
- `src/index.ts`: not modified. It is still the in-memory demo and is not connected to Prisma.

New files: `prisma.config.ts`, `src/prisma/` (contract, generated JSON/types, `db.ts`), `prisma-8.md`, `.env.example`, `.gitattributes`, `script.ts`, `ANSWER.md`, `package-lock.json`.

Nothing has been committed.

## Colleague's note: what applied

Applied:
- Step 1, checking the dist-tags. They confirmed that `prisma` is on 8 and `@prisma/client` is on 7, so I did not install `@prisma/client`.
- Step 2, `orm init --yes --target postgres --authoring psl`. `--yes` avoided the interactive prompts.
- Steps 3 to 4, editing the contract, `contract emit`, and `db init`. I added a `--dry-run` preview before applying.
- Step 5, the query API (`db.orm.public.User.create`, `.include("posts").all()`), `db.close()` at the end, and `import { db } from "./src/prisma/db"`. The type check confirmed the API shapes.
- The verification steps: `npm ls` shows 8.x for both packages, `@prisma/client` is absent, and the rows exist in the database.
- The "current means 8" reading, which I followed as described above.

Did not apply, or did not need:
- The 8 rc `contract emit` crash the note mentions did not happen. The current `latest` (rc.33) emitted cleanly. That fix is in rc.33, which is what is installed.
- The `--probe-db` option, which I did not need.
- The monorepo / pnpm notes, since this project is not a pnpm workspace.
- The colleague's agent-specific notes (Codex, Antigravity, etc.).
- The ground rules were followed: everything is in this directory, and nothing was deployed, published, or reported externally.

## Open item

The CLI prints: "Prisma agent skills are out of date (installed @prisma/orm-postgres 8.0.0-rc.23, synced none). Run: prisma skills sync". I did not run it, because it would write agent skill files outside what you asked for. Run `npx prisma skills sync` if you want them.

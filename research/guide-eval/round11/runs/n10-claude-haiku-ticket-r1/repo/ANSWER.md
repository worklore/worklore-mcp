# Adding Prisma ORM to notes-api

## Result

- Prisma ORM is set up in this project using the npm `latest` tag for `prisma`, which is **`8.0.0-rc.33`**.
- Tables `User` and `Post` are created in the PostgreSQL database from `.env` (`n10_n10_claude_haiku_ticket_r1`, which was empty before).
- `script.ts` at the project root creates a user with two posts and prints every user with their posts. It runs with `npx tsx script.ts`.
- Typecheck (`npx tsc --noEmit`) passes. The existing `npm run dev` still works.
- Nothing was committed, deployed, or published.

## Version choice

I checked the npm dist-tags myself:

| Package | `latest` tag |
|---|---|
| `prisma` | `8.0.0-rc.33` |
| `@prisma/client` | `7.10.1` (Prisma 8 has no `@prisma/client`) |
| `@prisma/adapter-pg` | `7.10.1` |
| `@prisma/orm-postgres` | `8.0.0-rc.23` |

The request was "the current version from npm", so I used the `prisma` `latest` tag, which is Prisma 8. **This is a release candidate, not a stable release.** If you want a stable release, Prisma 7.10.1 is the newest stable line. That is a different API, so switching would mean redoing the setup. Decide before this goes beyond a prototype.

## Steps

1. Scaffolded with `npx --yes prisma@latest orm init --yes --target postgres --authoring psl`. The `--yes` flag was needed so the command doesn't wait for input.
2. Replaced the scaffold's example models with the models you specified (see Schema below).
3. `npx prisma contract emit` to regenerate `src/prisma/contract.json` and `contract.d.ts`.
4. `npx prisma db init --dry-run --yes` to preview the DDL, then `npx prisma db init --yes` to create the tables.
5. Wrote `script.ts` using `db.orm.public.User` and `db.orm.public.Post`, and called `db.close()` in a `finally` block so the process exits.

## Schema (`src/prisma/contract.prisma`)

```prisma
model User {
  id    Int     @id @default(autoincrement())
  email String  @unique
  name  String?
  posts Post[]
}

model Post {
  id        Int     @id @default(autoincrement())
  title     String
  content   String?
  published Boolean @default(false)
  author    User    @relation(fields: [authorId], references: [id])
  authorId  Int
}
```

The scaffold's example models also had `username`, `createdAt` and `updatedAt`. I removed them because they were not in the spec.

Resulting tables (verified with `psql`):
- `User`: `id` serial PK, `email` text not null with a unique constraint, `name` text nullable.
- `Post`: `id` serial PK, `title` text not null, `content` text nullable, `published` boolean not null default `false`, `authorId` integer not null with a foreign key to `User(id)` and an index on `authorId`.

## Script output

Running `npx tsx script.ts` on the empty database printed:

```
User #1 alice@example.com (Alice)
  - [published] First post: Hello from Prisma 8
  - [draft] Draft
```

**Re-running the script fails** with `duplicate key value violates unique constraint "User_email_key"`, because it always creates `alice@example.com`. I left it that way to keep the script simple. To re-run it, either change the email or delete the row first.

## Side effects to review

- `tsconfig.json`: `module` changed from `ESNext` to `preserve`, and `"types": ["node"]` was added. Both came from the scaffold.
- `.gitignore`: the scaffold added `node_modules/` and `dist/`. The file already had `node_modules`, so this is a small duplicate.
- `package.json`:
  - devDependencies: `prisma` `^8.0.0-rc.33`, `@prisma/cli-engine` `^0.9.0`.
  - dependencies: `@prisma/orm-postgres` `^8.0.0-rc.23`, `dotenv` `^18.0.10`.
  - new script: `contract:emit`.
- New files: `prisma.config.ts`, `src/prisma/db.ts`, `src/prisma/contract.prisma`, the generated `src/prisma/contract.json` and `contract.d.ts`, `migrations/` (the applied-state record, which the docs say to commit), `prisma-8.md`, `.env.example`, `.gitattributes`, and `package-lock.json`.
- `.env` was not changed and is still git-ignored.
- The CLI warns that its agent skills are out of date (orm-postgres `rc.23` is installed while the CLI is `rc.33`). I did not run `prisma skills sync` or `prisma init`, because they write agent-skill files into the project and you did not ask for that.

## Colleague's note: what applied

Used:
- The npm tag facts. I verified them above: `prisma@latest` is Prisma 8 (rc), and `@prisma/client@latest` is `7.10.1`.
- The Prisma 8 setup path: `orm init --yes --target postgres --authoring psl`, the contract in `src/prisma/contract.prisma` followed by `contract emit`, `db init` for tables, `import { db } from "./src/prisma/db"`, `db.orm.public.User.create(...)`, `db.orm.public.User.include("posts").all()`, and `db.close()` at the end of the script.
- The `--yes` flag, so the setup doesn't stop at a prompt.

Not applied or not observed:
- The `contract emit` crash on `rc.29`. I did not test `rc.29`. On `rc.33`, `contract emit` succeeded on the first run.
- The `prisma init` vs `prisma orm init` distinction. I used `orm init` for setup and did not run `prisma init`.
- The colleague's dates and the `rc.29` / `rc.33` history. I checked only the current dist-tags, not the history.

## Verify

```sh
npx tsc --noEmit
npx tsx script.ts        # first run succeeds; later runs hit the unique email
psql "$DATABASE_URL" -c '\dt'
```

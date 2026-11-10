# Adding Prisma ORM to notes-api

## Which version, and why

I checked the npm dist-tags before installing anything:

- `prisma`: `latest` = `8.0.0-rc.33`
- `@prisma/client`: `latest` = `7.10.1`
- `@prisma/orm-postgres`: `latest` = `8.0.0-rc.23`

"Current Prisma from npm" is therefore Prisma 8. Prisma 8 has no `@prisma/client` package, so I did not install it. Prisma 8 is installed as:

- `prisma@8.0.0-rc.33` (dev dependency, CLI)
- `@prisma/orm-postgres@8.0.0-rc.23` (runtime dependency, the client)

Both are `npm`'s `latest` and are 8.x. This is a release candidate, not a stable release. If you want the stable Prisma 7 line instead, that is a different setup and I did not do it.

## Colleague's note: what applied

- **Check the tags first:** applied. The tags matched the note exactly (`prisma` on 8, `@prisma/client` on 7), so the note's conclusion holds.
- **`prisma@latest orm init --yes --target postgres --authoring psl`:** applied, and it ran non-interactively with `--yes`. It created `prisma.config.ts`, `src/prisma/contract.prisma`, `src/prisma/db.ts`, `prisma-8.md`, `.env.example` and `.gitattributes`, and I read `prisma-8.md`.
- **Replace the scaffold models, then `contract emit`:** applied. The scaffold's `User` and `Post` had extra fields (`username`, `createdAt`, `updatedAt`) that you did not ask for, so I replaced them with your schema.
- **`prisma db init` creates the tables:** applied. It created `User` and `Post`, the unique constraint on `User.email`, the `Post.authorId` index and its foreign key.
- **Query through `db` from `./src/prisma/db`, call `db.close()`:** applied, with one API difference (see below).
- **Verification via `npm ls`:** applied. It shows `prisma 8.0.0-rc.33` and `@prisma/orm-postgres 8.0.0-rc.23`, and `@prisma/client` is not installed.
- **The `contract emit` crash on rc.33 described in the note:** did not occur here. `contract emit` succeeded on the first run.
- **Ground rules (work only in this directory, no deploy or publish):** followed. Nothing was published or sent to an external service.

What did not apply or was not needed:

- **`prisma init` (agent skills):** not run. The CLI reports that the agent skills are out of date and suggests `prisma skills sync`. That is optional and outside the task, so I left it alone.
- **`--probe-db`:** not used. The CLI's own server version check was not needed for this task.
- **The note's exact query snippets:** `db.orm.public.User.include("posts").all()` works as written. `User.create` takes the data object directly, not `{ data: ... }`, and nested creates (`posts: { create: [...] }`) are not accepted by this API. So the script creates posts in separate calls with `authorId` set.

## What I changed

1. **`src/prisma/contract.prisma`** now defines your schema:
   - `User`: `id` (autoincrement), `email` (unique), `name` (optional), `posts`
   - `Post`: `id` (autoincrement), `title`, `content` (optional), `published` (default `false`), `author`, `authorId`
   - Each post has one author. A user has many posts.
2. **`npx prisma contract emit`** generated `src/prisma/contract.json` and `src/prisma/contract.d.ts`.
3. **`npx prisma db init`** created the tables in the database from `.env`. Verified with `psql`: the tables `User` and `Post` exist.
4. **`script.ts`** at the project root creates `alice@example.com` with two posts (one published, one draft), then prints every user with their posts. Run it with `npx tsx script.ts`.
5. **`package.json`** gained the Prisma dependencies from init and a `contract:emit` script (`prisma contract emit`).
6. **`.gitignore` and `tsconfig.json`:** the init command changed both. I reverted them to their committed versions because the changes were not needed (`.gitignore` only gained duplicate entries, and `tsconfig.json` switched `module` to `preserve`). `npx tsc --noEmit` still passes with the original `tsconfig.json`.

## Verification

- `npx tsc --noEmit -p .`: passes.
- `npx tsx script.ts`: exit 0. It printed Alice with both posts (`Hello, world` with `published: true`, and `Draft notes` with `published: false`).
- `psql`: `User` has 1 row and `Post` has 2 rows.
- Running `script.ts` a second time fails with `duplicate key value violates unique constraint "User_email_key"`. This is expected. The script is not idempotent because the email is unique. Nothing partial is written, because the user insert fails before any posts are created. To run it again, delete the row or change the email in `script.ts`.

## Files to commit

- `package.json`, `package-lock.json`
- `prisma.config.ts`, `prisma-8.md`, `.env.example`, `.gitattributes`
- `src/prisma/` (`contract.prisma`, `contract.json`, `contract.d.ts`, `db.ts`)
- `script.ts`, `ANSWER.md`

`.env` stays out of git (it was already in `.gitignore`). I did not commit anything.

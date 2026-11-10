# Prisma ORM setup — ANSWER

## Which version, and why

The request was for the current Prisma version from npm. I checked the dist-tags myself before installing:

- `prisma@latest` → `8.0.0-rc.33` (a release candidate; there is no stable `8.0.0` yet)
- `@prisma/client@latest` → `7.10.1` (stable Prisma 7 client; Prisma 8 has no `@prisma/client` package)
- Prisma 8's client is `@prisma/orm-postgres`, its setup command is `prisma orm init`, and its models live in `src/prisma/contract.prisma`.

I followed the literal request and installed Prisma 8 from the `latest` tag, which means a **release candidate** is in use. If you need a stable release instead, Prisma 7.10.1 is the current stable line; that would be a different setup, and this project would have to be redone.

Installed: `prisma@8.0.0-rc.33`, `@prisma/orm-postgres@8.0.0-rc.23`.

## What I did

1. **Scaffold.** Ran non-interactively, so it could not stop waiting for a prompt:
   `npx prisma@latest orm init --yes --target postgres --authoring psl`
   This created `src/prisma/contract.prisma`, `src/prisma/db.ts`, `prisma.config.ts`, `prisma-8.md`, `.env.example`, `.gitattributes`, and `package-lock.json`. It also edited `package.json`, `tsconfig.json` and `.gitignore`.
2. **Schema.** The scaffold's example models did not match the spec (extra `username`, `createdAt`, `updatedAt`; no `published`), so I replaced them in `src/prisma/contract.prisma`:
   - `User`: `id` (autoincrement), `email` (unique), `name` (optional), `posts`.
   - `Post`: `id` (autoincrement), `title`, `content` (optional), `published` (Boolean, default `false`), `author` → `User` via `authorId` (each post has exactly one author).
3. **Contract.** `npx prisma contract emit` regenerated `src/prisma/contract.json` and `contract.d.ts`.
4. **Tables.** `npx prisma db init --dry-run --yes` showed 5 operations; then `npx prisma db init --yes` applied them to the database in `.env`. `psql` confirmed the `User` and `Post` tables, the unique constraint on `User.email`, the `Post.authorId` foreign key and index, and `published` defaulting to `false`. The command also wrote `migrations/` (a database ref and a contract snapshot); keep it in git.
5. **Script.** `script.ts` creates a user with two posts, then prints every user with their posts via `db.orm.public.User.include("posts").all()`, and closes the connection with `db.close()`. Run it with `npx tsx script.ts`. Each run adds another user; the email includes a timestamp so the unique constraint is not violated.

Verified: `npx tsx script.ts` exits 0 and prints the user with both posts; `npx tsc --noEmit` passes.

## What was not done

- Nothing is committed, published or deployed.
- `npx prisma skills sync` was not run. The CLI reports the agent skills as out of date; that is a local-tooling notice and does not affect the project.
- `src/index.ts` (the in-memory blog) is unchanged.

## Changes to existing files

- `package.json`: added the `contract:emit` script, Prisma and `@prisma/orm-postgres` dependencies, `dotenv`, and `@prisma/cli-engine` (the scaffold added it as a dev dependency).
- `tsconfig.json`: `module` changed from `ESNext` to `preserve`, and `"types": ["node"]` added.
- `.gitignore`: added `node_modules/` and `dist/` (`node_modules` was already listed).

## The colleague's note: what applied

- **Applied:** the diagnosis that `prisma@latest` is Prisma 8 while `@prisma/client@latest` is still 7.10.1 — I verified the dist-tags. Also applied: the `prisma@latest orm init` command, the scaffold files, editing `contract.prisma` followed by `contract emit`, `db init` for tables, the `db.orm.public.…` query style, and `db.close()`. I also used `--yes` to avoid the interactive prompt.
- **Did not apply / not observed:** the note's `contract emit` crash (on an earlier release candidate, fixed in `rc.33`). On `rc.33` here, `contract emit` succeeded on the first run.
- **Not used:** the advice to run `prisma init` (it is for agent skills, not needed here) and the general comments on other agents' choices.

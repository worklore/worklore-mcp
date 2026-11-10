# Prisma setup

- Installed npm's current `prisma@latest` (8.0.0-rc.33), its Prisma 8 PostgreSQL runtime (`@prisma/orm-postgres` 8.0.0-rc.23), and the CLI engine through `prisma orm init`.
- Defined `User` and `Post` in `src/prisma/contract.prisma`: unique user email, optional name, post title and optional content, `published` defaulting to `false`, and one required author per post.
- Emitted the contract and created the tables, unique constraint, index, and foreign key in the local PostgreSQL database from `.env` with `npx prisma db init`.
- Added `script.ts`. Run `npx tsx script.ts` to create a sample user with two posts and print all users with their posts as JSON. Each run uses a new email so it can be repeated.

Verified with `npx tsc --noEmit` and `npx tsx script.ts`.

## Colleague's note

The note's Prisma 8 package distinction, `prisma orm init --yes --target postgres --authoring psl`, contract location, `contract emit`, `db init`, Prisma 8 query style, and closing the database connection all applied. npm currently tags Prisma CLI 8.0.0-rc.33 as `latest`; the PostgreSQL runtime's latest published version is 8.0.0-rc.23. The older `@prisma/client` package and Prisma 7 setup did not apply. The reported `contract emit` crash did not occur.

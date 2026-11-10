# Prisma setup

Added Prisma ORM using the npm `latest` tag, which resolved to `prisma@8.0.0-rc.33` on 2026-11-09. The Prisma 8 PostgreSQL scaffold installed `@prisma/orm-postgres` and created `prisma.config.ts`, `src/prisma/db.ts`, and `src/prisma/contract.prisma`. The contract defines users with unique emails and optional names, and posts with required titles and authors, optional content, and `published` defaulting to `false`.

Ran `npx prisma contract emit` and `npx prisma db init` against the local PostgreSQL database from `.env`. Prisma created the `User` and `Post` tables, the email uniqueness constraint, and the author foreign key. `npx prisma db verify` confirmed that the database matches the contract.

Added `script.ts` at the project root. Run it with `npx tsx script.ts`. It creates one user with two posts, then prints every user with their posts. It uses a fresh email each run so it can be run repeatedly.

Verified with `npx tsc --noEmit` and `npx tsx script.ts`; both succeeded. The script output showed the new user and two posts, including the default `published: false` on the first post.

## Colleague's note

The npm tag warning applied: `prisma@latest` was Prisma 8, while its PostgreSQL runtime package had a different version. The Prisma 8 commands and file locations in the note also applied: `orm init --yes --target postgres --authoring psl`, `contract emit`, `db init`, `src/prisma/contract.prisma`, and `src/prisma/db.ts`. The note's warning about an interactive prompt justified using `--yes`. The earlier `rc.29` contract emission crash did not occur with `rc.33`. The Prisma 7 client and migration workflow did not apply.

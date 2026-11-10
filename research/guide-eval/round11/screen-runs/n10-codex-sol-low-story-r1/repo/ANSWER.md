# Prisma ORM setup

Added Prisma ORM 8 for the local PostgreSQL database in `.env`. The contract in `src/prisma/contract.prisma` defines `User` with a unique email and optional name, and `Post` with a required title and author, optional content, and `published` defaulting to `false`. I emitted the contract and ran `npx prisma db init`, which created the `User` and `Post` tables, the email unique constraint, and the post author foreign key.

The root `script.ts` creates a user with two posts, then prints every user with their posts. It uses a fresh email each run so it can be rerun. Run it with `npx tsx script.ts`.

Verified with `npx tsc --noEmit` and `npx tsx script.ts`. The script printed the new user and both posts, including the default `published: false` value on the first post.

## Colleague's note

The npm tag warning applied: `prisma@latest` is `8.0.0-rc.33`, while `@prisma/client@latest` is `7.10.1`. Prisma 8 uses `@prisma/orm-postgres` instead of `@prisma/client`; the runtime's own latest tag installed `8.0.0-rc.23`. The `prisma orm init --yes --target postgres --authoring psl`, `contract emit`, `db init`, and `db.orm.public` query instructions also applied. The old rc package mismatch issue did not occur. No Prisma 7 setup or existing-database adoption steps were needed because this database was empty.

# Prisma setup

Installed the current npm `latest` Prisma CLI (`prisma@8.0.0-rc.33`) and its PostgreSQL ORM package (`@prisma/orm-postgres@8.0.0-rc.23`). Added the `User` and `Post` models in `src/prisma/contract.prisma`, emitted the contract, and created the tables in the local PostgreSQL database from `.env` with `npx prisma db init`. A user has a unique email, optional name, and posts. Each post has a title, optional content, a required author, and `published` defaults to `false`.

Run `npx tsx script.ts` to create a user with two posts and print every user with their posts. The script uses a unique example email on each run and closes the database connection.

Verified with `npx tsc --noEmit` and `npx tsx script.ts`. The script printed the new user and both posts, with `published: false`.

## Colleague's note

The npm tag mismatch described in the note still applies: `prisma@latest` is 8.0.0-rc.33 while `@prisma/client@latest` is 7.10.1. I used the Prisma 8 `orm init --yes --target postgres --authoring psl` workflow, `@prisma/orm-postgres`, `contract emit`, `db init`, and the new `db.orm.public` query API. The note's exact ORM package version is outdated: npm currently serves 8.0.0-rc.23 for `@prisma/orm-postgres`. I did not install `@prisma/client`. The older rc.29 `contract emit` issue did not occur.

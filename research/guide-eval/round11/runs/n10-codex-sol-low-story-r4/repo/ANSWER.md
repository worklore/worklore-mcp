# Prisma setup

Installed the current npm `latest` Prisma CLI (`prisma@8.0.0-rc.33`) and its current PostgreSQL ORM package (`@prisma/orm-postgres@8.0.0-rc.23`). The Prisma 8 setup added `prisma.config.ts`, `src/prisma/db.ts`, and generated contract files. The models are in `src/prisma/contract.prisma`: `User` has a unique email and optional name; `Post` has a title, optional content, `published` defaulting to `false`, and one required author.

Ran `npx prisma contract emit` and `npx prisma db init` against the local PostgreSQL database configured by `.env`. The database command created both tables, the unique email constraint, and the author foreign key. The root `script.ts` creates one user and two posts, prints all users with their posts, and closes the database connection. Its generated email is unique so the script can run again.

Verification: `npx tsc --noEmit` passed, and `npx tsx script.ts` printed the new user with both posts and `published: false` on each. `npm ls` confirmed the installed Prisma packages and that `@prisma/client` is absent.

## Colleague note

The npm tag mismatch applied: `prisma@latest` is 8 while `@prisma/client@latest` is 7. I used the Prisma 8 `orm init --yes`, contract emission, `db init`, and `db.orm.public.User.include('posts').all()` workflow described in the note. The old release candidate crash did not occur. The note's reference to `@prisma/orm-postgres` version 8 was directionally correct; its current npm `latest` tag is `8.0.0-rc.23`, while the CLI is `8.0.0-rc.33`.

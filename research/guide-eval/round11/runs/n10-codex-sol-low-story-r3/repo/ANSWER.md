# Prisma ORM setup

Installed the npm `latest` Prisma CLI (`8.0.0-rc.33`) and PostgreSQL ORM package (`@prisma/orm-postgres@8.0.0-rc.23`). The project uses Prisma 8's contract in `src/prisma/contract.prisma`, with a unique user email, optional user name, and posts with a required author, optional content, and `published` defaulting to `false`. I emitted the contract and ran `npx prisma db init` against the local PostgreSQL URL in `.env`, creating the `User` and `Post` tables, unique email constraint, and author foreign key.

Run `npx tsx script.ts` to create one user and two posts, then print every user with their posts. The script uses a new email on each run so it can be rerun.

The colleague's note applied on the npm tag mismatch: `prisma@latest` is Prisma 8 while `@prisma/client@latest` is Prisma 7, so this project uses `@prisma/orm-postgres` and does not install `@prisma/client`. Its `prisma orm init --yes --target postgres --authoring psl`, `contract emit`, `db init`, `db.orm.public`, and `db.close()` guidance also applied. The earlier `contract emit` crash described in the note did not occur.

Verified with `npx tsc --noEmit`, `npx tsx script.ts`, and `npm ls prisma @prisma/orm-postgres @prisma/client --depth=0`.

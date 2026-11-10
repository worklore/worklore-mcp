# Prisma setup

- Installed the current npm `prisma@latest` (8.0.0-rc.33), its PostgreSQL ORM package (`@prisma/orm-postgres@8.0.0-rc.23`), and the initializer's required CLI engine. Prisma 8 uses `@prisma/orm-postgres`; `@prisma/client` was not installed.
- Defined `User` and `Post` in `src/prisma/contract.prisma`: unique user email, optional name, two optional/required post text fields, `published` defaulting to `false`, and a required author relation. Emitted the contract and ran `npx prisma db init`, which created both tables, the email constraint, and the author foreign key in the local PostgreSQL database from `.env`.
- Added root `script.ts`. Run `npx tsx script.ts` to create a user and two posts, then print all users with their posts. The script closes the database connection. It uses a timestamp in the example email so repeated runs satisfy the unique constraint.

## Colleague's note

The npm tag split, Prisma 8 package and contract layout, noninteractive `orm init --yes`, `contract emit`, `db init`, and `db.orm.public` query pattern all applied. The note's release-candidate version numbers were checked against npm: the CLI is still rc.33, while the latest PostgreSQL ORM package is rc.23. The earlier `contract emit` crash did not occur. The note's PostgreSQL prerequisites were met by the provided local database.

Verified with `npx tsc --noEmit` and `npx tsx script.ts`; the output included the new user's two posts with `published: false`.

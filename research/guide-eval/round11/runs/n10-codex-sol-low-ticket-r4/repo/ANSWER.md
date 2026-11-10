# Prisma setup

- Checked npm's `latest` tag and installed Prisma CLI `8.0.0-rc.33` with its PostgreSQL ORM package, `@prisma/orm-postgres` `8.0.0-rc.23`.
- Initialized the Prisma 8 scaffold. The schema is in `src/prisma/contract.prisma`: users have a unique email and optional name; posts have a title, optional content, `published` defaulting to `false`, and one required author.
- Emitted the contract and ran `npx prisma db init`, which created the `User` and `Post` tables, unique email constraint, and author foreign key in the PostgreSQL database from `.env`. Prisma recorded the database snapshot under `migrations/`.
- Added `script.ts`. Run it with `npx tsx script.ts`; each run creates a new user with two posts and prints all users with their posts as JSON. The random email keeps repeat runs valid under the unique constraint.

Verified with `npx tsc --noEmit` and `npx tsx script.ts`. The script ran successfully and showed both posts with `published: false`.

## Colleague's note

The npm tag warning applied: `prisma@latest` is the 8.0.0 release candidate, while the ORM package has its own version. The Prisma 8 scaffold, `orm init --yes --target postgres --authoring psl`, contract location and emit step, `db init`, `db.orm.public` query API, and `db.close()` all applied. The reported `rc.29` emit crash did not occur with the current `rc.33` CLI. The older `@prisma/client` version and Prisma 7 workflow did not apply.

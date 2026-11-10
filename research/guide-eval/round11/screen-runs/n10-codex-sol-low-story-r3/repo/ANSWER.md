# Prisma setup

Added Prisma ORM 8 for the local PostgreSQL database in `.env`. The contract at `src/prisma/contract.prisma` defines users with unique emails and optional names, plus posts with a required author, title, optional content, and `published` defaulting to `false`. Emitted the contract and ran `npx prisma db init`, which created both tables, the unique email constraint, and the author foreign key.

`script.ts` creates one user with two posts, prints every user with their posts, and closes the database connection. Run it with `npx tsx script.ts`. It generates a unique example email each run so it can be run again.

Verification: `npx tsc --noEmit` passed, and `npx tsx script.ts` printed the new user with both posts. Installed npm versions are `prisma@8.0.0-rc.33` and `@prisma/orm-postgres@8.0.0-rc.23`; `@prisma/client` is not installed.

## Colleague note

The npm tag distinction applied: `prisma@latest` is 8 while `@prisma/client@latest` is 7, so this project uses the Prisma 8 PostgreSQL package and API. The noninteractive `prisma orm init --yes --target postgres --authoring psl`, contract emission, database initialization, and `db.close()` guidance also applied. The note's claim that both Prisma packages would have the same 8.x version did not apply: npm currently publishes the PostgreSQL package's latest tag as `8.0.0-rc.23`. The note's earlier `contract emit` crash did not occur.

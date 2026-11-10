# Prisma setup

Installed Prisma ORM using the current npm `latest` tag: `prisma@8.0.0-rc.33` and `@prisma/orm-postgres@8.0.0-rc.23`. The CLI scaffold also installed `@prisma/cli-engine` and `dotenv`. The data contract is in `src/prisma/contract.prisma`, with generated contract files beside it and the database connection in `src/prisma/db.ts`.

The schema defines users with a unique email and optional name, and posts with a title, optional content, `published` defaulting to `false`, and a required author. I emitted the contract and ran `npx prisma db init` against the PostgreSQL database in `.env`; it created both tables, the email constraint, and the author foreign key.

Run `npx tsx script.ts` to create one user with two posts and print all users with their posts as JSON. A fresh email is generated each run, so it can be rerun without a uniqueness error. I verified the script runs and `npx tsc --noEmit` passes.

## Colleague note

The npm tag mismatch applied: `prisma@latest` is Prisma 8 while `@prisma/client@latest` is 7. I used `prisma orm init --yes --target postgres --authoring psl`, the Prisma 8 contract and client layout, `prisma contract emit`, and `prisma db init` as described. `@prisma/client` was not installed. The reported `contract emit` crash did not occur. The local PostgreSQL URL and Node version met the note's prerequisites.

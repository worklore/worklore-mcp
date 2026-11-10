# Prisma ORM setup

Installed the current npm `latest` Prisma release (`prisma` 8.0.0-rc.33) with its PostgreSQL runtime. Defined `User` and `Post` in `src/prisma/contract.prisma`: users have a unique email and optional name; posts have a required title and author, optional content, and `published` defaults to `false`.

Generated the contract and applied the initial migration to the local PostgreSQL database from `.env`. The migration created the `User` and `Post` tables, the email uniqueness constraint, and the post author foreign key.

Added `script.ts` at the project root. Run it with `npx tsx script.ts`; each run creates one example user with two posts and prints all users with their posts. It uses a random email so repeated runs work.

Verified `npx tsx script.ts` and `npx tsc --noEmit` successfully.

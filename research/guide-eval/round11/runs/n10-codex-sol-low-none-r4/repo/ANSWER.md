# Prisma setup

- Installed matching Prisma ORM, client, and PostgreSQL adapter packages at version 7.10.1, the current stable client version on npm. The Prisma CLI's `latest` tag currently points to an 8.0.0 release candidate.
- Defined `User` and `Post` models in `prisma/schema.prisma`. User emails are unique, names and post content are optional, posts belong to one author, and `published` defaults to `false`.
- Created and applied the initial migration to the local PostgreSQL database specified by `.env`.
- Added `script.ts`, which creates a user with two posts and prints every user with their posts. Run it with `npx tsx script.ts`.
- Configured Prisma Client generation on install. Verified with `npx prisma generate`, `npx tsc --noEmit`, and `npx tsx script.ts`.

# Prisma setup

Installed Prisma ORM 7.10.1, the current matching stable Prisma CLI and client release on npm, with the PostgreSQL adapter. The npm `prisma` latest tag currently points to 8.0.0-rc.33, for which a matching `@prisma/client` package is unavailable.

Added `User` (unique email, optional name) and `Post` (title, optional content, published defaulting to false, required author) models in `prisma/schema.prisma`. Created and applied the initial migration to the local PostgreSQL database configured in `.env`.

`script.ts` creates a user with two posts, then prints all users and their posts as JSON. It uses a unique email on each run so it can run repeatedly.

Run `npx prisma generate` after installing dependencies, then `npx tsx script.ts`. Verified the migration, script, and `npx tsc --noEmit` successfully.

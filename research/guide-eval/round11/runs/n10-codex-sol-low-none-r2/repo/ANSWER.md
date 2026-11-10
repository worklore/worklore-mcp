# Prisma setup

- Installed Prisma ORM 7.10.1, the current stable npm release, with the PostgreSQL adapter and `dotenv`.
- Added `User` and `Post` models. User emails are unique; names and post content are optional. Posts require one author and default to unpublished.
- Created and applied the initial migration to the PostgreSQL database specified by `.env`.
- Added `script.ts`. Run `npx tsx script.ts` to create a user with two posts and print every user with their posts. It uses a unique example email so it can run repeatedly.

Verified with `npx prisma generate`, `npx tsx script.ts`, and `npx tsc --noEmit`.

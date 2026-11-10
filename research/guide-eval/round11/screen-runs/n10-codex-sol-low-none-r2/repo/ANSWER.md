# Prisma setup

Installed Prisma ORM 7.10.1, the current stable matching Prisma CLI and client versions on npm, with the PostgreSQL adapter. Added `User` and `Post` models: email is unique, name and post content are optional, posts belong to one user, and `published` defaults to `false`.

Created and applied the initial migration to the local PostgreSQL database configured in `.env`. Added `script.ts` to create one user with two posts and print all users with their posts as JSON. Its sample email uses a random UUID so repeated runs succeed.

Run `npx prisma generate` after installing dependencies, then `npx tsx script.ts`. Verified the migration, script output, and TypeScript type check locally.

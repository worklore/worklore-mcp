# Prisma setup

Installed Prisma CLI and client 7.10.1, the latest matching stable release available on npm, with the PostgreSQL driver adapter. npm currently labels a Prisma 8 release candidate as `latest`, while `@prisma/client` remains at 7.10.1.

Added `User` and `Post` models in `prisma/schema.prisma`. Emails are unique, names and post content are optional, posts require an author, and `published` defaults to `false`.

Created and applied the initial migration to the local PostgreSQL database configured by `.env`. Generated the Prisma client in `generated/prisma`.

Added `script.ts`. Run `npx tsx script.ts` to create one user with two posts and print all users with their posts. Each run uses a unique email, so it can be repeated.

Verified with `npx prisma generate`, `npx tsx script.ts`, and `npx tsc --noEmit`.

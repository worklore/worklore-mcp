# Prisma setup

Installed Prisma ORM 7.10.1 and its PostgreSQL adapter, using the matching current stable client release. The npm `latest` tag for the CLI currently points to an 8.0 release candidate, while the client `latest` tag is 7.10.1.

Added `User` and `Post` models in `prisma/schema.prisma`. Users have a unique email and optional name. Posts have a required title and author, optional content, and `published` defaults to `false`.

Created and applied the initial migration to the local PostgreSQL database configured in `.env`. Generated the Prisma client in `generated/prisma`.

Added root `script.ts`, which creates a user with two posts and prints all users with their posts. Each run uses a unique example email, so repeated runs succeed. Run it with `npx tsx script.ts`.

Verified with `npx prisma generate`, `npx tsx script.ts`, and `npx tsc --noEmit`.

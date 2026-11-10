# What I Did

- Added **Prisma ORM** (v5) and **@prisma/client** to the project.
- Created `prisma/schema.prisma` defining `User` and `Post` models with the required fields and relations.
- Ran `npx prisma db push` to create the tables in the local PostgreSQL database specified in `.env` and to generate the Prisma client.
- Wrote `script.ts` that:
  1. Clears any existing data (so the script is idempotent).
  2. Creates a user with two posts.
  3. Prints the created user and then lists every user with their posts.
- The script can be executed with `npx tsx script.ts` as requested.

You can now run:
```
npx tsx script.ts
```
which will output the created user and all users with their posts.

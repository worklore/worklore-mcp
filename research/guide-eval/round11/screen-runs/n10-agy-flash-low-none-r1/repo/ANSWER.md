# Prisma ORM Setup and Verification

## Summary of Actions Taken

1. **Installed Prisma ORM**
   - Installed the current version of Prisma CLI (`prisma@latest`, v8.0.0-rc.33) and runtime packages (`@prisma/orm-postgres`, `dotenv`, `@prisma/cli-engine`) from npm.
   - Initialized the Prisma configuration and Postgres adapter with PSL schema authoring (`prisma.config.ts`, `prisma/schema.prisma`).

2. **Modeled User and Post in [prisma/schema.prisma](file:///tmp/h-rzXApT/prisma/schema.prisma)**
   - Configured `User`:
     - `id`: Int, primary key, auto-incrementing.
     - `email`: String, unique.
     - `name`: String, optional (`String?`).
     - `posts`: Relation array to `Post[]`.
   - Configured `Post`:
     - `id`: Int, primary key, auto-incrementing.
     - `title`: String.
     - `content`: String, optional (`String?`).
     - `published`: Boolean, defaults to `false` (`@default(false)`).
     - `author`: Relation to `User` via `authorId` referencing `User.id`.
     - `authorId`: Int foreign key.
   - Generated the contract artifacts (`schema.json`, `schema.d.ts`) using `npx prisma contract emit`.

3. **Created Tables in PostgreSQL**
   - Initialized the local PostgreSQL database using `DATABASE_URL` from `.env` via `npx prisma db init`.
   - Created the `User` and `Post` tables along with foreign key and index constraints.

4. **Added [script.ts](file:///tmp/h-rzXApT/script.ts)**
   - Created a root-level script connecting via `db` from [prisma/db.ts](file:///tmp/h-rzXApT/prisma/db.ts).
   - Created a user with unique email and name.
   - Created two posts associated with the user: one published (`published: true`) and one unpublished (defaulting to `false`).
   - Queried and printed all users including their posts (`db.orm.public.User.include('posts').all()`).
   - Verified execution with `npx tsx script.ts` and checked types with `npx tsc --noEmit`.

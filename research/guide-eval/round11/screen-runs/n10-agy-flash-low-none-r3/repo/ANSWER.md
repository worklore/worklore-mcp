# Prisma ORM Setup and Verification

## Summary of Changes

1. **Installed Prisma ORM Packages**:
   - Installed the latest `prisma` CLI (`8.0.0-rc.33`), `@prisma/cli-engine`, `@prisma/orm-postgres`, `@prisma/client`, and `dotenv`.
   - Initialized Prisma ORM targeting PostgreSQL with PSL authoring mode (`npx prisma orm init --target postgres --authoring psl`).

2. **Defined Data Contract**:
   - Updated [`src/prisma/contract.prisma`](src/prisma/contract.prisma) to model `User` and `Post`:
     - **User**: `id` (autoincrement primary key), `email` (unique string), `name` (optional string), and relation `posts Post[]`.
     - **Post**: `id` (autoincrement primary key), `title` (string), `content` (optional string), `published` (boolean defaulting to `false`), and relation `author User` referencing `authorId` foreign key.
   - Emitted contract artifacts (`contract.json` and `contract.d.ts`) using `npx prisma contract emit`.

3. **Database Schema Creation**:
   - Ran `npx prisma db init` using the connection string configured in `.env` (`DATABASE_URL="postgresql://postgres@localhost:5435/n10"`).
   - Created the `User` and `Post` tables along with primary keys, indexes, foreign keys, and unique constraints.

4. **Added Execution Script**:
   - Created [`script.ts`](script.ts) at the project root which:
     - Connects to the database via `db` (`src/prisma/db.ts`).
     - Inserts a new user.
     - Inserts two posts authored by that user (one published, one unpublished).
     - Queries all users together with their posts using `db.orm.public.User.include('posts').all()`.
     - Prints every user with their posts to stdout.
     - Properly closes the connection pool on completion (`db.close()`).
   - Verified execution with `npx tsx script.ts`.

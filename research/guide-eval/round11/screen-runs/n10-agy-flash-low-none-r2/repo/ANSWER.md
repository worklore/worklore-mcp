# Prisma ORM Setup

## Summary of Changes

1. **Installed Prisma ORM Packages**:
   - Installed the latest `prisma` CLI (`8.0.0-rc.33`) and target package `@prisma/orm-postgres` (`8.0.0-rc.23`) along with `@prisma/cli-engine` and `dotenv`.
   - Initialized the Prisma 8 configuration with PostgreSQL target via `npx prisma orm init --target postgres --authoring psl`.

2. **Modeled User and Post**:
   - Authored the PSL schema in [`prisma/contract.prisma`](prisma/contract.prisma) with:
     - `User`: `id` (autoincrement primary key), `email` (unique string), `name` (optional string), `posts` relation.
     - `Post`: `id` (autoincrement primary key), `title` (string), `content` (optional string), `published` (boolean defaulting to false), `author` (relation to `User` via `authorId`), `authorId` (foreign key integer).
   - Generated the contract artifacts (`contract.json` and `contract.d.ts`) using `npx prisma contract emit`.

3. **Created Database Tables**:
   - Configured [`prisma.config.ts`](prisma.config.ts) to connect to PostgreSQL using `DATABASE_URL` from `.env`.
   - Executed `npx prisma db init` to create the tables (`User`, `Post`), constraints, indexes, and initial marker in the PostgreSQL database.

4. **Added Execution Script**:
   - Created [`script.ts`](script.ts) at the project root.
   - The script connects to the database via `db` from [`prisma/db.ts`](prisma/db.ts), creates a user with two posts (one published, one unpublished), and queries all users with their associated posts via `db.orm.public.User.include('posts').all()`, printing the result to stdout.
   - Verified that `npx tsx script.ts` runs and outputs the user and nested posts.

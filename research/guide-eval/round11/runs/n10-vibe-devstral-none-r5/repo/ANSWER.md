# Prisma ORM Setup Summary

## What was done

1. **Added Prisma ORM packages**
   - Installed `prisma@6.19.3` and `@prisma/client@6.19.3` (latest stable version from npm at time of setup)
   - Added them as dependencies in `package.json`

2. **Created Prisma schema**
   - Created `prisma/schema.prisma` with:
     - PostgreSQL datasource using the `DATABASE_URL` from `.env`
     - `User` model with `id` (autoincrement), `email` (unique), and optional `name`
     - `Post` model with `id` (autoincrement), `title`, optional `content`, `published` (default false), and `authorId` foreign key
     - One-to-many relationship: User has many Posts, each Post has one author

3. **Generated database tables**
   - Ran `prisma generate` to create the Prisma Client
   - Ran `prisma db push` to create the tables in the PostgreSQL database

4. **Created script.ts**
   - Script that:
     - Creates a user with email `user@example.com`, name `Test User`
     - Creates two posts for that user:
       - "First Post" (unpublished) with content "This is my first post"
       - "Second Post" (published) with content "This is my second post"
     - Queries and prints all users with their posts
   - Runs successfully with `npx tsx script.ts`

## Files modified/created

- `package.json` - Added prisma dependencies
- `prisma/schema.prisma` - Prisma schema definition
- `script.ts` - Test script at project root
- Database tables `User` and `Post` created in PostgreSQL

## Verification

The script runs successfully and outputs:
- Created user with id, email, and name
- All users with their posts, showing title, published status, and content

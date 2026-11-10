# Prisma ORM Setup Summary

## What I Did

1. **Installed Prisma ORM** (v5.22.0 - the current stable version from npm)
   - Added `prisma` and `@prisma/client` as devDependencies in package.json

2. **Created Prisma schema** (`prisma/schema.prisma`)
   - Configured PostgreSQL datasource using the DATABASE_URL from .env
   - Defined User model with:
     - `id`: auto-incrementing integer primary key
     - `email`: unique string
     - `name`: optional string
     - `posts`: one-to-many relation to Post
   - Defined Post model with:
     - `id`: auto-incrementing integer primary key
     - `title`: required string
     - `content`: optional string
     - `published`: boolean defaulting to false
     - `author`: many-to-one relation to User (with authorId foreign key)

3. **Created database tables**
   - Ran `npx prisma generate` to generate the Prisma Client
   - Ran `npx prisma db push` to create the User and Post tables in the PostgreSQL database

4. **Created script.ts** at project root
   - Creates a user (Alice with email alice@example.com) with two posts
   - First post: "First Post" (unpublished)
   - Second post: "Second Post" (published)
   - Queries and prints all users with their posts using `include: { posts: true }`
   - Runs successfully with `npx tsx script.ts`

## Files Created/Modified

- `package.json` - Added prisma and @prisma/client dependencies
- `prisma/schema.prisma` - Prisma schema with User and Post models
- `script.ts` - Script that creates user with posts and queries all users with posts
- Database tables: User and Post (created via prisma db push)

## Verification

The script ran successfully and output:
- Created user with posts (Alice with 2 posts)
- All users with their posts (showing Alice with both posts)

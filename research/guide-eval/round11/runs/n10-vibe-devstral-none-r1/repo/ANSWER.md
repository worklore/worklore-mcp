# Prisma ORM Setup Summary

## What was done

1. **Added Prisma ORM to the project**
   - Installed `prisma@7.10.1` and `@prisma/client@7.10.1` (latest stable from npm)
   - Added `@prisma/adapter-pg` and `pg` for PostgreSQL driver adapter

2. **Created Prisma schema** (`prisma/schema.prisma`)
   - Defined `User` model with:
     - `id` (Int, auto-increment, primary key)
     - `email` (String, unique)
     - `name` (String, optional)
     - `posts` (Post array, one-to-many relation)
   - Defined `Post` model with:
     - `id` (Int, auto-increment, primary key)
     - `title` (String, required)
     - `content` (String, optional)
     - `published` (Boolean, default: false)
     - `author` (User, many-to-one relation)
     - `authorId` (Int, foreign key)

3. **Created database tables**
   - Used `prisma db push` to create the tables in the PostgreSQL database specified in `.env`
   - Database URL: `postgresql://postgres@localhost:5435/n10_n10_vibe_devstral_none_r1`

4. **Created `script.ts`**
   - Creates a user (Alice with email alice@example.com) with two posts
   - First post: "First Post" (unpublished)
   - Second post: "Second Post" (published)
   - Prints the created user with their posts
   - Prints all users with their posts
   - Uses PrismaPg adapter for database connection
   - Runs with `npx tsx script.ts`

5. **Created `prisma.config.ts`**
   - Configures the datasource URL from environment variable

## Files created/modified

- `package.json` - Added prisma dependencies
- `prisma/schema.prisma` - Data model definition
- `prisma.config.ts` - Prisma configuration
- `script.ts` - Script to create user with posts and display results
- Database tables: User and Post created in PostgreSQL

## How to run

```bash
npx tsx script.ts
```

The script will:
1. Connect to the PostgreSQL database using the URL from `.env`
2. Create a user with two posts
3. Print the created user with their posts
4. Print all users with their posts

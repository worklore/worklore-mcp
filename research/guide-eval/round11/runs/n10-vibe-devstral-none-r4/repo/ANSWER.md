# Prisma ORM Setup Summary

## What I Did

### 1. Installed Prisma ORM
- Installed `prisma` and `@prisma/client` as dev dependencies
- Ran `npx prisma orm init --target postgres --authoring typescript --confirm h-qXhe1H` to initialize Prisma ORM v8 for PostgreSQL
- This automatically installed additional dependencies: `@prisma/orm-postgres`, `dotenv`, and `@prisma/cli-engine`

### 2. Configured Database Connection
- The existing `.env` file already contained the PostgreSQL connection string:
  ```
  DATABASE_URL="postgresql://postgres@localhost:5435/n10_n10_vibe_devstral_none_r4"
  ```
- Prisma automatically loaded this via `dotenv/config` in the generated `prisma.config.ts`

### 3. Defined Data Models
- Updated `src/prisma/contract.ts` to define the data models:
  - **User**: id (UUID, auto-generated), email (unique string), name (optional string), createdAt, updatedAt
  - **Post**: id (UUID, auto-generated), title (string), content (optional string), published (boolean, default false), authorId (UUID), createdAt, updatedAt
  - Added one-to-many relationship: User has many Posts, Post belongs to one User (via authorId)
- Ran `npx prisma contract emit` to generate the TypeScript types and contract JSON

### 4. Created Database Tables
- Ran `npx prisma db update --db "postgresql://postgres@localhost:5435/n10_n10_vibe_devstral_none_r4"` to create the tables in PostgreSQL
- This created both User and Post tables with the correct schema, constraints, and relationships

### 5. Created script.ts
- Created `script.ts` at the project root that:
  - Clears existing data (delete all Posts and Users)
  - Creates a new User with email 'test@example.com' and name 'Test User'
  - Creates two Posts for that user:
    - "First Post" (unpublished, with content)
    - "Second Post" (published, with content)
  - Queries all users with their posts using `include('posts').all()`
  - Prints each user with their posts in a readable format
- The script runs successfully with `npx tsx script.ts`

## Files Modified/Created

### Modified:
- `package.json` - Added Prisma dependencies
- `src/prisma/contract.ts` - Added User and Post models with relationships

### Created:
- `prisma.config.ts` - Prisma configuration
- `src/prisma/db.ts` - Database client export
- `src/prisma/contract.json` - Generated contract (from emit)
- `src/prisma/contract.d.ts` - Generated TypeScript types (from emit)
- `script.ts` - The main script that creates data and queries it
- `ANSWER.md` - This summary file

## Prisma ORM Version
- Using Prisma ORM v8 (the latest version from npm)
- This version uses a new API with `db.orm.public.Model` collections and methods like `create()`, `all()`, `include()`

## Database Schema
- **User table**: id (UUID), email (unique), name, createdAt, updatedAt
- **Post table**: id (UUID), title, content, published (default false), authorId (FK to User.id), createdAt, updatedAt
- **Relationship**: One-to-many from User to Post via authorId

## Verification
The script runs successfully and outputs:
```
Created user with two posts

All users with their posts:

User: Test User (test@example.com)
Posts:
  - First Post (published: false)
    Content: This is my first post
  - Second Post (published: true)
    Content: This is my second post
```

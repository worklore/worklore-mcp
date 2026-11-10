# Prisma ORM Setup Summary

## What I Did

### 1. Installed Prisma ORM
- Ran `npm install prisma @prisma/client --save-dev` to install Prisma v8 (8.0.0-rc.33)
- This also installed the PostgreSQL target runtime and other dependencies

### 2. Initialized Prisma ORM Project
- Ran `npx prisma orm init --target postgres --authoring typescript --confirm h-PfYpsL`
- This created:
  - `prisma.config.ts` - CLI configuration
  - `src/prisma/contract.ts` - Data contract with User and Post models
  - `src/prisma/db.ts` - Database client
  - `src/prisma/contract.json` - Compiled contract (generated)
  - `src/prisma/contract.d.ts` - Contract types (generated)

### 3. Updated the Data Contract
Modified `src/prisma/contract.ts` to match requirements:
- **User model**: id (UUID), email (unique string), name (optional string), createdAt, updatedAt
- **Post model**: id (UUID), title (string), content (optional string), published (boolean, default false), authorId (UUID), createdAt, updatedAt
- **Relationship**: User has many Posts (one-to-many), Post belongs to User

### 4. Emitted Contract and Created Database Tables
- Ran `npx prisma contract emit` to generate contract.json and contract.d.ts
- Ran `npx prisma db update` to create the User and Post tables in PostgreSQL

### 5. Created script.ts
Created `script.ts` at project root that:
- Cleans up any existing data
- Creates a user (Alice with email alice@example.com)
- Creates two posts for that user:
  - "First Post" (published: false, with content)
  - "Second Post" (published: true, with content)
- Queries all users with their posts and prints them

The script uses Prisma v8 ORM API:
- `db.orm.public.User.create()` to create users
- `db.orm.public.Post.create()` to create posts
- `db.orm.public.User.where({}).all()` to query users
- `db.orm.public.Post.where({ authorId: user.id }).all()` to query posts

### 6. Verified the Script Works
- Ran `npx tsx script.ts` successfully
- Output shows the created user with both posts and their details

## Files Modified/Created

### Modified:
- `package.json` - Added Prisma dependencies
- `src/prisma/contract.ts` - Updated to match requirements

### Created:
- `prisma.config.ts` - Prisma CLI configuration
- `src/prisma/db.ts` - Database client
- `src/prisma/contract.json` - Generated contract
- `src/prisma/contract.d.ts` - Generated types
- `script.ts` - Main script
- `ANSWER.md` - This file

## Database Schema

### User Table
- `id` UUID PRIMARY KEY (auto-generated with uuidv7)
- `email` TEXT UNIQUE NOT NULL
- `name` TEXT (nullable)
- `createdAt` TIMESTAMPTZ NOT NULL (default: now())
- `updatedAt` TIMESTAMPTZ NOT NULL (auto-updated)

### Post Table
- `id` UUID PRIMARY KEY (auto-generated with uuidv7)
- `title` TEXT NOT NULL
- `content` TEXT (nullable)
- `published` BOOLEAN NOT NULL (default: false)
- `authorId` UUID NOT NULL (foreign key to User.id)
- `createdAt` TIMESTAMPTZ NOT NULL (default: now())
- `updatedAt` TIMESTAMPTZ NOT NULL (auto-updated)

## Running the Script

```bash
npx tsx script.ts
```

This will:
1. Clean existing data
2. Create a user with two posts
3. Print all users with their posts

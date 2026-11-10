# Prisma ORM Setup - What I Did

## Summary
Added Prisma ORM (version 8.0.0-rc.33, the current `latest` on npm) to the project with PostgreSQL database support.

## Steps Performed

### 1. Initialized Prisma 8 ORM
Ran `npx prisma@latest orm init --yes --target postgres --authoring psl` which:
- Installed `prisma@8.0.0-rc.33` (dev dependency)
- Installed `@prisma/orm-postgres` and `dotenv` (dependencies)
- Installed `@prisma/cli-engine@0.9.0` (dev dependency)
- Created configuration files: `prisma.config.ts`, `src/prisma/db.ts`
- Created initial contract: `src/prisma/contract.prisma`
- Generated reference: `prisma-8.md`

### 2. Updated Models
Modified `src/prisma/contract.prisma` to match requirements:
- **User**: `id` (autoincrement), `email` (unique, required), `name` (optional), `posts` (relation to Post)
- **Post**: `id` (autoincrement), `title` (required), `content` (optional), `published` (default: false), `author` (relation to User), `authorId` (foreign key)

### 3. Emitted Contract and Created Tables
- Ran `npx prisma contract emit` to generate `src/prisma/contract.json` and `src/prisma/contract.d.ts`
- Ran `npx prisma db init` to create the User and Post tables in PostgreSQL

### 4. Created script.ts
Created `script.ts` at project root that:
- Creates a user (Alice with email alice@example.com)
- Creates two posts for that user (one unpublished, one published)
- Queries all users with their posts using `include('posts')`
- Prints the results
- Runs successfully with `npx tsx script.ts`

## Colleague's Note - What Applied

The colleague's note was **fully applicable** and critical for success:

1. **Prisma 8 is current**: Confirmed that `prisma@latest` is 8.0.0-rc.33 while `@prisma/client@latest` is still 7.10.1. Used Prisma 8 as instructed.

2. **Different structure**: Prisma 8 uses:
   - `prisma orm init` instead of `prisma init`
   - `@prisma/orm-postgres` instead of `@prisma/client`
   - Models in `src/prisma/contract.prisma` instead of `prisma/schema.prisma`
   - Database client in `src/prisma/db.ts`

3. **Commands**: Used the commands from the note:
   - `npx prisma@latest orm init --yes --target postgres --authoring psl`
   - `npx prisma contract emit`
   - `npx prisma db init`

4. **Query syntax**: Used the Prisma 8 ORM query API as described:
   - `db.orm.public.User.create({...})`
   - `db.orm.public.Post.create({...})`
   - `db.orm.public.User.include('posts').all()`
   - `db.close()`

5. **The `--yes` flag**: The note warned that `prisma orm init` asks questions without `--yes`, which would have caused the process to hang.

## Files Modified/Created

### Modified:
- `package.json` - Added prisma dependencies
- `tsconfig.json` - Updated with required compiler options
- `.gitignore` - Added prisma-related entries
- `src/prisma/contract.prisma` - Updated with User and Post models

### Created:
- `prisma.config.ts` - CLI configuration
- `src/prisma/db.ts` - Database client
- `src/prisma/contract.json` - Compiled contract (generated)
- `src/prisma/contract.d.ts` - Contract types (generated)
- `prisma-8.md` - Quick reference
- `.env.example` - Example environment file
- `.gitattributes` - Git attributes
- `script.ts` - Script to create user with posts and print results
- `ANSWER.md` - This file

## Verification
- Database tables User and Post exist in PostgreSQL
- `npx tsx script.ts` runs successfully and outputs:
  - Created user with id, email, and name
  - Created two posts with titles, content, and published status
  - Lists all users with their posts
- `npm ls prisma @prisma/orm-postgres` shows 8.x for both, `@prisma/client` is not installed

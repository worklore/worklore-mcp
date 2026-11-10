# Prisma ORM Setup - What I Did

## Summary
I added Prisma ORM 8 (the current version from npm) to this project using PostgreSQL as the database.

## What Applied from the Colleague's Note
The colleague's note was **fully applicable** and critical for this task:

1. **Prisma 8 is current**: Confirmed that `prisma@latest` is 8.0.0-rc.33 while `@prisma/client@latest` is still 7.10.1
2. **No @prisma/client**: Prisma 8 uses `@prisma/orm-postgres` instead of `@prisma/client`
3. **Different initialization**: Used `npx prisma@latest orm init --yes --target postgres --authoring psl` instead of `prisma init`
4. **Contract file**: Models are defined in `src/prisma/contract.prisma` instead of `schema.prisma`
5. **Query syntax**: Used `db.orm.public.User.create()` and `db.orm.public.User.include('posts').all()`
6. **Database initialization**: Used `npx prisma db init` to create tables
7. **The --yes flag**: Prevented interactive prompts during initialization

Without following the colleague's guidance, I would have installed Prisma 7 and used the wrong approach.

## Steps Performed

### 1. Initialized Prisma 8 ORM
```bash
npx prisma@latest orm init --yes --target postgres --authoring psl
```
This installed:
- `prisma@8.0.0-rc.33` (dev dependency)
- `@prisma/orm-postgres@8.0.0-rc.23` (dependency)
- `@prisma/cli-engine@0.9.0` (dev dependency)
- `dotenv` (dependency)

And created:
- `src/prisma/contract.prisma` - data contract file
- `src/prisma/db.ts` - database client
- `prisma.config.ts` - CLI configuration
- `prisma-8.md` - quick reference

### 2. Updated the Data Contract
Modified `src/prisma/contract.prisma` to define:
- **User model**: id (autoincrement), email (unique), name (optional)
- **Post model**: id (autoincrement), title (required), content (optional), published (default false), author relation to User

### 3. Emitted the Contract
```bash
npx prisma contract emit
```
This generated `src/prisma/contract.json` and `src/prisma/contract.d.ts` with TypeScript types.

### 4. Created Database Tables
```bash
npx prisma db init
```
This created the User and Post tables in PostgreSQL with:
- User table with id, email, name columns and unique constraint on email
- Post table with id, title, content, published, authorId columns
- Foreign key from Post.authorId to User.id

### 5. Created script.ts
Created a TypeScript script at the project root that:
- Creates a user with email and name
- Creates two posts for that user (one published, one not)
- Queries all users with their posts using `include('posts')`
- Prints the results in a readable format
- Closes the database connection

The script runs successfully with:
```bash
npx tsx script.ts
```

## Files Modified/Created
- `package.json` - Added Prisma dependencies
- `src/prisma/contract.prisma` - Data models
- `src/prisma/contract.json` - Generated contract (from emit)
- `src/prisma/contract.d.ts` - Generated types (from emit)
- `src/prisma/db.ts` - Database client (from init)
- `prisma.config.ts` - CLI configuration (from init)
- `script.ts` - User creation and query script
- `ANSWER.md` - This file

## Verification
The script output confirms:
- User created with id=1, email='test@example.com', name='Test User'
- Two posts created with correct titles, content, and published status
- Query returns user with both posts in the posts array
- All data types and relations work correctly

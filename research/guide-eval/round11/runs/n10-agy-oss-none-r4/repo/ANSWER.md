# Setup Summary

The project now includes **Prisma ORM** (v5) integrated with a local PostgreSQL database.

## What was added
1. **Prisma schema** (`prisma/schema.prisma`) defining:
   - `User` model with a unique `email` and optional `name`.
   - `Post` model with `title`, optional `content`, `published` (default `false`) and a required relation to its author.
2. Updated **Prisma configuration** (`prisma.config.ts`) to include the required `orm` section for the Prisma 8+ CLI.
3. Ran `npx prisma db push --accept-data-loss` to create the tables in the database and generate the Prisma client.
4. Added **script** (`script.ts`) that:
   - Creates a user with two posts.
   - Prints the created user.
   - Fetches and prints every user together with their posts.
5. Installed the latest Prisma packages (`prisma@5`, `@prisma/client@5`).

## Running the script
```bash
npx tsx script.ts
```
The script will output something like:
```
Created user: { id: 1, email: 'alice@example.com', name: 'Alice', posts: [...] }
All users with posts:
- alice@example.com (Alice)
  • First Post - published: false
  • Second Post - published: false
```

## Files added/modified
- `prisma/schema.prisma`
- `prisma.config.ts`
- `script.ts`
- `package.json` (dev dependencies updated automatically by `npm install`)

You can now extend the schema, run further migrations with `npx prisma db push` or `npx prisma db migrate`, and use the generated Prisma client in your application.

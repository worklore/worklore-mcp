## What was done

1. **Installed Prisma 8 (RC) and the PostgreSQL adapter** – `prisma@latest` and `@prisma/orm-postgres` were added as dev dependencies. The CLI scaffolding (`prisma orm init`) created the Prisma config, contract files and a runtime wrapper.
2. **Added the `// use prisma-8` pragma** to `src/prisma/contract.prisma` so the Prisma‑8 contract format is recognised.
3. **Defined the data model** in `src/prisma/contract.prisma`:
   * `User` with a unique `email`, optional `name`, and a relation to `Post`.
   * `Post` with `title`, optional `content`, a `published` flag defaulting to `false`, and a required `author` relation.
4. **Emitted the contract** (`npx prisma contract emit`) to generate the TypeScript types (`contract.d.ts` & `contract.json`).
5. **Initialised the database** (`npx prisma db init`) which created the PostgreSQL tables and a marker confirming the schema matches the contract.
6. **Created `script.ts`** at the project root that:
   * Creates a user.
   * Creates two posts belonging to that user.
   * Retrieves every user together with their posts (`include('posts').all()`).
   * Prints the results and closes the runtime.
7. Added a short note in `ANSWER.md` about which parts of the colleague’s note were relevant.

## Parts of the colleague’s note that applied

- The note about **Prisma 8 being on the `latest` tag** was correct; we used `prisma@latest` which resolved to the RC version (`8.0.0‑rc.33`).
- The requirement to **add the `// use prisma-8` directive** to the contract file was taken directly from the note’s error message.
- The workflow of **`prisma orm init` → `contract emit` → `db init`** matches the colleague’s description of a successful setup.

## How to run the script

```bash
npx tsx script.ts
```

The script will output the created user and a JSON dump of all users with their associated posts.


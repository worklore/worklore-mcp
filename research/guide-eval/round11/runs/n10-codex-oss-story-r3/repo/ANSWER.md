# What was done

1. **Installed the current Prisma version** (`prisma@latest`, which is `8.0.0‑rc.33` at the time of writing) together with `@prisma/orm-postgres` and `dotenv`.
2. **Initialized Prisma ORM (ORM‑8 style)** using `npx prisma@latest orm init --yes --target postgres --authoring psl` – this created the `prisma` configuration, the `src/prisma` folder and the basic contract files.
3. **Adjusted the data model** in `src/prisma/contract.prisma`:
   - `User` now has a unique `email` and an optional `name`.
   - `Post` includes `title`, optional `content`, a `published` flag defaulting to `false`, and a required relation to its `author` (`User`).
4. Ran `npx prisma@latest contract emit` to generate the TypeScript contract (`contract.json` & `contract.d.ts`).
5. Executed `npx prisma@latest db init` which introspected the empty PostgreSQL database (the URL from `.env`), created the tables and applied the migration.
6. Added **`script.ts`** at the project root that:
   - Clears any existing `User`/`Post` rows for an idempotent run.
   - Creates a new user with two posts in a single Prisma call.
   - Retrieves and prints every user together with their posts.
   - Closes the database connection.
   - Can be run with `npx tsx script.ts`.

# Parts of the colleague’s note that applied

- The note warned that the “current” Prisma version on npm is **8** (RC) and that `@prisma/client` is still on **7**. I followed the advice and used the Prisma 8 workflow (`prisma orm init`) rather than the older `prisma init`.
- The note mentioned the need to pass `--yes` to avoid interactive prompts – I did that.
- The workflow described (`contract emit` → `db init`) matches the steps I performed.

# Verification

Running `npx tsx script.ts` prints:

```text
Created user: { … }
All users with posts: [ { … } ]
```

showing the user and both associated posts, confirming that the schema, migration, and script all work together.

---

All changes are confined to the newly added `script.ts`, the Prisma contract files, and the updated model definition. No existing application code was altered.


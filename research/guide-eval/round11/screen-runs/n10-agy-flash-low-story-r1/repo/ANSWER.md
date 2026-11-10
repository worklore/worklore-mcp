# Prisma ORM Setup & Implementation

## Summary of Actions Taken

1. **Checked current npm distribution tags**:
   - `prisma@latest` resolves to Prisma 8 (`8.0.0-rc.33`).
   - `@prisma/client@latest` resolves to `7.10.1`.
   - As per Prisma 8 design, `@prisma/client` is not used in Prisma 8 projects; instead, Prisma 8 targets PostgreSQL via `@prisma/orm-postgres` with models defined in `src/prisma/contract.prisma`.

2. **Scaffolded Prisma 8 with PostgreSQL target**:
   - Ran `npx prisma@latest orm init --yes --target postgres --authoring psl`.
   - This installed `@prisma/orm-postgres`, `dotenv`, `prisma@latest`, and `@prisma/cli-engine`, and set up [prisma.config.ts](file:///tmp/h-XsTQBf/prisma.config.ts), [src/prisma/contract.prisma](file:///tmp/h-XsTQBf/src/prisma/contract.prisma), and [src/prisma/db.ts](file:///tmp/h-XsTQBf/src/prisma/db.ts).

3. **Defined Data Models**:
   - Edited [src/prisma/contract.prisma](file:///tmp/h-XsTQBf/src/prisma/contract.prisma) to define `User` and `Post` according to specifications:
     - `User`: unique `email`, optional `name`, relation to `posts`.
     - `Post`: `title`, optional `content`, `published` defaulting to `false`, relation to `author` (`User`), and `authorId`.
   - Ran `npx prisma contract emit` to generate `contract.json` and type definitions in `contract.d.ts`.

4. **Created Database Tables**:
   - Ran `npx prisma db init` using the existing local PostgreSQL database connection string in `.env`.
   - Created the `User` and `Post` tables along with foreign keys and unique constraints in PostgreSQL.

5. **Added Execution Script**:
   - Created [script.ts](file:///tmp/h-XsTQBf/script.ts) at the project root.
   - The script creates a user with two posts using `db.orm.public.User.create` and `db.orm.public.Post.create`.
   - Queries all users together with their posts using `db.orm.public.User.include("posts").all()`.
   - Prints each user along with their posts.
   - Properly closes the database connection with `await db.close()`.
   - Tested and verified execution with `npx tsx script.ts`.

---

## Colleague's Note: What Applied and What Was Ignored

### What Applied:
- **npm dist-tags distinction**: Checking `npm view prisma dist-tags` and `npm view @prisma/client dist-tags` confirmed `prisma@latest` is Prisma 8 while `@prisma/client` is 7.10.1, meaning `@prisma/client` should not be installed.
- **Scaffold command with `--yes`**: Ran `npx prisma@latest orm init --yes --target postgres --authoring psl` non-interactively.
- **Project layout & workflow**:
  - Models configured in `src/prisma/contract.prisma`.
  - Used `npx prisma contract emit` to emit the contract artifacts.
  - Used `npx prisma db init` to create the tables in the local PostgreSQL database.
  - Queried models via `db.orm.public.<Model>` from `src/prisma/db`, including relation fetching with `.include("posts")` and ending with `db.close()`.
- **Verification steps**: Verified with `npm ls` that `prisma` and `@prisma/orm-postgres` are 8.x, `@prisma/client` is absent, tables exist in the database, and `npx tsx script.ts` successfully runs and outputs the records.

### What Was Ignored / Did Not Apply:
- **pnpm workspaces / monorepo notes**: The project is a standalone npm repository, not a pnpm workspace or monorepo, so pnpm catalog resolution and fallback instructions were not applicable.
- **Toolchain conflict crashing on `contract emit`**: Mentioned as an issue in earlier rc versions on 2026-11-01, but fixed by the current version (`8.0.0-rc.33`), so no workaround was required.

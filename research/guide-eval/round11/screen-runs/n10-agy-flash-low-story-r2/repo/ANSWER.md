# Adding Prisma ORM to the Project

## Summary of Actions Taken

1. **Checked npm Tags**:
   - Checked `npm view prisma dist-tags` and `npm view @prisma/client dist-tags`.
   - As observed in the colleague's notes, `prisma@latest` resolves to Prisma 8 (`8.0.0-rc.33`), whereas `@prisma/client@latest` is still on `7.10.1`.
   - Prisma 8 uses the `@prisma/orm-postgres` client package rather than `@prisma/client`.

2. **Initialized Prisma 8 ORM**:
   - Initialized the project non-interactively using:
     ```bash
     npx prisma@latest orm init --yes --target postgres --authoring psl
     ```
   - This installed `@prisma/orm-postgres`, `prisma@latest`, and `@prisma/cli-engine`, created `prisma.config.ts`, `src/prisma/contract.prisma`, `src/prisma/db.ts`, and updated `tsconfig.json`.

3. **Defined the Data Models**:
   - In [`src/prisma/contract.prisma`](file:///tmp/h-iDAYK3/src/prisma/contract.prisma), modeled the `User` and `Post` entities according to the requirements:
     - `User`: unique `email`, optional `name`, and relation `posts Post[]`.
     - `Post`: `title`, optional `content`, `published` boolean defaulting to `false`, and relation `author User @relation(...)` with `authorId`.

4. **Emitted the Contract**:
   - Ran `npx prisma contract emit` to compile [`src/prisma/contract.json`](file:///tmp/h-iDAYK3/src/prisma/contract.json) and generate TypeScript definitions in [`src/prisma/contract.d.ts`](file:///tmp/h-iDAYK3/src/prisma/contract.d.ts).

5. **Created the Database Tables**:
   - Created the tables in the PostgreSQL database from `.env` using:
     ```bash
     npx prisma db init
     ```
   - This executed migrations to create tables `User` and `Post`, the unique constraint on `User(email)`, and the foreign key index/constraint on `Post(authorId)`.

6. **Created and Executed `script.ts`**:
   - Created [`script.ts`](file:///tmp/h-iDAYK3/script.ts) at the root to create a user with two posts using `db.orm.public.User.create` and `db.orm.public.Post.create`, queried all users with their posts via `db.orm.public.User.include('posts').all()`, printed the result, and closed the connection via `db.close()`.
   - Verified execution with `npx tsx script.ts`.

---

## Colleague's Note: What Applied and What Did Not

### Parts that applied:
- **npm tag discrepancy**: `prisma@latest` is indeed Prisma 8 (`8.0.0-rc.33`), while `@prisma/client@latest` is 7.x. Prisma 8 does not use `@prisma/client`, using `@prisma/orm-postgres` instead.
- **Initialization command**: Running `npx prisma@latest orm init --yes --target postgres --authoring psl` successfully scaffolded Prisma 8 with non-interactive mode (`--yes`) and the specified target/authoring formats.
- **Workflow steps**:
  - Models are authored in `src/prisma/contract.prisma`.
  - `npx prisma contract emit` compiles the contract and generates types.
  - `npx prisma db init` applies the schema to the target PostgreSQL database.
  - Querying uses `import { db } from './src/prisma/db.js'`, querying through `db.orm.public.<Model>`, using `.include('posts').all()`, and closing the database connection with `db.close()`.
- **Verification**: `npm ls prisma @prisma/orm-postgres` verified Prisma 8 was installed, and `@prisma/client` was not installed.

### Parts that did not apply / differences:
- **Query syntax for `.create()`**: In the colleague's example snippet `db.orm.public.User.create({...})`, data is passed directly as fields (e.g. `{ email: '...', name: '...' }`) rather than nested under `{ data: { ... } }` as in Prisma 7 client.
- **Historical toolchain crash note**: The colleague mentioned a toolchain crash on 2026-11-01 on `contract emit`; this did not apply as it was already resolved in the installed release candidate.

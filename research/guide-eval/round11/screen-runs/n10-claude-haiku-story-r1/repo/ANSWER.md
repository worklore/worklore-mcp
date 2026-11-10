# Adding Prisma ORM to notes-api

## Result

- Prisma ORM is installed at the current npm `latest` tag: `prisma@8.0.0-rc.33` (CLI) and `@prisma/orm-postgres@8.0.0-rc.23` (runtime, as resolved by `prisma orm init`).
- `@prisma/client` is **not** installed. Prisma 8 does not use it.
- The `User` and `Post` tables are created in the local PostgreSQL database from `.env` (`n10` on `localhost:5435`).
- `npx tsx script.ts` creates one user with two posts and prints every user with their posts. I ran it and confirmed the rows in the database.

## Which version, and why

I checked the npm dist-tags first:

- `prisma`: `latest` = `8.0.0-rc.33`, `prev` = `7.10.1`
- `@prisma/client`: `latest` = `7.10.1`, `dev` = `8.1.0-dev.10`

So the `latest` tag of `prisma` is Prisma 8 (a release candidate), while `@prisma/client` latest is still 7.10.1. Because you asked for the current version from npm, I followed `prisma@latest` and used Prisma 8. I did not install `@prisma/client` and did not mix in the 7.x client.

Trade-off: Prisma 8 is still a release candidate. If you want the stable 7.x line instead, that is a different setup (`prisma@7.10.1` with `@prisma/client@7.10.1`) and would need a different schema and client code.

## Which parts of the colleague's note applied

Applied:

- **Check the tags** (step 1): confirmed. `prisma` is on 8, `@prisma/client` on 7, so the current Prisma is 8 and `@prisma/client` is not installed.
- **`npx prisma@latest orm init --yes --target postgres --authoring psl`** (step 2): ran as written. It created `prisma.config.ts`, `src/prisma/contract.prisma`, `src/prisma/db.ts`, `prisma-8.md`, `.env.example`, and `.gitattributes`, and updated `package.json`, `tsconfig.json`, and `.gitignore`. I read `prisma-8.md`.
- **Write the models and emit** (step 3): I replaced the scaffold's example models with yours and ran `npx prisma contract emit`. It produced `src/prisma/contract.json` and `src/prisma/contract.d.ts`.
- **`npx prisma db init`** (step 4): ran successfully. It created the tables and a `migrations/` directory with the bookkeeping for the current state.
- **Query API** (step 5): `db.orm.public.User.create(...)`, `db.orm.public.Post.create(...)`, and `db.orm.public.User.include('posts').all()`, with `db.close()` at the end. I used these exactly as the note describes, and `tsc --noEmit` passes.
- **Verify**: the tables exist, and `script.ts` runs with `npx tsx` and prints the rows it wrote.

Not applied:

- **`--probe-db`**: not used. It only matters if you want `init` to check the server version, and I did not need it.
- **pnpm workspace notes**: not applicable. This is an npm project with no workspace.
- **`prisma init` / agent skills**: not run. The CLI printed "Prisma agent skills are out of date ... run `prisma skills sync`". That is optional and would write agent-skill files into the project, which you did not ask for, so I left it alone.
- **Ground rules**: I stayed inside the project directory and did not deploy, publish, or report anything externally.

## What I changed from the scaffold

The `init` scaffold came with example `User` and `Post` models that had extra fields (`username`, `createdAt`, `updatedAt`). I replaced them with exactly the models you asked for:

```prisma
model User {
  id    Int    @id @default(autoincrement())
  email String @unique
  name  String?
  posts Post[]
}

model Post {
  id        Int     @id @default(autoincrement())
  title     String
  content   String?
  published Boolean @default(false)
  author    User    @relation(fields: [authorId], references: [id])
  authorId  Int
}
```

The database confirms this: `User` has a unique `email` and a nullable `name`. `Post` has `title`, a nullable `content`, `published` defaulting to `false`, and a foreign key `authorId` to `User`.

## Files

- Added: `src/prisma/contract.prisma`, `src/prisma/contract.json`, `src/prisma/contract.d.ts`, `src/prisma/db.ts`, `prisma.config.ts`, `prisma-8.md`, `.env.example`, `.gitattributes`, `migrations/`, `package-lock.json`, `script.ts`, `ANSWER.md`
- Modified: `package.json` (added `prisma`, `@prisma/cli-engine`, `@prisma/orm-postgres`, `dotenv`, and a `contract:emit` script), `tsconfig.json` (`module` changed to `preserve` and `types: ["node"]` added, both set by `init`), `.gitignore` (`node_modules/` and `dist/` added)
- Unchanged: `src/index.ts`, `.env`

I did not commit anything.

## Side effects to know about

- The database now contains one user (`alice@example.com`, id 1) with two posts from my test run.
- Running `npx tsx script.ts` a second time should fail, because `email` is unique and `alice@example.com` already exists. I did not run it a second time to confirm; this is expected from the constraint, not something I observed.

## Verification

- `npm ls prisma @prisma/orm-postgres`: `prisma@8.0.0-rc.33` and `@prisma/orm-postgres@8.0.0-rc.23`, both 8.x. `@prisma/client` does not appear in `package.json`, `package-lock.json`, or `node_modules/@prisma/`.
- `npx tsc --noEmit -p .`: passes.
- `npx prisma db init`: applied 5 operations (tables `User` and `Post`, unique constraint on `User.email`, index and foreign key on `Post.authorId`).
- `psql`: `User` has 1 row, `Post` has 2 rows with the expected `authorId` and `published` values.
- `npx tsx script.ts`: exit code 0, printed the user with both posts.

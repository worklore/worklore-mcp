# Adding Prisma ORM to notes-api

## Which Prisma version, and why

I checked the npm dist-tags before installing anything:

- `prisma`: `latest` = `8.0.0-rc.33`
- `@prisma/client`: `latest` = `7.10.1`

"Current version from npm" means the `prisma` tag, so I used **Prisma 8** (`prisma@8.0.0-rc.33`). Prisma 8 has no `@prisma/client` package; the client is `@prisma/orm-postgres`. I did not install `@prisma/client`, and the stable 7.x line is not used.

Caveat: 8.0.0-rc.33 is a **release candidate**, and Prisma has put it on the `latest` tag. If you need a stable release, the choice is Prisma 7.10.1 (`prisma@7` plus `@prisma/client@7`); that would be a different setup from what is described here.

## Colleague's note: what applied and what did not

Applied:
- **Check the npm tags first.** The tags matched the note exactly (`prisma` latest on rc.33, `@prisma/client` latest on 7.10.1), so Prisma 8 and no `@prisma/client`.
- **`npx prisma@latest orm init --yes --target postgres --authoring psl`.** Run with `--yes`, so it did not wait for input. It created `src/prisma/contract.prisma`, `src/prisma/db.ts`, `prisma.config.ts`, `prisma-8.md`, and `.env.example`, and it added the Prisma packages.
- **Contract, emit, db init, query.** I wrote the models in `src/prisma/contract.prisma`, ran `npx prisma contract emit`, ran `npx prisma db init`, and queried through `db` from `./src/prisma/db`. The script calls `db.close()` at the end.
- **Verification steps.** `npm ls` shows the Prisma 8 packages and no `@prisma/client`; the tables exist; `npx tsx script.ts` prints the rows it wrote.

Not applied, or different:
- **The scaffold's example models were replaced**, not kept. The scaffold `User` had `username` and timestamps, and `Post` had timestamps; you did not ask for those, so the models are exactly the ones you specified.
- **Versions differ slightly.** `prisma` resolved to `8.0.0-rc.33`, while `@prisma/orm-postgres` resolved to `8.0.0-rc.23`, which is that package's published `latest`. Both are 8.x, but they are not the same rc. I did not see the toolchain crash the note mentions on `contract emit`; it worked on the first try.
- **`prisma skills sync` was not run.** The CLI warns that the agent skills are out of date. I did not run it because it would change files outside what you asked for.

## Changes to the project

- `package.json`: added `prisma` (dev), `@prisma/cli-engine` (dev), `@prisma/orm-postgres` and `dotenv` (runtime), and a `contract:emit` script. Added `prisma` as dev and `@prisma/orm-postgres` as runtime, as the init scaffold writes them.
- `tsconfig.json`: the init changed `module` from `ESNext` to `preserve` and added `"types": ["node"]`. `npx tsc --noEmit` passes.
- `.gitignore`: added `node_modules/` and `dist/` (the init appended these).
- New: `prisma.config.ts`, `prisma-8.md`, `.env.example`, `.gitattributes`, `package-lock.json`, `src/prisma/` (`contract.prisma`, `contract.json`, `contract.d.ts`, `db.ts`), and `script.ts`.
- `src/index.ts` (the in-memory blog) is unchanged.
- `.env` is unchanged; `DATABASE_URL` was already set. Its value is not printed here.

## Schema (`src/prisma/contract.prisma`)

```prisma
model User {
  id    Int     @id @default(autoincrement())
  email String  @unique
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

## Database

`npx prisma db init --dry-run --yes` planned five additive operations: create `User` and `Post`, a unique constraint on `User.email`, an index on `Post.authorId`, and the foreign key `Post_authorId_fkey`. I applied them with `npx prisma db init --yes`. The database was empty, so nothing else was touched. `psql` confirms `Post` and `User` exist in `public`.

## script.ts

Run with `npx tsx script.ts`. It:

1. Creates a user in a transaction with two posts: one published ("Hello, Prisma", with content) and one draft (no content, so `published` defaults to `false`).
2. Prints every user with their posts via `db.orm.public.User.include('posts').all()`.
3. Calls `db.close()`.

The email is `alice-<timestamp>@example.com`, because `User.email` is unique and a fixed address would fail on the second run. Each run adds one more user, so the output grows.

Last run (abridged): one user with two posts, `published: true` on the first and `false` on the second. `tsc --noEmit` passes.

## Not done

- Nothing was committed, pushed, deployed, or reported to any external service.

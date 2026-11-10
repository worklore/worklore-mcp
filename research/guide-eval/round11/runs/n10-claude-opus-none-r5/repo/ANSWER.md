# Adding Prisma ORM

## Version choice
- `npm view prisma dist-tags` shows `latest` pointing at **8.0.0-rc.33**. That's a release candidate published 2026-11-06, and it has **no matching `@prisma/client`** (installing `@prisma/client@8.0.0-rc.33` gives a 404).
- The current stable release is **7.10.1** (2026-10-15). It's `latest` for `@prisma/client` and `@prisma/adapter-pg`, and `prev` for `prisma`. The CLI and client versions must match, so I installed 7.10.1 for all three:
  - dev: `prisma@7.10.1`
  - runtime: `@prisma/client@7.10.1`, `@prisma/adapter-pg@7.10.1`, `dotenv`

## Files added or changed
- `prisma/schema.prisma`: the models. It uses the Prisma 7 `prisma-client` generator, which writes the client to `src/generated/prisma`.
  - `User`: `id` (autoincrement), `email` (`@unique`), `name String?`, `posts Post[]`
  - `Post`: `id`, `title`, `content String?`, `published Boolean @default(false)`, and a required `author` relation through `authorId`. Each post has exactly one author.
- `prisma.config.ts`: the Prisma 7 config file. It loads `.env` through `dotenv` and reads `DATABASE_URL`. In Prisma 7 the URL goes here, not in the schema.
- `prisma/migrations/<timestamp>_init/migration.sql`: the first migration.
- `script.ts`: creates a user with two posts (one published, one draft using the default) using a nested `create`. It then prints every user with their posts (`findMany({ include: { posts: true } })`). It connects through the `@prisma/adapter-pg` driver adapter, which Prisma 7 requires.
- `package.json`: the new dependencies, plus `db:generate` and `db:migrate` scripts.
- `.gitignore`: `src/generated/` is now ignored, since the client is a build artifact.
- `.env` and `src/index.ts` are unchanged.

## Commands run
```sh
npx prisma migrate dev --name init   # created the User and Post tables in the local Postgres from .env
npx prisma generate                  # Prisma 7's migrate dev no longer generates the client
npx tsx script.ts                    # ran successfully, output below
npx tsc --noEmit                     # passes
```

Output of `npx tsx script.ts`:
```
Created user: { id: 1, email: 'alice+1794274628513@example.com', name: 'Alice' }
[ { id: 1, email: 'alice+…@example.com', name: 'Alice',
    posts: [ { id: 1, title: 'Hello, Prisma', content: 'My first post.', published: true, authorId: 1 },
             { id: 2, title: 'Drafts are fine too', content: null, published: false, authorId: 1 } ] } ]
```

## Notes
- The email has a timestamp appended, so the script can run more than once without breaking the unique constraint. Every run adds another user, and all of them are printed.
- On a fresh clone, run `npm install && npm run db:generate` before `npx tsx script.ts`, because the generated client isn't committed. Your npm version blocked dependency install scripts, so I didn't rely on a `postinstall` hook.
- Nothing was committed, pushed or published.

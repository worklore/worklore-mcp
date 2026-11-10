# Adding Prisma ORM

## Version choice
`npm view prisma dist-tags` showed that the `latest` tag for **prisma** (the CLI) points to **8.0.0-rc.33**, a release candidate. There is no `@prisma/client` 8.x release at all, only `8.1.0-dev.*` builds, and `latest` for `@prisma/client` is **7.10.1**. Using the RC CLI would have meant pairing it with a client from a different major version, so I installed the newest stable release, **7.10.1**, for every Prisma package:

- `prisma@7.10.1` (dev dependency, the CLI)
- `@prisma/client@7.10.1`
- `@prisma/adapter-pg@7.10.1` (Prisma 7 connects to Postgres through a driver adapter)
- `dotenv` (loads `.env` for `prisma.config.ts` and `script.ts`)

Moving to Prisma 8 once it's stable will mean bumping these packages and checking its upgrade guide.

## Files
- `prisma/schema.prisma`: the data models. The generator is `prisma-client` (Prisma 7's generator), with its output in `src/generated/prisma`.
  - `User`: `id` (auto-increment), `email` (unique), `name` (optional), `posts`
  - `Post`: `id`, `title`, `content` (optional), `published` (defaults to `false`), plus `author`/`authorId`, a required relation to exactly one `User`
- `prisma.config.ts`: Prisma 7 config file. It points to the schema and the migrations folder and reads the database URL from `DATABASE_URL` in `.env`.
- `prisma/migrations/<timestamp>_init/migration.sql`: the first migration. It creates the `User` and `Post` tables, the unique index on email and the foreign key.
- `script.ts`: creates a user with two posts in one nested `create` (one published post, one draft with no content), then prints every user with their posts (`findMany({ include: { posts: true } })`).
- `.gitignore`: now also ignores `src/generated/`, the generated client.

`.env` is unchanged.

## Commands run
```bash
npm install -D prisma@7.10.1
npm install @prisma/client@7.10.1 @prisma/adapter-pg@7.10.1 dotenv
npx prisma migrate dev --name init   # created and applied the migration to the local DB
npx prisma generate                  # generated the client into src/generated/prisma
npx tsx script.ts                    # works; output below
npx tsc --noEmit -p .                # passes
```

## Running it
```bash
npx prisma generate   # required after a fresh clone, because the generated client is not committed
npx tsx script.ts
```
Email must be unique, so the script adds a timestamp to the email (`alice+<timestamp>@example.com`). That way it can be run repeatedly, and each run adds one more user with two posts. I ran it twice while testing, so the database now holds 2 users and 4 posts.

Sample output from the first run:
```
Created user: alice+1794273885084@example.com with 2 posts
[
  {
    id: 1,
    email: 'alice+1794273885084@example.com',
    name: 'Alice',
    posts: [
      { id: 1, title: 'Hello Prisma', content: 'My first post.', published: true, authorId: 1 },
      { id: 2, title: 'Draft ideas', content: null, published: false, authorId: 1 }
    ]
  }
]
```

## Notes
- This npm version blocks install scripts by default, so it skipped the `preinstall` scripts for `prisma` and `esbuild`. Nothing broke: the Prisma engines and tsx work without them.
- `src/index.ts`, which still stores data in memory, is untouched. Switching it to use Prisma would be the next step.

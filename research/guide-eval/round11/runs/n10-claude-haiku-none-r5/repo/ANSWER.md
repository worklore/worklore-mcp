# Prisma ORM setup

## Version choice

On npm, the `prisma` package's `latest` tag is currently `8.0.0-rc.33`, a release candidate. `@prisma/client`'s `latest` is the stable `7.10.1`. An 8.x CLI does not match a 7.x client, so I used the stable **7.10.1** line for everything:

- `prisma@7.10.1` (dev CLI, in `dependencies` in package.json)
- `@prisma/client@7.10.1`
- `@prisma/adapter-pg@7.10.1` (Prisma 7 requires a driver adapter)
- `dotenv` (to load `.env` for the CLI and script)

Versions are pinned exactly (`--save-exact`). The CLI's upgrade notice suggests 8.0.0-rc; I did not take it.

## Files

- `prisma/schema.prisma`: `User` (unique `email`, optional `name`, many `posts`) and `Post` (`title`, optional `content`, `published` defaulting to `false`, required `authorId` referencing one `User`). The generator outputs to `generated/prisma`, which is git-ignored.
- `prisma.config.ts`: sets the schema path, the migrations directory, and the datasource URL from `DATABASE_URL`.
- `prisma/migrations/<timestamp>_init/migration.sql`: the initial migration, which creates the `User` and `Post` tables, the unique index on `User.email`, and the foreign key `Post.authorId -> User.id`.
- `script.ts`: creates a user with two posts, then prints every user with their posts.

## Steps performed

1. Checked the database at `localhost:5435`. It was reachable and had no tables.
2. Installed the pinned packages.
3. `npx prisma validate` passed.
4. `npx prisma migrate dev --name init` created the tables in the database.
5. `npx prisma generate` produced the client in `generated/prisma`.
6. `npx tsx script.ts` ran successfully. `npx tsc --noEmit` passed.

## Running the script

```sh
npx tsx script.ts
```

Each run creates a new user with a timestamped email (`alice-<timestamp>@example.com`), so the script can be rerun without hitting the unique constraint on `email`. Because of this, each run adds one more user to the database. My verification runs added two users (ids 1 and 2) with two posts each.

## Notes

- Nothing was committed, deployed, published or sent to any external service.
- If the schema changes, run `npx prisma migrate dev` (to create and apply a migration) and then `npx prisma generate`.

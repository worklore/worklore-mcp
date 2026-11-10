# Prisma setup

- Installed npm's current `prisma@latest` (`8.0.0-rc.33`) and the Prisma 8 PostgreSQL ORM package (`@prisma/orm-postgres@latest`, `8.0.0-rc.23`). The setup also installed its CLI engine and `dotenv`.
- Defined `User` with a unique email, optional name, and posts, and `Post` with a required title and author, optional content, and `published` defaulting to `false` in `src/prisma/contract.prisma`.
- Emitted the Prisma contract and ran `npx prisma db init` against the local PostgreSQL URL in `.env`. This created both tables, the unique email constraint, and the author foreign key.
- Added `script.ts`. Run `npx tsx script.ts` to create one user and two posts, then print every user with all their posts. It uses a unique email on each run so it can be rerun.

Verified with `npx tsc --noEmit` and `npx tsx script.ts`.

## Colleague's note

The npm tag warning applied: `prisma@latest` is Prisma 8 while `@prisma/client@latest` remains 7.x. The Prisma 8 `orm init --yes --target postgres --authoring psl` setup, `contract.prisma` edits, `contract emit`, `db init`, Prisma 8 query API, and `db.close()` guidance applied. The earlier `contract emit` crash did not occur. The release candidate versions of the CLI and ORM package differ because those are their current npm `latest` tags.

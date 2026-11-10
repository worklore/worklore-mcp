# Prisma setup

Installed npm's current `prisma@latest` (`8.0.0-rc.33`) with the PostgreSQL ORM package. Initialized the Prisma 8 project, defined `User` and `Post` in `src/prisma/contract.prisma`, emitted the contract, and ran `npx prisma db init` against the local PostgreSQL URL in `.env`. The database now has the tables, unique email constraint, post author foreign key, and `published` default of `false`.

`script.ts` creates one user with two posts and prints every user with their posts. Run it with `npx tsx script.ts`. It uses a unique email each run so the example can be rerun. Verified with `npx tsc --noEmit` and `npx tsx script.ts`; both succeeded.

## Colleague's note

The npm `latest` tag pointing to Prisma 8, the `orm init --yes --target postgres --authoring psl` setup, the `@prisma/orm-postgres` package, the contract and `db.ts` paths, `contract emit`, `db init`, Prisma 8 query style, and `db.close()` all applied. The warning about interactive setup also applied, so setup used `--yes`. The reported `rc.29` toolchain crash did not occur with the current `rc.33` CLI. The note's `@prisma/client@latest` and `@prisma/adapter-pg@latest` versions were background context; this Prisma 8 setup does not use those packages.

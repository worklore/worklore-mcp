import { db } from './src/prisma/db';

async function main() {
  await db.orm.public.User.create({
    email: `example-${crypto.randomUUID()}@example.com`,
    name: 'Example User',
    posts: (posts) => posts.create([
      { title: 'First post', content: 'Hello from Prisma.' },
      { title: 'Second post', published: true },
    ]),
  });

  const users = await db.orm.public.User.include('posts').all();
  console.dir(users, { depth: null });
}

main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => db.close());

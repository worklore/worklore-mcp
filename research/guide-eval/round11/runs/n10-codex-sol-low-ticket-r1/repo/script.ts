import { randomUUID } from 'node:crypto';
import { db } from './src/prisma/db';

async function main() {
  await db.orm.public.User.create({
    email: `alice-${randomUUID()}@example.com`,
    name: 'Alice',
    posts: (posts) => posts.create([
      { title: 'First post', content: 'Hello from Prisma' },
      { title: 'Second post', published: true },
    ]),
  });

  const users = await db.orm.public.User.include('posts').all();
  console.dir(users, { depth: null });
}

try {
  await main();
} finally {
  await db.close();
}

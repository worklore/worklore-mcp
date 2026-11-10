import { randomUUID } from 'node:crypto';
import { db } from './src/prisma/db';

try {
  await db.orm.public.User.create({
    email: `writer-${randomUUID()}@example.com`,
    name: 'Example Writer',
    posts: (posts) => posts.create([
      { title: 'First post', content: 'Hello from Prisma.' },
      { title: 'Second post', published: true },
    ]),
  });

  const users = await db.orm.public.User.include('posts').all();
  console.dir(users, { depth: null });
} finally {
  await db.close();
}

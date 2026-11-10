import { randomUUID } from 'node:crypto';
import { db } from './src/prisma/db';

try {
  await db.orm.public.User.create({
    email: `demo-${randomUUID()}@example.com`,
    name: 'Demo User',
    posts: (posts) => posts.create([
      { title: 'First post', content: 'Hello from Prisma.' },
      { title: 'Second post', published: true },
    ]),
  });

  const users = await db.orm.public.User.include('posts').all();
  console.log(JSON.stringify(users, null, 2));
} finally {
  await db.close();
}

import { db } from './src/prisma/db';

try {
  const user = await db.orm.public.User.create({
    email: `user-${crypto.randomUUID()}@example.com`,
    name: 'Alice',
  });

  await db.orm.public.Post.create({
    title: 'First post',
    content: 'Hello from Prisma',
    authorId: user.id,
  });
  await db.orm.public.Post.create({
    title: 'Second post',
    authorId: user.id,
  });

  const users = await db.orm.public.User.include('posts').all();
  console.dir(users, { depth: null });
} finally {
  await db.close();
}

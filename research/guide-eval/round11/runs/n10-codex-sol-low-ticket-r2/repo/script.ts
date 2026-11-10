import { db } from './src/prisma/db';

try {
  const user = await db.orm.public.User.create({
    email: `writer-${Date.now()}@example.com`,
    name: 'Sample Writer',
  });

  await db.orm.public.Post.create({
    title: 'First post',
    content: 'Hello from Prisma.',
    authorId: user.id,
  });
  await db.orm.public.Post.create({
    title: 'Second post',
    authorId: user.id,
  });

  const users = await db.orm.public.User.include('posts').all();
  console.log(JSON.stringify(users, null, 2));
} finally {
  await db.close();
}

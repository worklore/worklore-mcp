import { db } from './src/prisma/db.js';

async function main() {
  const email = `user_${Date.now()}@example.com`;

  const user = await db.orm.public.User.create({
    email,
    name: 'Alice',
  });

  await db.orm.public.Post.create({
    title: 'First Post',
    content: 'Hello, world!',
    published: true,
    authorId: user.id,
  });

  await db.orm.public.Post.create({
    title: 'Second Post',
    content: 'Draft content',
    published: false,
    authorId: user.id,
  });

  const users = await db.orm.public.User.include('posts').all();
  console.log(JSON.stringify(users, null, 2));

  await db.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

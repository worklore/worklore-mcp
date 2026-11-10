import { db } from './src/prisma/db';

async function main() {
  const timestamp = Date.now();
  const user = await db.orm.public.User.create({
    email: `alice_${timestamp}@example.com`,
    name: 'Alice',
  });

  await db.orm.public.Post.create({
    title: 'First Post',
    content: 'This is the first post content.',
    published: true,
    authorId: user.id,
  });

  await db.orm.public.Post.create({
    title: 'Second Post',
    content: 'This is the second post content.',
    authorId: user.id,
  });

  const usersWithPosts = await db.orm.public.User.include('posts').all();

  console.dir(usersWithPosts, { depth: null });
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await db.close();
  });

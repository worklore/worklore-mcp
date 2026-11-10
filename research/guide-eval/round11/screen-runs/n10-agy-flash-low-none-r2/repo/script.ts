import { db } from './prisma/db';

async function main() {
  const email = `alice_${Date.now()}@example.com`;

  // Create a user with two posts
  const user = await db.orm.public.User.create({
    email,
    name: 'Alice',
  });

  await db.orm.public.Post.create({
    title: 'First Post',
    content: 'Hello World! This is my first post.',
    published: true,
    authorId: user.id,
  });

  await db.orm.public.Post.create({
    title: 'Second Post',
    content: 'Another thought in draft mode.',
    published: false,
    authorId: user.id,
  });

  // Query and print every user together with their posts
  const allUsersWithPosts = await db.orm.public.User.include('posts').all();

  console.dir(allUsersWithPosts, { depth: null });

  await db.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

import { db } from './src/prisma/db.ts';

async function main() {
  const email = `user-${Date.now()}@example.com`;

  // Create a user
  const user = await db.orm.public.User.create({
    email,
    name: 'Alice',
  });

  // Create two posts for this user
  await db.orm.public.Post.create({
    title: 'First Post',
    content: 'Hello, world! This is my first post.',
    published: true,
    authorId: user.id,
  });

  await db.orm.public.Post.create({
    title: 'Second Post',
    content: 'Drafting another interesting update.',
    published: false,
    authorId: user.id,
  });

  // Query and print every user together with their posts
  const usersWithPosts = await db.orm.public.User.include('posts').all();
  console.log(JSON.stringify(usersWithPosts, null, 2));
}

try {
  await main();
} finally {
  await db.close();
}

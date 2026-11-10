import { db } from './src/prisma/db';

// Create one user with two posts.
const alice = await db.orm.public.User.create({
  email: 'alice@example.com',
  name: 'Alice',
});

await db.orm.public.Post.create({
  title: 'Hello, Prisma',
  content: 'My first post, written through Prisma ORM.',
  published: true,
  authorId: alice.id,
});

await db.orm.public.Post.create({
  title: 'Draft notes',
  authorId: alice.id,
});

// Print every user together with their posts.
const users = await db.orm.public.User.include('posts').all();
console.log(JSON.stringify(users, null, 2));

await db.close();

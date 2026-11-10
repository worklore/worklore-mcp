import { db } from './src/prisma/db';

// Creates one user with two posts (in one transaction), then prints every user with their posts.
// The email carries a timestamp so the script can be re-run: User.email is unique.
const email = `alice-${Date.now()}@example.com`;

await db.transaction(async (tx) => {
  const user = await tx.orm.public.User.create({ email, name: 'Alice' });
  await tx.orm.public.Post.create({
    title: 'Hello, Prisma',
    content: 'The first post.',
    published: true,
    authorId: user.id,
  });
  await tx.orm.public.Post.create({
    title: 'A draft',
    authorId: user.id, // content is optional; published defaults to false
  });
});

const users = await db.orm.public.User.include('posts').all();
console.dir(users, { depth: null });

await db.close();

import { db } from './src/prisma/db';

async function main() {
  // create user
  const user = await db.orm.public.User.create({ email: 'alice@example.com', name: 'Alice' });
  console.log('Created user', user);
  // create two posts
  await db.orm.public.Post.create({ title: 'First', authorId: user.id });
  await db.orm.public.Post.create({ title: 'Second', authorId: user.id, content: 'Second content', published: true });
  // fetch users with posts
  const users = await db.orm.public.User.include('posts').all();
  console.log('All users with posts:', JSON.stringify(users, null, 2));
  await db.close();
}

main().catch(e => console.error(e));

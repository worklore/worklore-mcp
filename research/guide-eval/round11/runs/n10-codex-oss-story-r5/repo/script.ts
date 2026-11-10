import 'dotenv/config';
import { db } from './src/prisma/db';

async function main() {
  // Create a user with two posts (one published)
  const user = await db.orm.public.User.create({
    email: 'alice@example.com',
    name: 'Alice',
    posts: {
      create: [
        { title: 'First post', content: 'Hello world', published: true },
        { title: 'Second post', content: 'Another post' },
      ],
    },
  });

  // Retrieve all users with their posts
  const users = await db.orm.public.User.include('posts').all();

  console.log('Created user:', user);
  console.log('All users with posts:');
  console.dir(users, { depth: null });
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

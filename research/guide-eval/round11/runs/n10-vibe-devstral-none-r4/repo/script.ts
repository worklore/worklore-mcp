import 'dotenv/config';
import { db } from './src/prisma/db';

async function main() {
  // Delete existing data to start fresh
  await db.orm.public.Post.deleteAll();
  await db.orm.public.User.deleteAll();

  // Create a user with two posts
  const user = await db.orm.public.User.create({
    email: 'test@example.com',
    name: 'Test User',
  });

  // Create two posts for the user
  await db.orm.public.Post.create({
    title: 'First Post',
    content: 'This is my first post',
    published: false,
    authorId: user.id,
  });

  await db.orm.public.Post.create({
    title: 'Second Post',
    content: 'This is my second post',
    published: true,
    authorId: user.id,
  });

  console.log('Created user with two posts');

  // Query all users with their posts
  const usersWithPosts = await db.orm.public.User.include('posts').all();

  console.log('\nAll users with their posts:');
  for (const user of usersWithPosts) {
    console.log(`\nUser: ${user.name || 'Unnamed'} (${user.email})`);
    console.log('Posts:');
    for (const post of user.posts) {
      console.log(`  - ${post.title} (published: ${post.published})`);
      if (post.content) {
        console.log(`    Content: ${post.content}`);
      }
    }
  }
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });

import 'dotenv/config';
import { db } from './src/prisma/db';

async function main() {
  // Delete existing data to ensure clean state
  await db.orm.public.Post.deleteAll();
  await db.orm.public.User.deleteAll();

  // Create a user first
  const user = await db.orm.public.User.create({
    email: 'alice@example.com',
    name: 'Alice',
  });

  console.log('Created user:', user);

  // Create two posts for the user
  const post1 = await db.orm.public.Post.create({
    title: 'First Post',
    content: 'This is my first post',
    published: false,
    authorId: user.id,
  });

  const post2 = await db.orm.public.Post.create({
    title: 'Second Post',
    content: 'This is my second post',
    published: true,
    authorId: user.id,
  });

  console.log('Created posts:', post1, post2);

  // Print every user together with their posts
  const allUsers = await db.orm.public.User.include('posts').all();

  console.log('\nAll users with their posts:');
  for (const u of allUsers) {
    console.log(`\nUser: ${u.name || 'Anonymous'} (${u.email})`);
    console.log('Posts:');
    for (const post of u.posts) {
      console.log(`  - ${post.title} (published: ${post.published})`);
      if (post.content) {
        console.log(`    Content: ${post.content}`);
      }
    }
  }

  await db.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

import 'dotenv/config';
import { db } from './src/prisma/db';

async function main() {
  // Check if user already exists, delete if so
  const existingUser = await db.orm.public.User.where({ email: 'alice@example.com' }).first();
  if (existingUser) {
    // Delete the user's posts first
    const posts = await db.orm.public.Post.where({ authorId: existingUser.id }).all();
    for (const post of posts) {
      await db.orm.public.Post.where({ id: post.id }).delete();
    }
    // Delete the user
    await db.orm.public.User.where({ id: existingUser.id }).delete();
  }

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
  const usersWithPosts = await db.orm.public.User.include('posts').all();
  
  console.log('\nAll users with their posts:');
  for (const user of usersWithPosts) {
    console.log(`\nUser: ${user.name || 'Anonymous'} (${user.email})`);
    console.log(`  Posts (${user.posts.length}):`);
    for (const post of user.posts) {
      console.log(`    - ${post.title} (published: ${post.published})`);
      if (post.content) {
        console.log(`      Content: ${post.content}`);
      }
    }
  }

  await db.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

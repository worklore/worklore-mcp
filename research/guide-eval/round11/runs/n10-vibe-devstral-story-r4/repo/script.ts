import { db } from './src/prisma/db';

async function main() {
  // Clean up existing data to ensure idempotency
  await db.orm.public.Post.deleteAll();
  await db.orm.public.User.deleteAll();

  // Create a user
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
  for (const u of usersWithPosts) {
    console.log(`\nUser ${u.id}: ${u.email}${u.name ? ` (${u.name})` : ''}`);
    console.log('  Posts:');
    for (const post of u.posts) {
      console.log(`    - ${post.title}${post.content ? `: ${post.content}` : ''} (published: ${post.published})`);
    }
  }

  await db.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

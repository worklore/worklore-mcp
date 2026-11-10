import { db } from './src/prisma/db';

async function main() {
  // Use a timestamp to ensure unique email each run
  const timestamp = Date.now();
  const email = `user_${timestamp}@example.com`;

  // Create a user first
  const user = await db.orm.public.User.create({
    email: email,
    name: 'Test User',
  });

  console.log('Created user:', user);

  // Create two posts for this user
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

  console.log('Created post 1:', post1);
  console.log('Created post 2:', post2);

  // Fetch all users with their posts
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

  await db.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

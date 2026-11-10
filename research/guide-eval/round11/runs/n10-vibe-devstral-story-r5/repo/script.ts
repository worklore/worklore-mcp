import { db } from './src/prisma/db';

async function main() {
  // Clear existing data to ensure clean run (delete posts first due to foreign key)
  await db.orm.public.Post.where({}).delete();
  await db.orm.public.User.where({}).delete();

  // Create a user
  const user = await db.orm.public.User.create({
    email: 'test@example.com',
    name: 'Test User',
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
    console.log(`\nUser: ${user.name || 'No name'} (${user.email})`);
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

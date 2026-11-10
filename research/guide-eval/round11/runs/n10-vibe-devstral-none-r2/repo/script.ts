import 'dotenv/config';
import { db } from './src/prisma/db';

async function main() {
  // Clean up any existing data
  await db.orm.public.Post.where({}).delete();
  await db.orm.public.User.where({}).delete();

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

  // Query all users with their posts
  const users = await db.orm.public.User.where({}).all();
  
  // Now query posts for each user
  const usersWithPosts = [];
  for (const user of users) {
    const posts = await db.orm.public.Post.where({ authorId: user.id }).all();
    usersWithPosts.push({ ...user, posts });
  }

  console.log('\nAll users with their posts:');
  for (const user of usersWithPosts) {
    console.log(`\nUser: ${user.email} (${user.name || 'No name'})`);
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

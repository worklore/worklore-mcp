import { db } from './src/prisma/db';

async function main() {
  const timestamp = Date.now();
  const user = await db.orm.public.User.create({
    email: `alice_${timestamp}@example.com`,
    name: 'Alice',
  });

  await db.orm.public.Post.create({
    title: 'First Post',
    content: 'Content of the first post',
    published: true,
    authorId: user.id,
  });

  await db.orm.public.Post.create({
    title: 'Second Post',
    content: 'Content of the second post',
    authorId: user.id,
  });

  const usersWithPosts = await db.orm.public.User.include('posts').all();

  console.log('Users and their posts:');
  for (const u of usersWithPosts) {
    console.log(`User: ${u.name ?? 'No name'} (${u.email}) [ID: ${u.id}]`);
    if (u.posts && u.posts.length > 0) {
      for (const p of u.posts) {
        console.log(
          `  - Post #${p.id}: "${p.title}" (published: ${p.published}) - ${p.content ?? 'No content'}`
        );
      }
    } else {
      console.log('  (no posts)');
    }
  }
}

main()
  .catch((err) => {
    console.error(err);
    process.exit(1);
  })
  .finally(async () => {
    await db.close();
  });

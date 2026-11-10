import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  // Clean up existing data for repeatable runs
  await prisma.post.deleteMany();
  await prisma.user.deleteMany();

  // Create a user with two posts
  const user = await prisma.user.create({
    data: {
      email: 'alice@example.com',
      name: 'Alice',
      posts: {
        create: [
          { title: 'First Post', content: 'Hello world!', published: true },
          { title: 'Second Post', content: 'Another post', published: false },
        ],
      },
    },
    include: { posts: true },
  });

  console.log('Created user:', user);

  // Fetch and print all users with their posts
  const users = await prisma.user.findMany({ include: { posts: true } });
  console.log('All users with posts:');
  for (const u of users) {
    console.log(`- ${u.email} (${u.name ?? 'no name'}):`);
    for (const p of u.posts) {
      console.log(`  * ${p.title} [${p.published ? 'published' : 'draft'}]`);
    }
  }
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

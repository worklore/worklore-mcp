import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  // Create a user with two posts
  const user = await prisma.user.create({
    data: {
      email: 'alice@example.com',
      name: 'Alice',
      posts: {
        create: [
          { title: 'First Post', content: 'Hello world!', published: false },
          { title: 'Second Post', content: 'Another post', published: false },
        ],
      },
    },
    include: { posts: true },
  });

  console.log('Created user:', user);

  // Fetch all users with their posts
  const allUsers = await prisma.user.findMany({
    include: { posts: true },
  });

  console.log('All users with posts:');
  for (const u of allUsers) {
    console.log(`- ${u.email} (${u.name ?? 'No name'})`);
    for (const p of u.posts) {
      console.log(`  • ${p.title} - published: ${p.published}`);
    }
  }
}

main()
  .catch((e) => {
    console.error(e);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

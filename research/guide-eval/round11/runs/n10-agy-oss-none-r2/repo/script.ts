import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  // Clean up any existing data (optional)
  await prisma.post.deleteMany();
  await prisma.user.deleteMany();

  // Create a user with two posts
  const user = await prisma.user.create({
    data: {
      email: 'alice@example.com',
      name: 'Alice',
      posts: {
        create: [
          {
            title: 'First Post',
            content: 'Hello world!',
            published: true,
          },
          {
            title: 'Draft Post',
            // content omitted (optional)
            // published defaults to false
          },
        ],
      },
    },
    include: { posts: true },
  });

  console.log('Created user with posts:', user);

  // Fetch all users with their posts
  const allUsers = await prisma.user.findMany({
    include: { posts: true },
  });

  console.log('\nAll users with posts:');
  for (const u of allUsers) {
    console.log(`User ${u.id} – ${u.email}${u.name ? ' (' + u.name + ')' : ''}`);
    for (const p of u.posts) {
      console.log(`  Post ${p.id}: ${p.title} – published: ${p.published}`);
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

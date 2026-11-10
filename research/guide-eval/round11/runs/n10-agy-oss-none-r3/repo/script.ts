import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  // Create a user with two posts using nested writes
  const user = await prisma.user.create({
    data: {
      email: 'alice@example.com',
      name: 'Alice',
      posts: {
        create: [
          {
            title: 'First post',
            content: 'Hello world!',
          },
          {
            title: 'Second post',
            // content is optional, leaving it undefined
          },
        ],
      },
    },
  });
  console.log('Created user:', user);

  // Retrieve all users with their posts
  const users = await prisma.user.findMany({
    include: {
      posts: true,
    },
  });

  console.log('\nAll users with their posts:');
  for (const u of users) {
    console.log(`User: ${u.email} (id=${u.id})`);
    if (u.name) console.log(`  Name: ${u.name}`);
    for (const p of u.posts) {
      console.log(`  Post: ${p.title} (published=${p.published})`);
      if (p.content) console.log(`    Content: ${p.content}`);
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

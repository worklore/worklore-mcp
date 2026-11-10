import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  // Create a user with two posts
  const user = await prisma.user.create({
    data: {
      email: 'user@example.com',
      name: 'Test User',
      posts: {
        create: [
          {
            title: 'First Post',
            content: 'This is my first post',
            published: false,
          },
          {
            title: 'Second Post',
            content: 'This is my second post',
            published: true,
          },
        ],
      },
    },
  });

  console.log('Created user with posts:');
  console.log('User:', {
    id: user.id,
    email: user.email,
    name: user.name,
  });

  // Fetch all users with their posts
  const usersWithPosts = await prisma.user.findMany({
    include: {
      posts: true,
    },
  });

  console.log('\nAll users with their posts:');
  for (const user of usersWithPosts) {
    console.log(`\nUser ${user.id}: ${user.email} (${user.name || 'no name'})`);
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
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

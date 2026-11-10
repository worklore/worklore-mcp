import { PrismaClient } from '@prisma/client';
import { PrismaPg } from '@prisma/adapter-pg';
import { Pool } from 'pg';

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const adapter = new PrismaPg(pool);
const prisma = new PrismaClient({ adapter });

async function main() {
  // Create a user with two posts
  const user = await prisma.user.create({
    data: {
      email: 'alice@example.com',
      name: 'Alice',
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
    include: {
      posts: true,
    },
  });

  console.log('Created user with posts:');
  console.log(JSON.stringify(user, null, 2));

  // Print every user together with their posts
  const allUsers = await prisma.user.findMany({
    include: {
      posts: true,
    },
  });

  console.log('\nAll users with their posts:');
  console.log(JSON.stringify(allUsers, null, 2));
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

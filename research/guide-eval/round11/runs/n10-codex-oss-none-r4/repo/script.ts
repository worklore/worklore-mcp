import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  // Create a user with two posts
  await prisma.user.create({
    data: {
      email: "alice@example.com",
      name: "Alice",
      posts: {
        create: [
          { title: "First post", content: "Hello world" },
          { title: "Second post", published: true },
        ],
      },
    },
  });

  // Fetch and print all users with their posts
  const users = await prisma.user.findMany({
    include: { posts: true },
  });
  console.dir(users, { depth: null });
}

main()
  .catch((e) => console.error(e))
  .finally(async () => {
    await prisma.$disconnect();
  });

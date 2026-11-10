import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  // Create a user with two posts
  const user = await prisma.user.create({
    data: {
      email: "alice@example.com",
      name: "Alice",
      posts: {
        create: [
          { title: "First post", content: "Hello world" },
          { title: "Second post" }, // content is optional
        ],
      },
    },
    include: { posts: true },
  });
  console.log("Created user with posts:", user);

  // Fetch and print every user with their posts
  const allUsers = await prisma.user.findMany({
    include: { posts: true },
  });
  console.log("All users with posts:");
  console.dir(allUsers, { depth: null });
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });


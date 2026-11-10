// script.ts
// This script creates a user with two posts and prints all users with their posts.

import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  // Create a user with two posts using nested writes
  const user = await prisma.user.create({
    data: {
      email: "alice@example.com",
      name: "Alice",
      posts: {
        create: [
          { title: "First Post", content: "Hello world!", published: true },
          { title: "Second Post", content: "Another post", published: false },
        ],
      },
    },
  });
  console.log("Created user:", user);

  // Fetch and print all users with their posts
  const users = await prisma.user.findMany({
    include: { posts: true },
    orderBy: { id: "asc" },
  });

  console.log("\nAll users and their posts:");
  for (const u of users) {
    console.log(`User ${u.id} - ${u.email} (${u.name ?? "no name"})`);
    for (const p of u.posts) {
      console.log(`  Post ${p.id}: ${p.title} (published: ${p.published})`);
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

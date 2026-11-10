import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./generated/prisma/client.js";

const prisma = new PrismaClient({
  adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL! }),
});

try {
  await prisma.user.create({
    data: {
      email: `reader-${crypto.randomUUID()}@example.com`,
      name: "Reader",
      posts: {
        create: [
          { title: "First post", content: "Hello from Prisma" },
          { title: "Second post", published: true },
        ],
      },
    },
  });

  const users = await prisma.user.findMany({ include: { posts: true } });
  console.log(JSON.stringify(users, null, 2));
} finally {
  await prisma.$disconnect();
}

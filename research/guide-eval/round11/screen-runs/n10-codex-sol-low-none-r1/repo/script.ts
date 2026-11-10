import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./generated/prisma/client.js";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL! });
const prisma = new PrismaClient({ adapter });

try {
  await prisma.user.create({
    data: {
      email: `writer-${crypto.randomUUID()}@example.com`,
      name: "Writer",
      posts: {
        create: [
          { title: "First post", content: "Hello, world!" },
          { title: "Second post" },
        ],
      },
    },
  });

  const users = await prisma.user.findMany({ include: { posts: true } });
  console.log(JSON.stringify(users, null, 2));
} finally {
  await prisma.$disconnect();
}

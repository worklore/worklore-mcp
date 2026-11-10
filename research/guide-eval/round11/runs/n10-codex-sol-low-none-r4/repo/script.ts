import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./generated/prisma/client";

const connectionString = process.env.DATABASE_URL;
if (!connectionString) throw new Error("DATABASE_URL is required");

const prisma = new PrismaClient({ adapter: new PrismaPg({ connectionString }) });

try {
  await prisma.user.create({
    data: {
      email: `demo-${Date.now()}@example.com`,
      name: "Demo User",
      posts: {
        create: [
          { title: "First post", content: "Hello from Prisma" },
          { title: "Second post", published: true },
        ],
      },
    },
  });

  console.log(JSON.stringify(await prisma.user.findMany({ include: { posts: true } }), null, 2));
} finally {
  await prisma.$disconnect();
}

import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./src/generated/prisma/client.js";

const prisma = new PrismaClient({
  adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL }),
});

async function main() {
  await prisma.user.create({
    data: {
      email: `example-${crypto.randomUUID()}@example.com`,
      name: "Example User",
      posts: {
        create: [
          { title: "First post", content: "Hello from Prisma" },
          { title: "Second post", published: true },
        ],
      },
    },
  });

  const users = await prisma.user.findMany({ include: { posts: true } });
  console.dir(users, { depth: null });
}

main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());

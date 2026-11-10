import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./src/generated/prisma/client";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL! });
const prisma = new PrismaClient({ adapter });

async function main() {
  const email = `alice+${Date.now()}@example.com`;
  const user = await prisma.user.create({
    data: {
      email,
      name: "Alice",
      posts: {
        create: [
          { title: "Hello Prisma", content: "My first post", published: true },
          { title: "Draft thoughts" },
        ],
      },
    },
  });
  console.log("Created user:", user);

  const users = await prisma.user.findMany({ include: { posts: true } });
  console.dir(users, { depth: null });
}

main()
  .catch((e) => {
    console.error(e);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());

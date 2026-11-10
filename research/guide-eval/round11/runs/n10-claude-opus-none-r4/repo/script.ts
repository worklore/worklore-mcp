import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./src/generated/prisma/client";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL! });
const prisma = new PrismaClient({ adapter });

async function main() {
  // upsert keeps the script re-runnable despite the unique email constraint
  const user = await prisma.user.upsert({
    where: { email: "alice@example.com" },
    update: {},
    create: {
      email: "alice@example.com",
      name: "Alice",
      posts: {
        create: [
          { title: "Hello, Prisma", content: "My first post.", published: true },
          { title: "Draft thoughts" },
        ],
      },
    },
  });
  console.log("User:", user);

  const users = await prisma.user.findMany({ include: { posts: true } });
  console.dir(users, { depth: null });
}

main()
  .catch((e) => {
    console.error(e);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());

import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./src/generated/prisma/client";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL! });
const prisma = new PrismaClient({ adapter });

async function main() {
  // Unique email per run so the script can be executed repeatedly.
  const user = await prisma.user.create({
    data: {
      email: `alice+${Date.now()}@example.com`,
      name: "Alice",
      posts: {
        create: [
          { title: "Hello, Prisma", content: "My first post.", published: true },
          { title: "Draft ideas" },
        ],
      },
    },
    include: { posts: true },
  });
  console.log("Created user:", user.email);

  const users = await prisma.user.findMany({ include: { posts: true }, orderBy: { id: "asc" } });
  console.dir(users, { depth: null });
}

main()
  .catch((e) => {
    console.error(e);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());

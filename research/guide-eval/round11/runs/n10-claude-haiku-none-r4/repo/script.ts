import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./generated/prisma/client";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
const prisma = new PrismaClient({ adapter });

async function main() {
  // A unique email per run, so the script can be re-run without hitting the unique constraint.
  const email = `user-${Date.now()}@example.com`;

  await prisma.user.create({
    data: {
      email,
      name: "Example User",
      posts: {
        create: [
          { title: "First post", content: "Hello, world!", published: true },
          { title: "Draft", content: "Work in progress" },
        ],
      },
    },
  });

  const users = await prisma.user.findMany({
    include: { posts: true },
    orderBy: { id: "asc" },
  });

  console.log(JSON.stringify(users, null, 2));
}

main()
  .catch((err) => {
    console.error(err);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());

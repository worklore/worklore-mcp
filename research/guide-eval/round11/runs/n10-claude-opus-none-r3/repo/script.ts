import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./src/generated/prisma/client";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL! });
const prisma = new PrismaClient({ adapter });

async function main() {
  // Email is unique, so add a timestamp to let the script run more than once.
  const user = await prisma.user.create({
    data: {
      email: `alice+${Date.now()}@example.com`,
      name: "Alice",
      posts: {
        create: [
          { title: "Hello Prisma", content: "My first post.", published: true },
          { title: "Draft ideas" }, // no content; published defaults to false
        ],
      },
    },
    include: { posts: true },
  });
  console.log("Created user:", user.email, `with ${user.posts.length} posts`);

  const users = await prisma.user.findMany({
    include: { posts: true },
    orderBy: { id: "asc" },
  });
  console.dir(users, { depth: null });
}

main()
  .catch((e) => {
    console.error(e);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());

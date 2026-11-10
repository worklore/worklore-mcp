import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./src/generated/prisma/client.js";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL! });
const prisma = new PrismaClient({ adapter });

async function main() {
  // Unique email per run so the script can be executed repeatedly.
  const email = `author-${Date.now()}@example.com`;

  await prisma.user.create({
    data: {
      email,
      name: "Example Author",
      posts: {
        create: [
          { title: "First post", content: "Hello from Prisma", published: true },
          { title: "Draft post" },
        ],
      },
    },
  });

  const users = await prisma.user.findMany({
    include: { posts: true },
    orderBy: { id: "asc" },
  });

  for (const user of users) {
    console.log(`${user.id} ${user.email} (${user.name ?? "no name"})`);
    if (user.posts.length === 0) {
      console.log("  (no posts)");
    }
    for (const post of user.posts) {
      console.log(
        `  - [${post.id}] ${post.title} | published=${post.published} | content=${post.content ?? "null"}`,
      );
    }
  }
}

main()
  .catch((err) => {
    console.error(err);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());

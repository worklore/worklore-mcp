import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./generated/prisma/client";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL! });
const prisma = new PrismaClient({ adapter });

async function main() {
  // Unique email per run, so the script can be executed repeatedly.
  const email = `alice-${Date.now()}@example.com`;

  await prisma.user.create({
    data: {
      email,
      name: "Alice",
      posts: {
        create: [
          { title: "Hello world", content: "My first post", published: true },
          { title: "Draft", content: "Work in progress" },
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
        `  - [${post.published ? "published" : "draft"}] ${post.title}: ${post.content ?? ""}`,
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

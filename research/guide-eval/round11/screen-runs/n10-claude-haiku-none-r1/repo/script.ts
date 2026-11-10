import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./generated/prisma/client.js";

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  throw new Error("DATABASE_URL is not set");
}

const prisma = new PrismaClient({
  adapter: new PrismaPg({ connectionString }),
});

async function main() {
  const user = await prisma.user.create({
    data: {
      email: "alice@example.com",
      name: "Alice",
      posts: {
        create: [
          { title: "Hello world", content: "My first post", published: true },
          { title: "Draft", content: "Work in progress" },
        ],
      },
    },
  });
  console.log(`Created user ${user.id} (${user.email})`);

  const users = await prisma.user.findMany({
    include: { posts: true },
    orderBy: { id: "asc" },
  });

  for (const u of users) {
    console.log(`\nUser #${u.id} ${u.email}${u.name ? ` (${u.name})` : ""}`);
    if (u.posts.length === 0) {
      console.log("  (no posts)");
    }
    for (const p of u.posts) {
      console.log(
        `  - [${p.published ? "published" : "draft"}] ${p.title}${p.content ? `: ${p.content}` : ""}`,
      );
    }
  }
}

main()
  .catch((e) => {
    console.error(e);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());

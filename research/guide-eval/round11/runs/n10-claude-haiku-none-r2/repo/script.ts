import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./generated/prisma/client";

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  throw new Error("DATABASE_URL is not set (see .env)");
}

const prisma = new PrismaClient({
  adapter: new PrismaPg({ connectionString }),
});

async function main() {
  // Unique email per run so the script can be executed repeatedly.
  const email = `alice+${Date.now()}@example.com`;

  const user = await prisma.user.create({
    data: {
      email,
      name: "Alice",
      posts: {
        create: [
          { title: "Hello, world", content: "My first post.", published: true },
          { title: "Draft notes", content: "Not ready yet." },
        ],
      },
    },
    include: { posts: true },
  });
  console.log(`Created user ${user.id} (${user.email}) with ${user.posts.length} posts.\n`);

  const users = await prisma.user.findMany({
    include: { posts: { orderBy: { id: "asc" } } },
    orderBy: { id: "asc" },
  });

  console.log(`All users (${users.length}):`);
  for (const u of users) {
    console.log(`- [${u.id}] ${u.email} (${u.name ?? "no name"})`);
    if (u.posts.length === 0) {
      console.log("    (no posts)");
    }
    for (const p of u.posts) {
      console.log(
        `    - [${p.id}] "${p.title}" published=${p.published}${p.content ? ` content="${p.content}"` : ""}`,
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

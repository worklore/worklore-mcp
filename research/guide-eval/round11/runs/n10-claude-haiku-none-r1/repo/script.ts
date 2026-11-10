import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./src/generated/prisma/client";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
const prisma = new PrismaClient({ adapter });

async function main() {
  // Unique email per run so the script can be executed repeatedly.
  const email = `alice+${Date.now()}@example.com`;

  const user = await prisma.user.create({
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
  console.log(`Created user #${user.id} (${user.email}) with 2 posts.\n`);

  const users = await prisma.user.findMany({
    orderBy: { id: "asc" },
    include: { posts: { orderBy: { id: "asc" } } },
  });

  console.log(`All users (${users.length}):`);
  for (const u of users) {
    console.log(`- #${u.id} ${u.email} (${u.name ?? "no name"})`);
    if (u.posts.length === 0) console.log("    (no posts)");
    for (const p of u.posts) {
      console.log(
        `    • [${p.published ? "published" : "draft"}] #${p.id} ${p.title}${p.content ? ` — ${p.content}` : ""}`,
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

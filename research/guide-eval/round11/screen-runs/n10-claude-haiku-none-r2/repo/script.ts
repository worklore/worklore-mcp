import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./generated/prisma/client";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
const prisma = new PrismaClient({ adapter });

async function main() {
  // Unique email per run so the script can be executed repeatedly.
  const email = `user-${Date.now()}@example.com`;

  const user = await prisma.user.create({
    data: {
      email,
      name: "Example User",
      posts: {
        create: [
          { title: "First post", content: "Hello from Prisma", published: true },
          { title: "Draft", content: "Not published yet" },
        ],
      },
    },
  });
  console.log(`Created user ${user.id} (${user.email}) with 2 posts\n`);

  const users = await prisma.user.findMany({
    include: { posts: { orderBy: { id: "asc" } } },
    orderBy: { id: "asc" },
  });

  console.log(`All users (${users.length}):`);
  for (const u of users) {
    console.log(`- [${u.id}] ${u.email} (${u.name ?? "no name"})`);
    for (const p of u.posts) {
      console.log(`    · [${p.id}] ${p.title} | published: ${p.published} | content: ${p.content ?? "-"}`);
    }
    if (u.posts.length === 0) console.log("    (no posts)");
  }
}

main()
  .catch((err) => {
    console.error(err);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());

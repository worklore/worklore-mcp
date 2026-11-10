import { db } from "./src/prisma/db";

async function main() {
  // Create a user with two posts
  await db.orm.public.User.create({
    data: {
      email: "alice@example.com",
      name: "Alice",
      posts: {
        create: [
          { title: "First post", content: "Hello world", published: false },
          { title: "Second post", content: "Another post", published: false },
        ],
      },
    },
  });

  // Fetch and print all users with their posts
  const users = await db.orm.public.User.findMany({
    include: { posts: true },
  });

  console.dir(users, { depth: null });

  // Close the DB connection if a close method exists
  if (typeof (db as any).close === "function") {
    await (db as any).close();
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

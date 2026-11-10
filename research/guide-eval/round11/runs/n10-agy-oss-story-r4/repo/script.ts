// script.ts
import { db } from "./src/prisma/db";

async function main() {
  // Create a user with two posts
  await db.orm.public.User.create({
    data: {
      email: "alice@example.com",
      name: "Alice",
      posts: {
        create: [
          { title: "First Post", content: "Hello world", published: false },
          { title: "Second Post", content: "Another post", published: false },
        ],
      },
    },
  });

  // Retrieve all users with their posts
  const users = await db.orm.public.User.findMany({
    include: { posts: true },
  });

  console.log("All users with posts:");
  console.dir(users, { depth: null });

  await db.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

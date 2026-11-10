// script.ts
// Creates a user with two posts and prints all users with their posts.
// Run with: npx tsx script.ts

import { db } from "./src/prisma/db";

async function main() {
  // Create a user with two posts
  const createdUser = await db.orm.public.User.create({
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
    include: { posts: true },
  });

  console.log("Created user with posts:", createdUser);

  // Fetch and print all users with their posts
  const users = await db.orm.public.User.findMany({
    include: { posts: true },
  });

  console.log("All users and their posts:");
  console.dir(users, { depth: null });
}

main()
  .catch((e) => {
    console.error("Error:", e);
  })
  .finally(() => {
    // Close the DB connection if the client provides a close method
    // @ts-ignore
    if (typeof db.close === "function") {
      // @ts-ignore
      db.close();
    }
  });

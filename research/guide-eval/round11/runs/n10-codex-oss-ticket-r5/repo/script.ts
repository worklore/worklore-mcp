import { db } from "./src/prisma/db";

async function main() {
  // Create a user with two posts in a single nested create operation.
  await db.orm.public.User.create({
    email: "alice@example.com",
    name: "Alice",
    posts: {
      create: [
        { title: "First post", content: "Hello world!" },
        { title: "Second post", content: "Another entry" },
      ],
    },
  });

  // Retrieve all users together with their posts.
  const users = await db.orm.public.User.include("posts").all();
  console.log(JSON.stringify(users, null, 2));
}

await main();

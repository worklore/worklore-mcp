import { db } from "./src/prisma/db";

async function main() {
  // Create a user with two posts in a single transaction.
  await db.orm.public.User.create({
    email: "alice@example.com",
    name: "Alice",
    posts: {
      create: [
        { title: "First post", content: "Hello world" },
        { title: "Second post", content: "Another post" },
      ],
    },
  });

  // Retrieve every user together with their posts.
  const users = await db.orm.public.User.include("posts").all();
  console.dir(users, { depth: null });
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});


import { db } from "./src/prisma/db";

/**
 * Demonstrates creating a user with two posts and printing all users with
 * their posts.
 */
async function main() {
  // Clean slate for idempotent runs.
  await db.orm.public.Post.where({}).deleteAll();
  await db.orm.public.User.where({}).deleteAll();

  // Create a user and two associated posts in a single call.
  const user = await db.orm.public.User.create({
    email: "alice@example.com",
    name: "Alice",
    posts: (p) =>
      p.create([
        { title: "First post", content: "Hello world", published: false },
        { title: "Second post", content: "Another post", published: true },
      ]),
  });

  console.log("Created user:", user);

  // Fetch every user together with their posts.
  const users = await db.orm.public.User.include("posts").all();
  console.log("All users with posts:", JSON.stringify(users, null, 2));

  await db.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});


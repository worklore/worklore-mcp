import { db } from "./src/prisma/db";

async function main() {
  // Create a user with two posts (one unpublished, one published).
  await db.orm.public.User.create({
    data: {
      email: "alice@example.com",
      name: "Alice",
      posts: {
        create: [
          { title: "First post", content: "Hello world", published: false },
          { title: "Second post", content: "Another post", published: true },
        ],
      },
    },
  });

  // Fetch all users together with their posts.
  const users = await db.orm.public.User.include("posts").all();
  console.log(JSON.stringify(users, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});


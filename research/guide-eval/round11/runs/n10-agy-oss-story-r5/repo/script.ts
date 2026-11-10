// script.ts
import { db } from "./src/prisma/db";

async function main() {
  // Create a user with two posts
  const user = await db.orm.public.User.create({
    data: {
      email: "alice@example.com",
      name: "Alice",
      posts: {
        create: [
          { title: "First Post", content: "Hello world!" },
          { title: "Second Post", content: "Another post" },
        ],
      },
    },
    include: { posts: true },
  });

  console.log("Created user:", user);

  // Fetch all users with their posts
  const allUsers = await db.orm.public.User.findMany({
    include: { posts: true },
  });

  console.log("All users with their posts:");
  for (const u of allUsers) {
    console.log(`User ${u.id} (${u.email}) - ${u.name ?? "<no name>"}`);
    for (const p of u.posts) {
      console.log(`  Post ${p.id}: ${p.title} (published: ${p.published})`);
    }
  }
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await db.$close?.(); // close connection if needed
  });

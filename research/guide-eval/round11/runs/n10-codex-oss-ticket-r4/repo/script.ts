import { db } from "./src/prisma/db";

// Helper to run the demo and exit cleanly
async function main() {
  // Create a user with two posts. If the user already exists (unique email), ignore the error.
  try {
    await db.orm.public.User.create({
      data: {
        email: "alice@example.com",
        name: "Alice",
        posts: {
          create: [
            { title: "First post", content: "Hello world", published: true },
            { title: "Second post" },
          ],
        },
      },
    });
  } catch (e) {
    // If the user already exists, Prisma will throw a unique‑constraint error.
    // We swallow it because the demo can be rerun.
    // eslint-disable-next-line no-console
    console.error("Create error (ignored if duplicate):", e instanceof Error ? e.message : e);
  }

  // Fetch every user together with their posts.
  const users = await db.orm.public.User.all();
  // Print the result in a readable format.
  console.log(JSON.stringify(users, null, 2));
}

// Run the script.
main()
  .catch((err) => {
    console.error("Unexpected error:", err);
    process.exit(1);
  })
  .finally(() => {
    // Close the connection pool.
    // `db.close()` is not a method; we use the runtime's close if needed.
    // The Prisma client will close when the process exits.
  });


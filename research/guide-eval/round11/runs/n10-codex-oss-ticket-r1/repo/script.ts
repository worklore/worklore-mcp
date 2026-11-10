import { db } from "./src/prisma/db";

// Top‑level async entry point (supported by tsx)
async function main() {
  // Create a user (email unique, name optional)
  const alice = await db.orm.public.User.create({
    email: "alice@example.com",
    name: "Alice",
  });

  // Create two posts belonging to the user
  await db.orm.public.Post.create({
    title: "First post",
    content: "Hello world",
    published: false,
    authorId: alice.id,
  });

  await db.orm.public.Post.create({
    title: "Second post",
    content: "Another post",
    published: false,
    authorId: alice.id,
  });

  // Fetch every user together with their posts
  const users = await db.orm.public.User.include("posts").all();
  console.log(JSON.stringify(users, null, 2));

  // Gracefully shut down the client if a close method exists
  // (orm‑postgres runtime provides a close function)
  // eslint-disable-next-line @typescript-eslint/no‑unsafe‑call
  if (typeof (db as any).close === "function") {
    // @ts-ignore – close may be undefined in some runtimes
    await (db as any).close();
  }
}

main().catch((e) => {
  console.error("Script failed:", e);
  process.exit(1);
});


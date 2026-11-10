import { db } from "./src/prisma/db";

// Create one user with two posts, atomically.
// The email is suffixed with a timestamp so re-running the script doesn't hit the unique constraint on User.email.
const email = `alice+${Date.now()}@example.com`;

await db.transaction(async (tx) => {
  const user = await tx.orm.public.User.create({ email, name: "Alice" });
  await tx.orm.public.Post.create({ title: "Hello, Prisma", content: "First post", authorId: user.id });
  await tx.orm.public.Post.create({ title: "Draft", published: false, authorId: user.id });
});

// Print every user together with their posts.
const users = await db.orm.public.User.include("posts").all();
console.log(JSON.stringify(users, null, 2));

await db.close();

import { db } from "./src/prisma/db";

// Unique per run, so the script can be executed more than once without hitting the unique email constraint.
const email = `alice+${Date.now()}@example.com`;

const user = await db.orm.public.User.create({ email, name: "Alice" });

await db.orm.public.Post.create({
  title: "Hello, Prisma",
  content: "My first post.",
  published: true,
  authorId: user.id,
});

await db.orm.public.Post.create({
  title: "Draft",
  authorId: user.id,
});

const users = await db.orm.public.User.include("posts").all();

console.log(JSON.stringify(users, null, 2));

await db.close();

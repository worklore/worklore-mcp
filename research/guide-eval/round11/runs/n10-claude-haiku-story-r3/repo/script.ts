import { db } from "./src/prisma/db";

// Unique suffix so the script can be re-run without violating User.email uniqueness.
const email = `alice-${Date.now()}@example.com`;

const user = await db.orm.public.User.create({ email, name: "Alice" });

await db.orm.public.Post.create({
  title: "Hello world",
  content: "My first post",
  published: true,
  authorId: user.id,
});
await db.orm.public.Post.create({
  title: "Draft",
  authorId: user.id, // published defaults to false
});

const users = await db.orm.public.User.include("posts").all();
console.log(JSON.stringify(users, null, 2));

await db.close();

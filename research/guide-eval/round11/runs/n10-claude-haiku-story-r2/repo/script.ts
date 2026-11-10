import { db } from "./src/prisma/db";

// A fresh email on every run, because User.email is unique.
const email = `alice-${Date.now()}@example.com`;

const user = await db.orm.public.User.create({ email, name: "Alice" });

await db.orm.public.Post.create({
  title: "First post",
  content: "Hello from Prisma 8",
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

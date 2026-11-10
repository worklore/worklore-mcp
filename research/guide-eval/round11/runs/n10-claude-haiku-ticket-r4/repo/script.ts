import { db } from "./src/prisma/db";

const alice = await db.orm.public.User.create({
  email: `alice-${Date.now()}@example.com`,
  name: "Alice",
});

await db.orm.public.Post.create({
  title: "First post",
  content: "Hello from Prisma",
  published: true,
  authorId: alice.id,
});

await db.orm.public.Post.create({
  title: "Draft",
  authorId: alice.id,
});

const users = await db.orm.public.User.include("posts").all();
console.log(JSON.stringify(users, null, 2));

await db.close();

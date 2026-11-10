import { db } from "./src/prisma/db";

// Create a user with two posts.
const user = await db.orm.public.User.create({
  email: "alice@example.com",
  name: "Alice",
});

await db.orm.public.Post.create({
  title: "Hello, Prisma",
  content: "My first post.",
  published: true,
  authorId: user.id,
});

await db.orm.public.Post.create({
  title: "Draft notes",
  authorId: user.id,
});

// Print every user together with their posts.
const users = await db.orm.public.User.include("posts").all();
console.log(JSON.stringify(users, null, 2));

await db.close();

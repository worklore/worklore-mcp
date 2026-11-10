import { db } from "./src/prisma/db";

async function main() {
  const user = await db.orm.public.User.create({
    email: "alice@example.com",
    name: "Alice",
  });

  await db.orm.public.Post.create({
    title: "Hello, world",
    content: "My first post.",
    published: true,
    authorId: user.id,
  });

  await db.orm.public.Post.create({
    title: "Draft notes",
    authorId: user.id,
  });

  const users = await db.orm.public.User.include("posts").all();
  console.log(JSON.stringify(users, null, 2));
}

main().finally(() => db.close());

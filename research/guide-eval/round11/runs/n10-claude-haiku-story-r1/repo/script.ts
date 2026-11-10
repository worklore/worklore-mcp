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
  for (const u of users) {
    console.log(u);
  }

  await db.close();
}

main().catch(async (err) => {
  console.error(err);
  await db.close();
  process.exit(1);
});

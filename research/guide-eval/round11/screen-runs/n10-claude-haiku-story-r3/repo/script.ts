import { db } from "./src/prisma/db";

async function main() {
  const alice = await db.orm.public.User.create({
    email: "alice@example.com",
    name: "Alice",
  });

  await db.orm.public.Post.create({
    title: "Hello, world",
    content: "My first post.",
    published: true,
    authorId: alice.id,
  });
  await db.orm.public.Post.create({
    title: "Draft notes",
    authorId: alice.id,
  });

  const users = await db.orm.public.User.include("posts").all();
  for (const user of users) {
    console.log(`${user.name ?? "(no name)"} <${user.email}>`);
    for (const post of user.posts) {
      console.log(`  - [${post.published ? "published" : "draft"}] ${post.title}`);
    }
  }
}

main()
  .catch((err) => {
    console.error(err);
    process.exitCode = 1;
  })
  .finally(() => db.close());

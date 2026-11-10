import { db } from "./src/prisma/db";

try {
  // Create a user with two posts.
  const author = await db.orm.public.User.create({
    email: "alice@example.com",
    name: "Alice",
  });

  await db.orm.public.Post.create({
    title: "First post",
    content: "Hello from Prisma 8",
    published: true,
    authorId: author.id,
  });
  await db.orm.public.Post.create({
    title: "Draft",
    authorId: author.id,
  });

  // Print every user together with their posts.
  const users = await db.orm.public.User.include("posts").all();
  for (const user of users) {
    console.log(`User #${user.id} ${user.email}${user.name ? ` (${user.name})` : ""}`);
    for (const post of user.posts) {
      console.log(
        `  - [${post.published ? "published" : "draft"}] ${post.title}${
          post.content ? `: ${post.content}` : ""
        }`,
      );
    }
  }
} finally {
  await db.close();
}

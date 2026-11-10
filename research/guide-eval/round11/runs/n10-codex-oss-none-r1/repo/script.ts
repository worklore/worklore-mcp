import "dotenv/config";
import { db } from "./src/prisma/db";

async function main() {
  // Use ORM façade for Postgres namespace
  const orm = db.orm.public;
  // Create a user first
  const user = await orm.User.create({
    email: "alice@example.com",
    name: "Alice",
  });
  // Create two posts linked to the user via authorId
  await orm.Post.create({
    title: "First Post",
    content: "Hello world",
    authorId: user.id,
  });
  await orm.Post.create({
    title: "Second Post",
    authorId: user.id,
  });
  console.log("Created user and posts:", user);

  // Fetch and print all users with their posts
  const allUsers = await orm.User.findMany();
  console.log("All users:");
  for (const u of allUsers) {
    const posts = await orm.Post.findMany({ where: { authorId: u.id } });
    console.log({ ...u, posts });
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

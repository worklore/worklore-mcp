import { db } from "./src/prisma/db";

async function main() {
  // Connect to the database using the serverless client.
  await using conn = await db.connect({ url: process.env["DATABASE_URL"]! });

  // Create a user.
  const user = await conn.orm.public.User.create({
    email: "alice@example.com",
    name: "Alice",
  });

  // Create two posts for the user.
  await conn.orm.public.Post.create({
    title: "First post",
    content: "Hello world",
    authorId: user.id,
  });

  await conn.orm.public.Post.create({
    title: "Second post",
    content: "Another post",
    published: true,
    authorId: user.id,
  });

  // Fetch all users with their posts.
  const users = await conn.orm.public.User.select(
    "id",
    "email",
    "name",
    "posts",
  ).all();

  console.log(JSON.stringify(users, null, 2));
}

await main();


import { db } from "./src/prisma/db";

// Unique email per run, so the script can be re-run without hitting the unique constraint on User.email.
const email = `alice+${Date.now()}@example.com`;

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

for (const u of users) {
  console.log(`${u.id} ${u.email} ${u.name ?? "(no name)"}`);
  for (const p of u.posts) {
    console.log(`  - [${p.published ? "published" : "draft"}] ${p.title}${p.content ? `: ${p.content}` : ""}`);
  }
}

await db.close();

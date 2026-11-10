import { db } from "./src/prisma/db";

const user = await db.orm.public.User.create({ email: `alice+${Date.now()}@example.com`, name: "Alice" });
await db.orm.public.Post.create({ title: "Hello", content: "First post", authorId: user.id });
await db.orm.public.Post.create({ title: "Second", authorId: user.id });
const users = await db.orm.public.User.include("posts").all();
console.log(JSON.stringify(users, null, 2));
await db.close();

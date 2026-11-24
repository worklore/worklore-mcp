import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./src/generated/prisma/client";

const prisma = new PrismaClient({ adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL! }) });
const user = await prisma.user.create({
  data: { email: `alice+${Date.now()}@example.com`, name: "Alice", posts: { create: [{ title: "Hello", content: "First post" }, { title: "Second" }] } },
});
const users = await prisma.user.findMany({ include: { posts: true } });
console.log(JSON.stringify(users, null, 2));
await prisma.$disconnect();

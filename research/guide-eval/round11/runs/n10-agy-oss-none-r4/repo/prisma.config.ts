import { definePrismaConfig } from "prisma/config";

export default definePrismaConfig({
  orm: {
    adapter: { type: "prisma-client-js" },
    family: { type: "postgresql" },
    target: { directory: "./prisma" },
  },
  skills: {
    agents: ["claude", "cursor", "agents", "devin"],
  },
});

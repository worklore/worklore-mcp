import { definePrismaConfig } from "prisma/config";

export default definePrismaConfig({
  skills: {
    agents: ["claude", "cursor", "agents", "devin"],
  },
  orm: {
    // Basic Prisma client generation targeting PostgreSQL
    adapter: {
      type: "prisma-client-js",
    },
    target: {
      provider: "postgresql",
    },
    // No preview features needed for this simple schema
    previewFeatures: [],
  },
});

/**
 * Prisma seed entrypoint (docs/51-T6).
 *
 * Triggered by `prisma db seed` (configured via `prisma.seed` in
 * package.json). Currently only seeds Strategy Presets; further seeders
 * can be appended here.
 */

import { PrismaClient } from "@prisma/client";
import { seedPresets } from "./seedPresets.js";

async function main() {
  const prisma = new PrismaClient();
  try {
    const presetResults = await seedPresets(prisma);
    // eslint-disable-next-line no-console
    console.log("seedPresets:", presetResults);
  } finally {
    await prisma.$disconnect();
  }
}

main().catch((err) => {
  // eslint-disable-next-line no-console
  console.error("seed failed:", err);
  process.exit(1);
});

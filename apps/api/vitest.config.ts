import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    root: ".",
    include: ["tests/**/*.test.ts"],
    environment: "node",
    globals: false,
    testTimeout: 10_000,
    reporters: ["default"],
  },
});

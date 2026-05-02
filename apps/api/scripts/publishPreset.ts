#!/usr/bin/env tsx
/**
 * Promote a StrategyPreset to PUBLIC (or roll it back to PRIVATE) —
 * admin CLI tool for the visibility-flip step shared by docs/53-T4 and
 * docs/54-T1..T3 closing.
 *
 * Why a script and not an HTTP endpoint:
 *   - Visibility flips are infrequent and audited (commit / chat record).
 *   - There is no admin UI for `/presets` today — a CLI is the cleanest
 *     interface that does not require building one.
 *   - The script writes a one-line audit summary to stdout that
 *     operators can paste into the gate companion-doc.
 *
 * Usage:
 *   pnpm --filter @botmarketplace/api exec tsx scripts/publishPreset.ts \
 *     --slug adaptive-regime --visibility PUBLIC
 *
 *   pnpm --filter @botmarketplace/api exec tsx scripts/publishPreset.ts \
 *     --slug adaptive-regime --visibility PRIVATE --dry-run
 *
 * Lookup is by slug (unique). Visibility values must match the Prisma
 * `PresetVisibility` enum — currently `PRIVATE` | `PUBLIC`. The BETA
 * value lands with docs/55-T6; this script will accept it without
 * source-edit once the enum is extended (we read the allowed values
 * from `@prisma/client` at runtime).
 *
 * The script is idempotent: setting the visibility a preset already has
 * is a no-op with a clear "already at <visibility>, no change" message.
 */

import { PrismaClient, PresetVisibility } from "@prisma/client";

// ---------------------------------------------------------------------------
// CLI argument parsing
// ---------------------------------------------------------------------------

export interface ParsedArgs {
  slug?: string;
  visibility?: string;
  dryRun: boolean;
}

export function parseArgs(argv: readonly string[]): ParsedArgs {
  const out: ParsedArgs = { dryRun: false };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--slug") out.slug = argv[++i];
    else if (arg === "--visibility") out.visibility = argv[++i];
    else if (arg === "--dry-run") out.dryRun = true;
  }
  return out;
}

/** All allowed visibility values, read from the generated enum so the
 *  script picks up additions (BETA in 55-T6) without an edit here. */
export function allowedVisibilities(): string[] {
  return Object.values(PresetVisibility);
}

// ---------------------------------------------------------------------------
// Core logic — exported so tests can drive it without spawning a process
// ---------------------------------------------------------------------------

export type PublishOutcome =
  | { kind: "noop";       slug: string; visibility: PresetVisibility }
  | { kind: "changed";    slug: string; from: PresetVisibility; to: PresetVisibility; dryRun: boolean }
  | { kind: "not_found";  slug: string }
  | { kind: "bad_input";  reason: string };

export interface PublishArgs {
  slug?: string;
  visibility?: string;
  dryRun?: boolean;
  /** Inject a Prisma client (mock in tests). */
  prisma: Pick<PrismaClient, "strategyPreset">;
  /** Write audit messages somewhere (defaults to console.log). */
  log?: (line: string) => void;
}

export async function publishPreset(args: PublishArgs): Promise<PublishOutcome> {
  const log = args.log ?? ((line: string) => console.log(line));

  if (!args.slug) {
    return { kind: "bad_input", reason: "--slug <slug> is required" };
  }
  if (!args.visibility) {
    return {
      kind: "bad_input",
      reason: `--visibility <${allowedVisibilities().join("|")}> is required`,
    };
  }
  if (!allowedVisibilities().includes(args.visibility)) {
    return {
      kind: "bad_input",
      reason: `invalid visibility "${args.visibility}", expected one of: ${allowedVisibilities().join(", ")}`,
    };
  }

  const target = args.visibility as PresetVisibility;
  const dryRun = args.dryRun ?? false;

  const before = await args.prisma.strategyPreset.findUnique({
    where: { slug: args.slug },
    select: { slug: true, name: true, visibility: true, updatedAt: true },
  });
  if (!before) {
    return { kind: "not_found", slug: args.slug };
  }

  if (before.visibility === target) {
    log(`[publishPreset] ${before.slug} already at ${target}, no change`);
    return { kind: "noop", slug: before.slug, visibility: target };
  }

  log(`[publishPreset] mode=${dryRun ? "dry-run" : "apply"}`);
  log(`[publishPreset] ${before.slug}: ${before.visibility} → ${target}`);
  log(`[publishPreset]   name: "${before.name}"`);
  log(`[publishPreset]   updatedAt(before): ${before.updatedAt.toISOString()}`);

  if (dryRun) {
    log("[publishPreset] dry-run — no changes written");
    return { kind: "changed", slug: before.slug, from: before.visibility, to: target, dryRun: true };
  }

  const updated = await args.prisma.strategyPreset.update({
    where: { slug: before.slug },
    data: { visibility: target },
    select: { slug: true, visibility: true, updatedAt: true },
  });
  log(
    `[publishPreset] OK ${updated.slug} → ${updated.visibility} ` +
    `(updatedAt=${updated.updatedAt.toISOString()})`,
  );
  return { kind: "changed", slug: updated.slug, from: before.visibility, to: target, dryRun: false };
}

// ---------------------------------------------------------------------------
// Process entry point — only when invoked directly, not on import.
// ---------------------------------------------------------------------------

const isDirectInvocation = (() => {
  // Run when this file is the entry point. Vitest imports the module —
  // we must not call main() under that scenario.
  if (typeof process === "undefined" || !process.argv[1]) return false;
  const entry = process.argv[1];
  return entry.endsWith("publishPreset.ts") || entry.endsWith("publishPreset.js");
})();

if (isDirectInvocation) {
  const cli = parseArgs(process.argv.slice(2));
  const prisma = new PrismaClient();
  publishPreset({ ...cli, prisma })
    .then((out) => {
      switch (out.kind) {
        case "bad_input":
          console.error(`error: ${out.reason}`);
          process.exit(1);
        case "not_found":
          console.error(`error: preset not found: ${out.slug}`);
          process.exit(2);
        default:
          // success — message already logged inside publishPreset.
          process.exit(0);
      }
    })
    .catch((err) => {
      console.error(err);
      process.exit(1);
    })
    .finally(() => prisma.$disconnect());
}

import * as Sentry from "@sentry/node";

let initialized = false;

/**
 * Initialize Sentry if `SENTRY_DSN` is set. No-op otherwise, so tests and
 * local dev work without any Sentry project configured.
 *
 * Must be called before any Fastify instance is created so instrumentation
 * can attach (see @sentry/node v10 docs).
 */
export function initSentry(): void {
  if (initialized) return;
  const dsn = process.env.SENTRY_DSN;
  if (!dsn) return;

  Sentry.init({
    dsn,
    environment: process.env.NODE_ENV ?? "development",
    release: process.env.SENTRY_RELEASE,
    tracesSampleRate: Number(process.env.SENTRY_TRACES_SAMPLE_RATE ?? "0"),
  });
  initialized = true;
}

export function isSentryEnabled(): boolean {
  return initialized;
}

export { Sentry };

import pino from "pino";

/**
 * Shared application logger.
 *
 * Fastify's built-in logger handles request logging with pino-pretty in dev.
 * This logger is for non-request contexts (workers, background jobs, etc.).
 */
export const logger = pino({
  level: process.env.LOG_LEVEL || "info",
});

export default logger;

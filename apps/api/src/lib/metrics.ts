import { Registry, collectDefaultMetrics, Counter, Histogram } from "prom-client";

export const register = new Registry();
register.setDefaultLabels({ app: "botmarket-api" });
collectDefaultMetrics({ register });

export const intentCreatedTotal = new Counter({
  name: "botmarket_intent_created_total",
  help: "Total number of bot intents created.",
  registers: [register],
});

export const intentFilledTotal = new Counter({
  name: "botmarket_intent_filled_total",
  help: "Total number of bot intents that reached FILLED state.",
  registers: [register],
});

export const intentFailedTotal = new Counter({
  name: "botmarket_intent_failed_total",
  help: "Total number of bot intents that reached FAILED state.",
  registers: [register],
});

export const stalePendingCancelledTotal = new Counter({
  name: "botmarket_stale_pending_cancelled_total",
  help: "PENDING intents cancelled by the periodic reconciliation sweep.",
  registers: [register],
});

export const httpRequestDurationSeconds = new Histogram({
  name: "botmarket_http_request_duration_seconds",
  help: "HTTP request duration in seconds.",
  labelNames: ["method", "route", "status"],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [register],
});

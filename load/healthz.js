// @ts-nocheck -- this file is run by the k6 runtime (Go), not Node/tsc.
import http from "k6/http";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

// Baseline health-endpoint probe (§5.2 / docs/37).
// Purpose: confirm base HTTP stack capacity + establish a p99 floor
// that other scenarios can be compared against.
//
// Usage:
//   BASE_URL=http://localhost:4000 k6 run load/healthz.js
//   BASE_URL=https://staging.botmarketplace.store k6 run load/healthz.js
//
// Output: JSON summary goes to stdout; p95/p99 latencies + error rate in
// the trend metrics.

const BASE_URL = __ENV.BASE_URL || "http://localhost:4000";

const healthzLatency = new Trend("healthz_latency_ms", true);

export const options = {
  scenarios: {
    baseline: {
      executor: "constant-arrival-rate",
      rate: 50,                // 50 req/s
      timeUnit: "1s",
      duration: "30s",
      preAllocatedVUs: 10,
      maxVUs: 50,
    },
  },
  thresholds: {
    // p99 on /healthz should be < 250ms even under 50 rps — it's just a
    // DB-less handler returning a constant object.
    http_req_duration: ["p(95)<100", "p(99)<250"],
    http_req_failed:   ["rate<0.001"],
  },
};

export default function () {
  const res = http.get(`${BASE_URL}/healthz`);
  healthzLatency.add(res.timings.duration);
  check(res, {
    "status is 200": (r) => r.status === 200,
    "body has status=ok": (r) => r.json("status") === "ok",
  });
  sleep(0.02); // target ~50 rps per VU with constant-arrival-rate
}

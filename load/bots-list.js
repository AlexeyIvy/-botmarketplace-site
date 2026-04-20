// @ts-nocheck -- k6 runtime, not Node.
import http from "k6/http";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

// /api/v1/bots load scenario (§5.2 / docs/37).
//
// Authenticated read path — representative of dashboard traffic where a
// logged-in user polls their bot list. Exercises JWT verify + Prisma
// findMany + workspace resolution.
//
// Usage:
//   BASE_URL=http://localhost:4000 \
//     LOAD_EMAIL=seed@example.com LOAD_PASS=Seed1234! \
//     k6 run load/bots-list.js
//
// The script logs in once in setup() and reuses the access token for VUs.

const BASE_URL = __ENV.BASE_URL  || "http://localhost:4000";
const EMAIL    = __ENV.LOAD_EMAIL || "seed@example.com";
const PASSWORD = __ENV.LOAD_PASS  || "Seed1234!";

const listLatency = new Trend("bots_list_latency_ms", true);

export const options = {
  scenarios: {
    dashboard_poll: {
      executor: "ramping-vus",
      startVUs: 5,
      stages: [
        { target: 10, duration: "30s" },
        { target: 25, duration: "30s" },
        { target: 50, duration: "30s" },
        { target: 0,  duration: "10s" },
      ],
    },
  },
  thresholds: {
    // Authenticated JSON list should stay under 500ms p99 up to 50 VUs.
    http_req_duration: ["p(95)<300", "p(99)<500"],
    http_req_failed:   ["rate<0.005"],
  },
};

export function setup() {
  const res = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email: EMAIL, password: PASSWORD }),
    { headers: { "Content-Type": "application/json" } },
  );
  if (res.status !== 200) {
    throw new Error(`setup: login failed status=${res.status} body=${res.body}`);
  }
  return {
    accessToken: res.json("accessToken"),
    workspaceId: res.json("workspaceId"),
  };
}

export default function (data) {
  const headers = {
    Authorization:   `Bearer ${data.accessToken}`,
    "X-Workspace-Id": data.workspaceId,
  };
  const res = http.get(`${BASE_URL}/api/v1/bots`, { headers });
  listLatency.add(res.timings.duration);
  check(res, {
    "status is 200":    (r) => r.status === 200,
    "body is array":    (r) => Array.isArray(r.json()) || Array.isArray(r.json("items")),
  });
  sleep(1); // model a dashboard polling once per second per user
}

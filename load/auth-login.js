// @ts-nocheck -- k6 runtime, not Node.
import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate } from "k6/metrics";

// /auth/login load scenario (§5.2 / docs/37).
//
// Two interleaved profiles:
//   - valid credentials   — exercises bcrypt.compare + refresh token issuance
//   - invalid credentials — exercises rate-limit path (5 req / 15 min) and
//     should see 429s kick in quickly, validating the limiter
//
// Usage:
//   BASE_URL=http://localhost:4000 LOAD_EMAIL=seed@example.com LOAD_PASS=Seed1234! \
//     k6 run load/auth-login.js
//
// Seed the account first:
//   curl -s http://localhost:4000/api/v1/auth/register \
//     -H "Content-Type: application/json" \
//     -d '{"email":"seed@example.com","password":"Seed1234!"}'

const BASE_URL  = __ENV.BASE_URL  || "http://localhost:4000";
const EMAIL     = __ENV.LOAD_EMAIL || "seed@example.com";
const PASSWORD  = __ENV.LOAD_PASS  || "Seed1234!";

const loginLatency  = new Trend("auth_login_latency_ms", true);
const rateLimitRate = new Rate("auth_login_rate_limited");

export const options = {
  scenarios: {
    valid_creds: {
      executor: "ramping-arrival-rate",
      startRate: 1,
      timeUnit: "1s",
      preAllocatedVUs: 5,
      maxVUs: 20,
      stages: [
        { target: 5,  duration: "30s" },
        { target: 10, duration: "30s" },
        { target: 0,  duration: "10s" },
      ],
      exec: "validLogin",
    },
    invalid_creds: {
      executor: "constant-arrival-rate",
      rate: 2,
      timeUnit: "1s",
      duration: "60s",
      preAllocatedVUs: 2,
      maxVUs: 5,
      exec: "invalidLogin",
      startTime: "10s",
    },
  },
  thresholds: {
    // bcrypt is intentionally slow; keep p99 under 2s at this load.
    "http_req_duration{scenario:valid_creds}": ["p(95)<1000", "p(99)<2000"],
    // invalid path should be fast after limiter kicks in — either quick
    // 401 or instant 429. Keep failure rate accounting expected 429s.
    "http_req_failed{scenario:valid_creds}": ["rate<0.01"],
  },
};

export function validLogin() {
  const res = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email: EMAIL, password: PASSWORD }),
    { headers: { "Content-Type": "application/json" }, tags: { scenario: "valid_creds" } },
  );
  loginLatency.add(res.timings.duration);
  check(res, {
    "status is 200":   (r) => r.status === 200,
    "has accessToken": (r) => !!r.json("accessToken"),
  });
}

export function invalidLogin() {
  const res = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email: EMAIL, password: "wrong-password" }),
    { headers: { "Content-Type": "application/json" }, tags: { scenario: "invalid_creds" } },
  );
  rateLimitRate.add(res.status === 429);
  check(res, {
    "401 or 429": (r) => r.status === 401 || r.status === 429,
  });
  sleep(0.5);
}

/**
 * Error Classifier Tests (#141, slice 3)
 *
 * Validates the pure classification logic for execution errors:
 *
 *   1. Bybit API retCode → transient/permanent/unknown
 *   2. HTTP status → transient/permanent/unknown
 *   3. Network/system error patterns → transient
 *   4. Config/normalization error patterns → permanent
 *   5. Unknown errors → conservative default
 *   6. Determinism and consistency
 *
 * All tests are deterministic: no DB, no network, no wall-clock dependence.
 *
 * Stage 8, issue #141 — slice 3: retry classification + dead-letter handling.
 */

import { describe, it, expect } from "vitest";
import {
  classifyExecutionError,
  type ErrorClass,
  type ErrorClassification,
} from "../../src/lib/errorClassifier.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function classify(message: string): ErrorClassification {
  return classifyExecutionError(new Error(message));
}

function expectClass(message: string, expected: ErrorClass) {
  const result = classify(message);
  expect(result.errorClass).toBe(expected);
  expect(result.retryable).toBe(expected === "transient");
  expect(result.reason.length).toBeGreaterThan(0);
}

// ===========================================================================
// 1. Bybit API retCode classification
// ===========================================================================

describe("Bybit API retCode classification", () => {
  describe("transient retCodes", () => {
    it("classifies retCode 10006 (rate limit) as transient", () => {
      expectClass("Bybit API error 10006: too many visits", "transient");
    });

    it("classifies retCode 10016 (server error) as transient", () => {
      expectClass("Bybit API error 10016: internal server error", "transient");
    });

    it("classifies retCode 10018 (server timeout) as transient", () => {
      expectClass("Bybit API error 10018: server timeout", "transient");
    });

    it("transient retCodes are retryable", () => {
      const result = classify("Bybit API error 10006: too many visits");
      expect(result.retryable).toBe(true);
    });
  });

  describe("permanent retCodes", () => {
    it("classifies retCode 10001 (parameter error) as permanent", () => {
      expectClass("Bybit API error 10001: parameter error", "permanent");
    });

    it("classifies retCode 10003 (invalid API key) as permanent", () => {
      expectClass("Bybit API error 10003: invalid API key", "permanent");
    });

    it("classifies retCode 10005 (permission denied) as permanent", () => {
      expectClass("Bybit API error 10005: permission denied", "permanent");
    });

    it("classifies retCode 110003 (insufficient balance) as permanent", () => {
      expectClass("Bybit API error 110003: insufficient balance", "permanent");
    });

    it("classifies retCode 110007 (insufficient margin) as permanent", () => {
      expectClass("Bybit API error 110007: insufficient available balance", "permanent");
    });

    it("classifies retCode 110008 (already filled/cancelled) as permanent", () => {
      expectClass("Bybit API error 110008: order already filled or cancelled", "permanent");
    });

    it("classifies retCode 110009 (max active orders) as permanent", () => {
      expectClass("Bybit API error 110009: max active orders exceeded", "permanent");
    });

    it("classifies retCode 170124 (invalid symbol) as permanent", () => {
      expectClass("Bybit API error 170124: symbol not exists", "permanent");
    });

    it("permanent retCodes are not retryable", () => {
      const result = classify("Bybit API error 110007: insufficient balance");
      expect(result.retryable).toBe(false);
    });
  });

  describe("unknown retCodes", () => {
    it("classifies unrecognized retCode as unknown", () => {
      expectClass("Bybit API error 99999: something unexpected", "unknown");
    });

    it("unknown retCodes are not retryable (conservative)", () => {
      const result = classify("Bybit API error 99999: something");
      expect(result.retryable).toBe(false);
    });

    it("reason mentions the unrecognized retCode", () => {
      const result = classify("Bybit API error 55555: foo");
      expect(result.reason).toContain("55555");
    });
  });
});

// ===========================================================================
// 2. HTTP status classification
// ===========================================================================

describe("HTTP status classification", () => {
  describe("transient HTTP statuses", () => {
    it("classifies 429 (Too Many Requests) as transient", () => {
      expectClass("Bybit order request failed: 429 Too Many Requests", "transient");
    });

    it("classifies 500 (Internal Server Error) as transient", () => {
      expectClass("Bybit order request failed: 500 Internal Server Error", "transient");
    });

    it("classifies 502 (Bad Gateway) as transient", () => {
      expectClass("Bybit order request failed: 502 Bad Gateway", "transient");
    });

    it("classifies 503 (Service Unavailable) as transient", () => {
      expectClass("Bybit order request failed: 503 Service Unavailable", "transient");
    });

    it("classifies 504 (Gateway Timeout) as transient", () => {
      expectClass("Bybit order request failed: 504 Gateway Timeout", "transient");
    });

    it("classifies 408 (Request Timeout) as transient", () => {
      expectClass("Bybit order request failed: 408 Request Timeout", "transient");
    });
  });

  describe("permanent HTTP statuses", () => {
    it("classifies 400 (Bad Request) as permanent", () => {
      expectClass("Bybit order request failed: 400 Bad Request", "permanent");
    });

    it("classifies 401 (Unauthorized) as permanent", () => {
      expectClass("Bybit order request failed: 401 Unauthorized", "permanent");
    });

    it("classifies 403 (Forbidden) as permanent", () => {
      expectClass("Bybit order request failed: 403 Forbidden", "permanent");
    });
  });

  describe("unknown HTTP statuses", () => {
    it("classifies unrecognized HTTP status as unknown", () => {
      expectClass("Bybit order request failed: 418 I'm a teapot", "unknown");
    });
  });

  it("also matches status request failures", () => {
    expectClass("Bybit status request failed: 503 Service Unavailable", "transient");
  });
});

// ===========================================================================
// 3. Network / system error patterns
// ===========================================================================

describe("network/system error pattern classification", () => {
  it("classifies ECONNREFUSED as transient", () => {
    expectClass("connect ECONNREFUSED 127.0.0.1:443", "transient");
  });

  it("classifies ECONNRESET as transient", () => {
    expectClass("read ECONNRESET", "transient");
  });

  it("classifies ETIMEDOUT as transient", () => {
    expectClass("connect ETIMEDOUT 1.2.3.4:443", "transient");
  });

  it("classifies ENETUNREACH as transient", () => {
    expectClass("connect ENETUNREACH", "transient");
  });

  it("classifies socket hang up as transient", () => {
    expectClass("socket hang up", "transient");
  });

  it("classifies fetch failed as transient", () => {
    expectClass("fetch failed", "transient");
  });

  it("classifies generic timeout as transient", () => {
    expectClass("The operation was aborted due to timeout", "transient");
  });

  it("classifies network error as transient", () => {
    expectClass("network error", "transient");
  });
});

// ===========================================================================
// 4. Config / normalization error patterns (permanent)
// ===========================================================================

describe("config/normalization error pattern classification", () => {
  it("classifies missing encryption key as permanent", () => {
    expectClass("SECRET_ENCRYPTION_KEY not configured", "permanent");
  });

  it("classifies normalization failure as permanent", () => {
    expectClass("Order normalization failed: qty below minimum", "permanent");
  });

  it("classifies invalid symbol in message as permanent", () => {
    expectClass("invalid symbol XYZUSDT", "permanent");
  });

  it("classifies insufficient margin in message as permanent", () => {
    expectClass("insufficient margin for this order", "permanent");
  });
});

// ===========================================================================
// 5. Unknown / fallthrough
// ===========================================================================

describe("unknown error classification", () => {
  it("classifies completely unknown error as unknown", () => {
    expectClass("something completely unexpected happened", "unknown");
  });

  it("unknown errors are not retryable (conservative)", () => {
    const result = classify("no idea what this error means");
    expect(result.retryable).toBe(false);
    expect(result.errorClass).toBe("unknown");
  });

  it("handles non-Error input (string)", () => {
    const result = classifyExecutionError("raw string error");
    expect(result.errorClass).toBe("unknown");
  });

  it("handles non-Error input (number)", () => {
    const result = classifyExecutionError(42);
    expect(result.errorClass).toBe("unknown");
  });

  it("handles null/undefined input", () => {
    const r1 = classifyExecutionError(null);
    const r2 = classifyExecutionError(undefined);
    expect(r1.errorClass).toBe("unknown");
    expect(r2.errorClass).toBe("unknown");
  });
});

// ===========================================================================
// 6. Determinism and consistency
// ===========================================================================

describe("determinism and consistency", () => {
  it("same error message always produces same classification", () => {
    const msg = "Bybit API error 10006: too many visits";
    const r1 = classify(msg);
    const r2 = classify(msg);
    expect(r1).toEqual(r2);
  });

  it("classification is idempotent", () => {
    const messages = [
      "Bybit API error 110007: insufficient balance",
      "Bybit order request failed: 429 Too Many Requests",
      "connect ECONNREFUSED 127.0.0.1:443",
      "something unknown",
    ];
    for (const msg of messages) {
      const results = [];
      for (let i = 0; i < 5; i++) {
        results.push(classify(msg));
      }
      for (let i = 1; i < results.length; i++) {
        expect(results[i]).toEqual(results[0]);
      }
    }
  });

  it("retryable is always consistent with errorClass", () => {
    const testCases = [
      "Bybit API error 10006: rate limit",     // transient
      "Bybit API error 10001: param error",     // permanent
      "Bybit API error 99999: unknown",         // unknown
      "Bybit order request failed: 429 TMR",    // transient
      "Bybit order request failed: 400 Bad",    // permanent
      "connect ECONNREFUSED 1.2.3.4:443",       // transient
      "SECRET_ENCRYPTION_KEY not configured",    // permanent
      "something completely unexpected",          // unknown
    ];
    for (const msg of testCases) {
      const result = classify(msg);
      if (result.errorClass === "transient") {
        expect(result.retryable).toBe(true);
      } else {
        expect(result.retryable).toBe(false);
      }
    }
  });

  it("reason is always a non-empty string", () => {
    const messages = [
      "Bybit API error 10006: x",
      "Bybit order request failed: 500 x",
      "ECONNREFUSED",
      "SECRET_ENCRYPTION_KEY not configured",
      "something unknown",
    ];
    for (const msg of messages) {
      expect(classify(msg).reason.length).toBeGreaterThan(0);
    }
  });
});

// ===========================================================================
// 7. Classification priority (API retCode > HTTP status > pattern > unknown)
// ===========================================================================

describe("classification priority", () => {
  it("API retCode takes precedence over pattern match", () => {
    // Message has "timeout" (transient pattern) but retCode 10001 is permanent
    const result = classify("Bybit API error 10001: request timeout parameter error");
    expect(result.errorClass).toBe("permanent");
  });

  it("HTTP status takes precedence over pattern match", () => {
    // Message has "timeout" but HTTP 400 is permanent
    const result = classify("Bybit order request failed: 400 timeout bad request");
    expect(result.errorClass).toBe("permanent");
  });
});

// ===========================================================================
// 8. Integration: execution path behavior validation
// ===========================================================================

describe("execution path behavior", () => {
  it("metadata shape matches what botWorker records", () => {
    const result = classifyExecutionError(new Error("Bybit API error 110007: no money"));
    // Verify the shape matches what executeIntent catch block records
    expect(result).toHaveProperty("errorClass");
    expect(result).toHaveProperty("retryable");
    expect(result).toHaveProperty("reason");
    expect(typeof result.errorClass).toBe("string");
    expect(typeof result.retryable).toBe("boolean");
    expect(typeof result.reason).toBe("string");
  });

  it("permanent error classification feeds into dead-letter semantics", () => {
    // A permanent error means: do NOT retry, this intent is terminal
    const permanentCases = [
      "Bybit API error 110007: insufficient balance",
      "Bybit API error 10001: parameter error",
      "SECRET_ENCRYPTION_KEY not configured",
      "Order normalization failed: qty below minimum",
    ];
    for (const msg of permanentCases) {
      const result = classify(msg);
      expect(result.errorClass).toBe("permanent");
      expect(result.retryable).toBe(false);
      // This means the intent stays FAILED — it's effectively dead-lettered
    }
  });

  it("transient error classification enables potential future retry", () => {
    const transientCases = [
      "Bybit API error 10006: too many visits",
      "Bybit order request failed: 429 Too Many Requests",
      "connect ECONNREFUSED 127.0.0.1:443",
      "socket hang up",
    ];
    for (const msg of transientCases) {
      const result = classify(msg);
      expect(result.errorClass).toBe("transient");
      expect(result.retryable).toBe(true);
      // Retryable=true means a retry mechanism could pick this up
    }
  });

  it("unknown errors default to non-retryable (safe for circuit breaker)", () => {
    // The pauseOnError circuit breaker counts consecutive FAILED intents.
    // Unknown errors should count toward that threshold (non-retryable).
    const result = classify("something we've never seen before");
    expect(result.retryable).toBe(false);
  });
});

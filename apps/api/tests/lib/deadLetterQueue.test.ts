/**
 * Dead-letter queue logic tests (Roadmap V3, Task #22)
 *
 * Tests the retry vs dead-letter decision logic in executeIntent's catch block.
 * Uses pure function approach — verifies decision outcomes, not DB writes.
 */

import { describe, it, expect } from "vitest";
import { classifyExecutionError } from "../../src/lib/errorClassifier.js";

// ---------------------------------------------------------------------------
// Replicate the DLQ decision logic from botWorker's executeIntent catch block
// ---------------------------------------------------------------------------

const MAX_INTENT_RETRIES = 3;

interface DlqDecision {
  action: "retry" | "dead_letter" | "permanent_fail";
  retryAttempt?: number;
  reason: string;
}

function decideDlqAction(err: unknown, retryCount: number): DlqDecision {
  const classification = classifyExecutionError(err);
  const canRetry = classification.retryable && retryCount < MAX_INTENT_RETRIES;

  if (canRetry) {
    return {
      action: "retry",
      retryAttempt: retryCount + 1,
      reason: `transient error, retry ${retryCount + 1}/${MAX_INTENT_RETRIES}`,
    };
  }

  if (classification.retryable) {
    return {
      action: "dead_letter",
      reason: `max retries exhausted (${retryCount}/${MAX_INTENT_RETRIES})`,
    };
  }

  return {
    action: "permanent_fail",
    reason: `permanent error: ${classification.reason}`,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("DLQ decision: transient errors", () => {
  const transientErrors = [
    new Error("Bybit API error 10006: too many requests"),
    new Error("Bybit order request failed: 503 Service Unavailable"),
    new Error("ECONNRESET"),
    new Error("fetch failed"),
    new Error("socket hang up"),
    new Error("Bybit API error 10018: server timeout"),
  ];

  for (const err of transientErrors) {
    it(`retries on first failure: ${err.message.slice(0, 50)}`, () => {
      const decision = decideDlqAction(err, 0);
      expect(decision.action).toBe("retry");
      expect(decision.retryAttempt).toBe(1);
    });

    it(`retries on second failure: ${err.message.slice(0, 50)}`, () => {
      const decision = decideDlqAction(err, 1);
      expect(decision.action).toBe("retry");
      expect(decision.retryAttempt).toBe(2);
    });

    it(`retries on third failure: ${err.message.slice(0, 50)}`, () => {
      const decision = decideDlqAction(err, 2);
      expect(decision.action).toBe("retry");
      expect(decision.retryAttempt).toBe(3);
    });

    it(`dead-letters after max retries: ${err.message.slice(0, 50)}`, () => {
      const decision = decideDlqAction(err, 3);
      expect(decision.action).toBe("dead_letter");
      expect(decision.reason).toContain("max retries exhausted");
    });

    it(`dead-letters when retryCount exceeds max: ${err.message.slice(0, 50)}`, () => {
      const decision = decideDlqAction(err, 10);
      expect(decision.action).toBe("dead_letter");
    });
  }
});

describe("DLQ decision: permanent errors", () => {
  const permanentErrors = [
    new Error("Bybit API error 10001: parameter error"),
    new Error("Bybit API error 110003: insufficient balance"),
    new Error("Bybit API error 10003: invalid API key"),
    new Error("Bybit order request failed: 403 Forbidden"),
    new Error("Order normalization failed: invalid qty"),
    new Error("SECRET_ENCRYPTION_KEY not configured"),
  ];

  for (const err of permanentErrors) {
    it(`immediately fails (no retry): ${err.message.slice(0, 50)}`, () => {
      const decision = decideDlqAction(err, 0);
      expect(decision.action).toBe("permanent_fail");
      expect(decision.reason).toContain("permanent");
    });

    it(`still fails even with retryCount=0: ${err.message.slice(0, 50)}`, () => {
      const decision = decideDlqAction(err, 0);
      expect(decision.action).toBe("permanent_fail");
    });
  }
});

describe("DLQ decision: unknown errors", () => {
  it("does not retry unknown errors (conservative)", () => {
    const err = new Error("something completely unexpected");
    const decision = decideDlqAction(err, 0);
    expect(decision.action).toBe("permanent_fail");
  });
});

describe("DLQ decision: boundary cases", () => {
  it("retryCount exactly at max → dead letter", () => {
    const err = new Error("ECONNRESET");
    const decision = decideDlqAction(err, MAX_INTENT_RETRIES);
    expect(decision.action).toBe("dead_letter");
  });

  it("retryCount one below max → still retries", () => {
    const err = new Error("ECONNRESET");
    const decision = decideDlqAction(err, MAX_INTENT_RETRIES - 1);
    expect(decision.action).toBe("retry");
    expect(decision.retryAttempt).toBe(MAX_INTENT_RETRIES);
  });

  it("classifyExecutionError is consistent for same input", () => {
    const err = new Error("Bybit API error 10006: rate limit");
    const c1 = classifyExecutionError(err);
    const c2 = classifyExecutionError(err);
    expect(c1).toEqual(c2);
  });
});

describe("DLQ constants", () => {
  it("MAX_INTENT_RETRIES is 3", () => {
    expect(MAX_INTENT_RETRIES).toBe(3);
  });

  it("all transient Bybit retCodes are retryable", () => {
    for (const code of [10006, 10016, 10018]) {
      const err = new Error(`Bybit API error ${code}: test`);
      const c = classifyExecutionError(err);
      expect(c.retryable).toBe(true);
      expect(c.errorClass).toBe("transient");
    }
  });

  it("all permanent Bybit retCodes are not retryable", () => {
    for (const code of [10001, 10003, 110003, 170124]) {
      const err = new Error(`Bybit API error ${code}: test`);
      const c = classifyExecutionError(err);
      expect(c.retryable).toBe(false);
      expect(c.errorClass).toBe("permanent");
    }
  });
});

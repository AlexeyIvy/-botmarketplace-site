/**
 * Crypto rotation helpers — `getEncryptionKeysRaw` + `decryptWithFallback`
 * (docs/34 §A4 follow-up; existing `encryptionKeyFix.test.ts` already
 * covers the encrypt/decrypt single-key roundtrip cases).
 *
 * The rotation path is § 5.7 of the security model: a new
 * `SECRET_ENCRYPTION_KEY` is rolled in while the old value is moved to
 * `SECRET_ENCRYPTION_KEY_OLD` (comma-separated for multi-step rotations).
 * Existing exchange-credential rows decrypt against whichever key still
 * matches; a one-shot migration re-encrypts everything with the new key,
 * after which `_OLD` can be removed. If this code path silently fails,
 * every operator's exchange connection breaks on the next live trade.
 *
 * The tests fix `SECRET_ENCRYPTION_KEY` per case and restore at the end
 * so they don't bleed env state into other suites.
 */

import { afterEach, describe, expect, it } from "vitest";

import {
  encrypt,
  decrypt,
  decryptWithFallback,
  getEncryptionKeyRaw,
  getEncryptionKeysRaw,
} from "../../src/lib/crypto.js";

// Two distinct 64-hex-char (32-byte) keys. Predictable — easier to debug
// than generating random ones, and the test asserts the SAME key is used
// for both encrypt and the matching decrypt branch.
const KEY_A = "a".repeat(64); // current key in the rotation tests
const KEY_B = "b".repeat(64); // old key #1
const KEY_C = "c".repeat(64); // old key #2

const originalCurrent = process.env.SECRET_ENCRYPTION_KEY;
const originalOld = process.env.SECRET_ENCRYPTION_KEY_OLD;

afterEach(() => {
  // Restore env so tests in other files (and this file) start clean.
  if (originalCurrent === undefined) delete process.env.SECRET_ENCRYPTION_KEY;
  else process.env.SECRET_ENCRYPTION_KEY = originalCurrent;
  if (originalOld === undefined) delete process.env.SECRET_ENCRYPTION_KEY_OLD;
  else process.env.SECRET_ENCRYPTION_KEY_OLD = originalOld;
});

// ---------------------------------------------------------------------------
// getEncryptionKeysRaw — env parsing
// ---------------------------------------------------------------------------

describe("getEncryptionKeysRaw — env parser", () => {
  it("returns [current] only when SECRET_ENCRYPTION_KEY_OLD is unset", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    delete process.env.SECRET_ENCRYPTION_KEY_OLD;
    const keys = getEncryptionKeysRaw();
    expect(keys).toHaveLength(1);
    expect(keys[0]).toEqual(Buffer.from(KEY_A, "hex"));
  });

  it("returns [current, old] when one old key is supplied", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = KEY_B;
    const keys = getEncryptionKeysRaw();
    expect(keys).toHaveLength(2);
    expect(keys[0]).toEqual(Buffer.from(KEY_A, "hex"));
    expect(keys[1]).toEqual(Buffer.from(KEY_B, "hex"));
  });

  it("parses comma-separated multi-step rotation list in declared order", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = `${KEY_B},${KEY_C}`;
    const keys = getEncryptionKeysRaw();
    expect(keys).toHaveLength(3);
    expect(keys[0]).toEqual(Buffer.from(KEY_A, "hex"));
    expect(keys[1]).toEqual(Buffer.from(KEY_B, "hex"));
    expect(keys[2]).toEqual(Buffer.from(KEY_C, "hex"));
  });

  it("trims whitespace around comma-separated entries", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = `  ${KEY_B}  ,\t${KEY_C}\n`;
    const keys = getEncryptionKeysRaw();
    expect(keys).toHaveLength(3);
    expect(keys[1]).toEqual(Buffer.from(KEY_B, "hex"));
    expect(keys[2]).toEqual(Buffer.from(KEY_C, "hex"));
  });

  it("filters empty entries (e.g. trailing comma) silently", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = `${KEY_B},,${KEY_C},`;
    const keys = getEncryptionKeysRaw();
    expect(keys).toHaveLength(3);
  });

  it("treats SECRET_ENCRYPTION_KEY_OLD = '' (empty) as unset", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = "";
    const keys = getEncryptionKeysRaw();
    expect(keys).toHaveLength(1);
  });

  it("throws with diagnostic length info when an old key is the wrong length", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = "a".repeat(63); // one short
    expect(() => getEncryptionKeysRaw()).toThrow(/SECRET_ENCRYPTION_KEY_OLD/);
    expect(() => getEncryptionKeysRaw()).toThrow(/63/);
  });

  it("throws when ANY entry in a comma-separated list is wrong length (rotation safety)", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = `${KEY_B},short`;
    expect(() => getEncryptionKeysRaw()).toThrow(/SECRET_ENCRYPTION_KEY_OLD/);
  });

  it("propagates the SECRET_ENCRYPTION_KEY (current) failure if the current key is missing", () => {
    delete process.env.SECRET_ENCRYPTION_KEY;
    process.env.SECRET_ENCRYPTION_KEY_OLD = KEY_B;
    expect(() => getEncryptionKeysRaw()).toThrow(/SECRET_ENCRYPTION_KEY/);
  });
});

// ---------------------------------------------------------------------------
// decryptWithFallback — multi-key decrypt
// ---------------------------------------------------------------------------

describe("decryptWithFallback — multi-key decrypt path", () => {
  it("decrypts a payload encrypted with the CURRENT key (no fallback needed)", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = KEY_B;
    const keyA = Buffer.from(KEY_A, "hex");
    const payload = encrypt("hello-current", keyA);
    expect(decryptWithFallback(payload)).toBe("hello-current");
  });

  it("falls back to the OLD key for legacy rows still encrypted with it", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = KEY_B;
    const keyB = Buffer.from(KEY_B, "hex");
    // Simulate a row written before the rotation: encrypted with the OLD key.
    const legacyPayload = encrypt("legacy-secret", keyB);
    expect(decryptWithFallback(legacyPayload)).toBe("legacy-secret");
  });

  it("walks the multi-step rotation list and matches the second old key", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = `${KEY_B},${KEY_C}`;
    const keyC = Buffer.from(KEY_C, "hex");
    const veryLegacyPayload = encrypt("very-old-secret", keyC);
    expect(decryptWithFallback(veryLegacyPayload)).toBe("very-old-secret");
  });

  it("throws when none of the configured keys can decrypt (preserves last error)", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = KEY_B;
    // Encrypted with a key NOT in the configured set.
    const keyC = Buffer.from(KEY_C, "hex");
    const orphanPayload = encrypt("orphan-secret", keyC);
    expect(() => decryptWithFallback(orphanPayload)).toThrow();
  });

  it("rejects a tampered payload even when the correct key is available", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = KEY_B;
    const keyA = Buffer.from(KEY_A, "hex");
    const payload = encrypt("integrity-check", keyA);

    // Flip one byte of ciphertext.
    const [iv, tag, ct] = payload.split(":");
    const tamperedCt = Buffer.from(ct, "base64");
    tamperedCt[0] ^= 0x01;
    const tampered = [iv, tag, tamperedCt.toString("base64")].join(":");

    expect(() => decryptWithFallback(tampered)).toThrow();
  });

  it("rejects an invalid format payload (single-key path raises 'Invalid encrypted payload format')", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    delete process.env.SECRET_ENCRYPTION_KEY_OLD;
    expect(() => decryptWithFallback("not-a-valid-payload")).toThrow(/Invalid encrypted payload format/);
  });

  it("works with no SECRET_ENCRYPTION_KEY_OLD set (falls back path is a no-op)", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    delete process.env.SECRET_ENCRYPTION_KEY_OLD;
    const keyA = Buffer.from(KEY_A, "hex");
    const payload = encrypt("single-key-mode", keyA);
    expect(decryptWithFallback(payload)).toBe("single-key-mode");
  });

  it("preserves the original plaintext through a full rotation cycle (encrypt-old → decrypt-fallback → re-encrypt-current)", () => {
    // This is the migration shape — read with fallback, write with the
    // current key. Confirms the helper composes cleanly with re-encryption.
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = KEY_B;

    const keyA = Buffer.from(KEY_A, "hex");
    const keyB = Buffer.from(KEY_B, "hex");

    const original = "rotated-secret-🔑";
    const oldPayload = encrypt(original, keyB);

    // Read step (production migration): decryptWithFallback honours OLD.
    const recovered = decryptWithFallback(oldPayload);
    expect(recovered).toBe(original);

    // Write step (production migration): re-encrypt with CURRENT.
    const newPayload = encrypt(recovered, keyA);
    expect(newPayload).not.toBe(oldPayload);

    // After migration, decrypt should still resolve via current key path.
    expect(decryptWithFallback(newPayload)).toBe(original);
    // And the regular single-key decrypt with CURRENT works too.
    expect(decrypt(newPayload, keyA)).toBe(original);
  });
});

// ---------------------------------------------------------------------------
// Sanity bridge — getEncryptionKeyRaw exists alongside the rotation helpers.
// ---------------------------------------------------------------------------

describe("getEncryptionKeyRaw vs getEncryptionKeysRaw — same current key", () => {
  it("getEncryptionKeysRaw[0] equals getEncryptionKeyRaw() output", () => {
    process.env.SECRET_ENCRYPTION_KEY = KEY_A;
    process.env.SECRET_ENCRYPTION_KEY_OLD = KEY_B;
    const single = getEncryptionKeyRaw();
    const list = getEncryptionKeysRaw();
    expect(list[0]).toEqual(single);
  });
});

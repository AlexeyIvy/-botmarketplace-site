/**
 * Encryption key missing fix — Roadmap V3, Task #2
 *
 * Tests that getEncryptionKeyRaw() throws instead of silently returning null
 * when SECRET_ENCRYPTION_KEY is missing or invalid.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { getEncryptionKeyRaw, encrypt, decrypt } from "../../src/lib/crypto.js";

describe("getEncryptionKeyRaw", () => {
  const VALID_KEY_HEX = "a".repeat(64); // 32 bytes in hex
  let originalEnv: string | undefined;

  beforeEach(() => {
    originalEnv = process.env.SECRET_ENCRYPTION_KEY;
  });

  afterEach(() => {
    if (originalEnv !== undefined) {
      process.env.SECRET_ENCRYPTION_KEY = originalEnv;
    } else {
      delete process.env.SECRET_ENCRYPTION_KEY;
    }
  });

  it("throws when SECRET_ENCRYPTION_KEY is not set", () => {
    delete process.env.SECRET_ENCRYPTION_KEY;
    expect(() => getEncryptionKeyRaw()).toThrow("SECRET_ENCRYPTION_KEY is not set");
  });

  it("throws when SECRET_ENCRYPTION_KEY is empty string", () => {
    process.env.SECRET_ENCRYPTION_KEY = "";
    expect(() => getEncryptionKeyRaw()).toThrow("SECRET_ENCRYPTION_KEY is not set");
  });

  it("throws when SECRET_ENCRYPTION_KEY has wrong length", () => {
    process.env.SECRET_ENCRYPTION_KEY = "abcd1234"; // too short
    expect(() => getEncryptionKeyRaw()).toThrow("wrong length");
  });

  it("throws with specific length info for wrong-length key", () => {
    process.env.SECRET_ENCRYPTION_KEY = "ab".repeat(16); // 32 hex chars, need 64
    expect(() => getEncryptionKeyRaw()).toThrow("expected 64 hex chars, got 32");
  });

  it("returns Buffer for valid 64-char hex key", () => {
    process.env.SECRET_ENCRYPTION_KEY = VALID_KEY_HEX;
    const key = getEncryptionKeyRaw();
    expect(key).toBeInstanceOf(Buffer);
    expect(key.length).toBe(32);
  });

  it("encrypt→decrypt roundtrip works with valid key", () => {
    process.env.SECRET_ENCRYPTION_KEY = VALID_KEY_HEX;
    const key = getEncryptionKeyRaw();
    const plaintext = "my-bybit-api-secret-12345";
    const ciphertext = encrypt(plaintext, key);
    const decrypted = decrypt(ciphertext, key);
    expect(decrypted).toBe(plaintext);
  });

  it("decrypt with wrong key throws (GCM auth tag failure)", () => {
    process.env.SECRET_ENCRYPTION_KEY = VALID_KEY_HEX;
    const key = getEncryptionKeyRaw();
    const ciphertext = encrypt("secret", key);

    const wrongKey = Buffer.from("b".repeat(64), "hex");
    expect(() => decrypt(ciphertext, wrongKey)).toThrow();
  });
});

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { randomBytes } from "node:crypto";
import {
  encrypt,
  decrypt,
  decryptWithFallback,
  getEncryptionKeysRaw,
} from "../../src/lib/crypto.js";

const KEY_A = randomBytes(32);
const KEY_B = randomBytes(32);

describe("encryption key rotation (§5.7)", () => {
  const saved = {
    CURRENT: process.env.SECRET_ENCRYPTION_KEY,
    OLD: process.env.SECRET_ENCRYPTION_KEY_OLD,
  };

  beforeEach(() => {
    delete process.env.SECRET_ENCRYPTION_KEY;
    delete process.env.SECRET_ENCRYPTION_KEY_OLD;
  });

  afterEach(() => {
    process.env.SECRET_ENCRYPTION_KEY = saved.CURRENT;
    process.env.SECRET_ENCRYPTION_KEY_OLD = saved.OLD;
  });

  describe("getEncryptionKeysRaw", () => {
    it("returns only the current key when SECRET_ENCRYPTION_KEY_OLD is unset", () => {
      process.env.SECRET_ENCRYPTION_KEY = KEY_A.toString("hex");
      const keys = getEncryptionKeysRaw();
      expect(keys.length).toBe(1);
      expect(keys[0].equals(KEY_A)).toBe(true);
    });

    it("returns current then old keys, in order, when OLD is a single key", () => {
      process.env.SECRET_ENCRYPTION_KEY = KEY_A.toString("hex");
      process.env.SECRET_ENCRYPTION_KEY_OLD = KEY_B.toString("hex");
      const keys = getEncryptionKeysRaw();
      expect(keys.length).toBe(2);
      expect(keys[0].equals(KEY_A)).toBe(true);
      expect(keys[1].equals(KEY_B)).toBe(true);
    });

    it("supports comma-separated list of old keys", () => {
      const KEY_C = randomBytes(32);
      process.env.SECRET_ENCRYPTION_KEY = KEY_A.toString("hex");
      process.env.SECRET_ENCRYPTION_KEY_OLD = `${KEY_B.toString("hex")},${KEY_C.toString("hex")}`;
      const keys = getEncryptionKeysRaw();
      expect(keys.length).toBe(3);
      expect(keys[1].equals(KEY_B)).toBe(true);
      expect(keys[2].equals(KEY_C)).toBe(true);
    });

    it("throws on malformed SECRET_ENCRYPTION_KEY_OLD entry", () => {
      process.env.SECRET_ENCRYPTION_KEY = KEY_A.toString("hex");
      process.env.SECRET_ENCRYPTION_KEY_OLD = "deadbeef"; // wrong length
      expect(() => getEncryptionKeysRaw()).toThrow(/wrong length/);
    });
  });

  describe("decryptWithFallback", () => {
    it("decrypts with the current key when no old key is configured", () => {
      process.env.SECRET_ENCRYPTION_KEY = KEY_A.toString("hex");
      const ciphertext = encrypt("hello", KEY_A);
      expect(decryptWithFallback(ciphertext)).toBe("hello");
    });

    it("falls back to the old key when the payload was encrypted with it", () => {
      process.env.SECRET_ENCRYPTION_KEY = KEY_A.toString("hex");
      process.env.SECRET_ENCRYPTION_KEY_OLD = KEY_B.toString("hex");
      const oldCiphertext = encrypt("legacy-secret", KEY_B);
      expect(decryptWithFallback(oldCiphertext)).toBe("legacy-secret");
    });

    it("prefers the current key when the payload was already rotated", () => {
      process.env.SECRET_ENCRYPTION_KEY = KEY_A.toString("hex");
      process.env.SECRET_ENCRYPTION_KEY_OLD = KEY_B.toString("hex");
      const newCiphertext = encrypt("rotated-secret", KEY_A);
      expect(decryptWithFallback(newCiphertext)).toBe("rotated-secret");
    });

    it("throws when neither key works", () => {
      process.env.SECRET_ENCRYPTION_KEY = KEY_A.toString("hex");
      process.env.SECRET_ENCRYPTION_KEY_OLD = KEY_B.toString("hex");
      const unrelatedKey = randomBytes(32);
      const ciphertext = encrypt("unknown", unrelatedKey);
      expect(() => decryptWithFallback(ciphertext)).toThrow();
    });
  });

  describe("decrypt (underlying primitive)", () => {
    it("round-trips encrypt → decrypt", () => {
      const key = randomBytes(32);
      const ct = encrypt("round-trip", key);
      expect(decrypt(ct, key)).toBe("round-trip");
    });
  });
});

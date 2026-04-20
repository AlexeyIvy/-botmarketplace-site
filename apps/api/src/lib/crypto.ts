import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";
import type { FastifyReply } from "fastify";
import { problem } from "./problem.js";

const ALGORITHM = "aes-256-gcm";
const KEY_HEX_LENGTH = 64; // 32 bytes = 64 hex chars

/**
 * Get the encryption key from env.
 * Returns null and sends a 500 Problem Details if key is missing or invalid.
 */
export function getEncryptionKey(reply: FastifyReply): Buffer | null {
  const raw = process.env.SECRET_ENCRYPTION_KEY;
  if (!raw) {
    reply.log.error("SECRET_ENCRYPTION_KEY is not set — cannot proceed with secret encryption");
    problem(reply, 500, "Server Configuration Error", "Secret encryption key is not configured. Set SECRET_ENCRYPTION_KEY env variable.");
    return null;
  }
  if (raw.length !== KEY_HEX_LENGTH) {
    reply.log.error({ keyLength: raw.length }, "SECRET_ENCRYPTION_KEY has wrong length — expected 64 hex chars (32 bytes)");
    problem(reply, 500, "Server Configuration Error", "SECRET_ENCRYPTION_KEY must be a 64-character hex string (32 bytes).");
    return null;
  }
  return Buffer.from(raw, "hex");
}

/**
 * Encrypt a plaintext string with AES-256-GCM.
 * Returns a base64-encoded payload: iv:authTag:ciphertext (colon-separated).
 */
export function encrypt(plaintext: string, key: Buffer): string {
  const iv = randomBytes(12); // 96-bit IV recommended for GCM
  const cipher = createCipheriv(ALGORITHM, key, iv);
  const encrypted = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()]);
  const authTag = cipher.getAuthTag();
  // Format: base64(iv):base64(authTag):base64(ciphertext)
  return [iv.toString("base64"), authTag.toString("base64"), encrypted.toString("base64")].join(":");
}

/**
 * Get the encryption key directly (no Fastify reply required).
 * Throws if the key is missing or invalid — fail fast, never silently skip.
 */
export function getEncryptionKeyRaw(): Buffer {
  const raw = process.env.SECRET_ENCRYPTION_KEY;
  if (!raw) {
    throw new Error("SECRET_ENCRYPTION_KEY is not set — cannot decrypt exchange credentials");
  }
  if (raw.length !== KEY_HEX_LENGTH) {
    throw new Error(`SECRET_ENCRYPTION_KEY has wrong length: expected ${KEY_HEX_LENGTH} hex chars, got ${raw.length}`);
  }
  return Buffer.from(raw, "hex");
}

/**
 * Get all encryption keys in priority order for decryption fallback (§5.7).
 *
 * Returns `[current, ...old]` where `old` is an array of previous keys
 * supplied via `SECRET_ENCRYPTION_KEY_OLD` (comma-separated list of hex).
 *
 * Intended usage: during key rotation, decrypt tries the current key first
 * and falls back to the old one(s) for records not yet re-encrypted. A
 * one-shot migration re-encrypts everything with the new key, after which
 * `SECRET_ENCRYPTION_KEY_OLD` can be removed.
 */
export function getEncryptionKeysRaw(): Buffer[] {
  const keys: Buffer[] = [getEncryptionKeyRaw()];
  const oldRaw = process.env.SECRET_ENCRYPTION_KEY_OLD;
  if (!oldRaw) return keys;

  for (const candidate of oldRaw.split(",").map((s) => s.trim()).filter(Boolean)) {
    if (candidate.length !== KEY_HEX_LENGTH) {
      throw new Error(
        `SECRET_ENCRYPTION_KEY_OLD entry has wrong length: expected ${KEY_HEX_LENGTH} hex chars, got ${candidate.length}`,
      );
    }
    keys.push(Buffer.from(candidate, "hex"));
  }
  return keys;
}

/**
 * Decrypt using whichever configured key works (§5.7 rotation helper).
 *
 * Tries the current key first, then any in `SECRET_ENCRYPTION_KEY_OLD`.
 * Throws if none succeed — same failure shape as `decrypt` when the
 * single-key call fails.
 */
export function decryptWithFallback(payload: string): string {
  const keys = getEncryptionKeysRaw();
  let lastErr: unknown;
  for (const key of keys) {
    try {
      return decrypt(payload, key);
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error("decryptWithFallback: all keys failed");
}

/**
 * Decrypt a payload produced by encrypt().
 * Throws on any tampering / wrong key.
 */
export function decrypt(payload: string, key: Buffer): string {
  const parts = payload.split(":");
  if (parts.length !== 3) throw new Error("Invalid encrypted payload format");
  const [ivB64, authTagB64, ciphertextB64] = parts;
  const iv = Buffer.from(ivB64, "base64");
  const authTag = Buffer.from(authTagB64, "base64");
  const ciphertext = Buffer.from(ciphertextB64, "base64");
  const decipher = createDecipheriv(ALGORITHM, key, iv);
  decipher.setAuthTag(authTag);
  return Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString("utf8");
}

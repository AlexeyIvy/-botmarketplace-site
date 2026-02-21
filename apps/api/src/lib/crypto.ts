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

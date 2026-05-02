-- ExchangeConnection — optional dedicated spot credentials (docs/55-T5).
--
-- Funding-arbitrage requires Bybit access to BOTH the linear (perp) and the
-- spot wallet. Bybit unified accounts can issue a single API key with both
-- scopes — but operators may prefer separate keys (smaller blast radius if
-- one is compromised). These three columns let `ExchangeConnection` carry an
-- optional second key/secret pair for the spot wallet.
--
-- Backwards compatibility:
--   * All three columns are NULL on existing rows.
--   * Single-key fallback: when `spotApiKey` / `spotEncryptedSecret` are NULL,
--     the linear `apiKey` / `encryptedSecret` is reused for spot API calls
--     (see `apps/api/src/lib/exchange/balanceReconciler.ts`).
--
-- Encryption format: `spotEncryptedSecret` mirrors `encryptedSecret` —
-- AES-256-GCM, base64 colon-joined `iv:authTag:ciphertext`, decrypted via
-- `decryptWithFallback` (apps/api/src/lib/crypto.ts).

ALTER TABLE "ExchangeConnection" ADD COLUMN "spotApiKey" TEXT;
ALTER TABLE "ExchangeConnection" ADD COLUMN "spotEncryptedSecret" TEXT;
ALTER TABLE "ExchangeConnection" ADD COLUMN "spotKeyLabel" TEXT;

/**
 * PATCH /exchanges/:id — apiKey validation (Roadmap V3, Task #17)
 *
 * Verifies that PATCH rejects empty/null apiKey the same way POST does.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock Prisma before any import that touches it
vi.mock("@prisma/client", () => ({
  PrismaClient: vi.fn().mockImplementation(() => ({
    $connect: vi.fn(),
    $disconnect: vi.fn(),
  })),
  Prisma: { sql: vi.fn(), join: vi.fn() },
}));

const mockFindUnique = vi.fn();
const mockUpdate = vi.fn();
const mockCreate = vi.fn();

vi.mock("../../src/lib/prisma.js", () => ({
  prisma: {
    exchangeConnection: {
      findUnique: (...args: unknown[]) => mockFindUnique(...args),
      findMany: vi.fn().mockResolvedValue([]),
      create: (...args: unknown[]) => mockCreate(...args),
      update: (...args: unknown[]) => mockUpdate(...args),
      delete: vi.fn(),
    },
    $connect: vi.fn(),
    $disconnect: vi.fn(),
    $queryRaw: vi.fn().mockResolvedValue([{ "?column?": 1 }]),
  },
}));

vi.mock("../../src/lib/workspace.js", () => ({
  resolveWorkspace: vi.fn().mockResolvedValue({ id: "ws-1", name: "test" }),
}));

vi.mock("../../src/lib/crypto.js", () => ({
  getEncryptionKey: vi.fn().mockReturnValue(Buffer.alloc(32)),
  encrypt: vi.fn().mockReturnValue("iv:tag:cipher"),
  decrypt: vi.fn().mockReturnValue("decrypted"),
  decryptWithFallback: vi.fn().mockReturnValue("decrypted"),
}));

import { buildApp } from "../../src/app.js";

async function getApp() {
  const app = await buildApp();
  // Generate a valid JWT for auth
  const token = app.jwt.sign({ sub: "user-1", workspaceId: "ws-1" });
  return { app, token };
}

describe("PATCH /exchanges/:id — apiKey validation", () => {
  const CONN_ID = "conn-123";
  const EXISTING_CONN = {
    id: CONN_ID,
    workspaceId: "ws-1",
    exchange: "BYBIT",
    name: "My Bybit",
    apiKey: "valid-key",
    encryptedSecret: "iv:tag:cipher",
    status: "CONNECTED",
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  it("rejects apiKey: '' (empty string)", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { apiKey: "" },
    });

    expect(res.statusCode).toBe(400);
    const body = JSON.parse(res.payload);
    expect(body.detail).toContain("apiKey must be a non-empty string");

    await app.close();
  });

  it("rejects apiKey: '   ' (whitespace only)", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { apiKey: "   " },
    });

    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("accepts valid apiKey string", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);
    mockUpdate.mockResolvedValue({ ...EXISTING_CONN, apiKey: "new-valid-key", status: "UNKNOWN" });

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { apiKey: "new-valid-key" },
    });

    expect(res.statusCode).toBe(200);
    await app.close();
  });

  it("allows PATCH with only name (no apiKey)", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);
    mockUpdate.mockResolvedValue({ ...EXISTING_CONN, name: "Renamed" });

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { name: "Renamed" },
    });

    expect(res.statusCode).toBe(200);
    await app.close();
  });

  it("rejects apiKey exceeding max length", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { apiKey: "a".repeat(257) },
    });

    expect(res.statusCode).toBe(400);
    const body = JSON.parse(res.payload);
    expect(body.detail).toContain("256");
    await app.close();
  });

  it("rejects apiKey with invalid characters", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { apiKey: "key with spaces!" },
    });

    expect(res.statusCode).toBe(400);
    const body = JSON.parse(res.payload);
    expect(body.detail).toContain("invalid characters");
    await app.close();
  });

  it("accepts apiKey with alphanumeric, dash, underscore", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING_CONN);
    mockUpdate.mockResolvedValue({ ...EXISTING_CONN, apiKey: "My-Key_123", status: "UNKNOWN" });

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}` },
      payload: { apiKey: "My-Key_123" },
    });

    expect(res.statusCode).toBe(200);
    await app.close();
  });

  it("returns 401 without auth token", async () => {
    const { app } = await getApp();

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      payload: { apiKey: "test" },
    });

    expect(res.statusCode).toBe(401);
    await app.close();
  });
});

// ---------------------------------------------------------------------------
// docs/55-T5 spot-key fields — POST + PATCH + safeView projection
// ---------------------------------------------------------------------------

describe("POST /exchanges — spot key fields", () => {
  beforeEach(() => {
    // Don't reset implementations (ours rely on a `mockResolvedValue` /
    // `mockImplementation` per test) — just clear call history so
    // `mock.calls[0]` is unambiguous.
    mockFindUnique.mockClear();
    mockUpdate.mockClear();
    mockCreate.mockClear();
  });

  const baseBody = {
    exchange: "BYBIT",
    name: "spot-test",
    apiKey: "linear-key",
    secret: "linear-secret",
  };

  const baseRow = {
    id: "conn-spot",
    workspaceId: "ws-1",
    exchange: "BYBIT",
    name: "spot-test",
    apiKey: "linear-key",
    encryptedSecret: "iv:tag:cipher",
    status: "UNKNOWN",
    spotApiKey: null,
    spotEncryptedSecret: null,
    spotKeyLabel: null,
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  it("accepts both spotApiKey + spotSecret + spotKeyLabel; safeView returns hasSpotKey=true + label", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(null); // no existing
    mockCreate.mockImplementation(async ({ data }: { data: Record<string, unknown> }) => ({
      ...baseRow,
      ...data,
      id: "conn-spot-1",
      createdAt: new Date(),
      updatedAt: new Date(),
    }));

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/exchanges`,
      headers: { authorization: `Bearer ${token}`, "x-workspace-id": "ws-1" },
      payload: { ...baseBody, spotApiKey: "spot-key", spotSecret: "spot-secret", spotKeyLabel: "Funding-arb spot" },
    });

    expect(res.statusCode).toBe(201);
    const body = JSON.parse(res.payload);
    expect(body.hasSpotKey).toBe(true);
    expect(body.spotKeyLabel).toBe("Funding-arb spot");
    // The key string itself MUST NOT leak in the response — defence-in-depth.
    expect(body.spotApiKey).toBeUndefined();
    expect(body.spotEncryptedSecret).toBeUndefined();
    expect(body.encryptedSecret).toBeUndefined();
    // Persisted shape — both spot fields populated, single-key fallback skipped.
    const createCall = mockCreate.mock.calls[0]?.[0] as { data: Record<string, unknown> };
    expect(createCall.data.spotApiKey).toBe("spot-key");
    expect(createCall.data.spotEncryptedSecret).toBe("iv:tag:cipher");
    await app.close();
  });

  it("omitting both spot fields → hasSpotKey=false, persisted fields are null (single-key fallback)", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(null);
    mockCreate.mockImplementation(async ({ data }: { data: Record<string, unknown> }) => ({
      ...baseRow,
      ...data,
      id: "conn-single",
      createdAt: new Date(),
      updatedAt: new Date(),
    }));

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/exchanges`,
      headers: { authorization: `Bearer ${token}`, "x-workspace-id": "ws-1" },
      payload: baseBody,
    });

    expect(res.statusCode).toBe(201);
    const body = JSON.parse(res.payload);
    expect(body.hasSpotKey).toBe(false);
    expect(body.spotKeyLabel).toBeNull();
    const createCall = mockCreate.mock.calls[0]?.[0] as { data: Record<string, unknown> };
    expect(createCall.data.spotApiKey).toBeNull();
    expect(createCall.data.spotEncryptedSecret).toBeNull();
    await app.close();
  });

  it("supplying spotApiKey without spotSecret → 400 'must be supplied together'", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(null);

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/exchanges`,
      headers: { authorization: `Bearer ${token}`, "x-workspace-id": "ws-1" },
      payload: { ...baseBody, spotApiKey: "spot-key" },
    });

    expect(res.statusCode).toBe(400);
    const body = JSON.parse(res.payload);
    expect(JSON.stringify(body)).toContain("must be supplied together");
    expect(mockCreate).not.toHaveBeenCalled();
    await app.close();
  });

  it("spotApiKey with invalid characters → 400 with field-pinned error", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(null);

    const res = await app.inject({
      method: "POST",
      url: `/api/v1/exchanges`,
      headers: { authorization: `Bearer ${token}`, "x-workspace-id": "ws-1" },
      payload: { ...baseBody, spotApiKey: "key with spaces!", spotSecret: "spot-secret" },
    });

    expect(res.statusCode).toBe(400);
    const body = JSON.parse(res.payload);
    expect(JSON.stringify(body)).toContain("spotApiKey");
    expect(JSON.stringify(body)).toContain("invalid characters");
    await app.close();
  });
});

describe("PATCH /exchanges/:id — spot key rotation + clear", () => {
  beforeEach(() => {
    mockFindUnique.mockClear();
    mockUpdate.mockClear();
    mockCreate.mockClear();
  });

  const CONN_ID = "conn-spot-patch";
  const EXISTING = {
    id: CONN_ID,
    workspaceId: "ws-1",
    exchange: "BYBIT",
    name: "rotate-me",
    apiKey: "linear-key",
    encryptedSecret: "iv:tag:cipher",
    status: "CONNECTED",
    spotApiKey: "old-spot-key",
    spotEncryptedSecret: "iv:tag:old-spot-cipher",
    spotKeyLabel: "Old label",
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  it("rotates spot key when both spotApiKey + spotSecret are strings; status reset to UNKNOWN", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING);
    mockUpdate.mockImplementation(async ({ data }: { data: Record<string, unknown> }) => ({
      ...EXISTING,
      ...data,
      updatedAt: new Date(),
    }));

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}`, "x-workspace-id": "ws-1" },
      payload: { spotApiKey: "new-spot-key", spotSecret: "new-spot-secret", spotKeyLabel: "New label" },
    });

    expect(res.statusCode).toBe(200);
    const updateCall = mockUpdate.mock.calls[0]?.[0] as { data: Record<string, unknown> };
    expect(updateCall.data.spotApiKey).toBe("new-spot-key");
    expect(updateCall.data.spotEncryptedSecret).toBe("iv:tag:cipher");
    expect(updateCall.data.spotKeyLabel).toBe("New label");
    // Cred change → status UNKNOWN, force re-test.
    expect(updateCall.data.status).toBe("UNKNOWN");
    await app.close();
  });

  it("clears spot key when both spotApiKey + spotSecret are null", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING);
    mockUpdate.mockImplementation(async ({ data }: { data: Record<string, unknown> }) => ({
      ...EXISTING,
      ...data,
      updatedAt: new Date(),
    }));

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}`, "x-workspace-id": "ws-1" },
      payload: { spotApiKey: null, spotSecret: null, spotKeyLabel: null },
    });

    expect(res.statusCode).toBe(200);
    const updateCall = mockUpdate.mock.calls[0]?.[0] as { data: Record<string, unknown> };
    expect(updateCall.data.spotApiKey).toBeNull();
    expect(updateCall.data.spotEncryptedSecret).toBeNull();
    expect(updateCall.data.spotKeyLabel).toBeNull();
    expect(updateCall.data.status).toBe("UNKNOWN");
    await app.close();
  });

  it("rejects half-cleared spot fields (spotApiKey=null but spotSecret=string)", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING);

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}`, "x-workspace-id": "ws-1" },
      payload: { spotApiKey: null, spotSecret: "still-here" },
    });

    expect(res.statusCode).toBe(400);
    expect(mockUpdate).not.toHaveBeenCalled();
    await app.close();
  });

  it("PATCH with no spot fields touches no spot data (omitted = no-op)", async () => {
    const { app, token } = await getApp();
    mockFindUnique.mockResolvedValue(EXISTING);
    mockUpdate.mockResolvedValue({ ...EXISTING, name: "Renamed" });

    const res = await app.inject({
      method: "PATCH",
      url: `/api/v1/exchanges/${CONN_ID}`,
      headers: { authorization: `Bearer ${token}`, "x-workspace-id": "ws-1" },
      payload: { name: "Renamed" },
    });

    expect(res.statusCode).toBe(200);
    const updateCall = mockUpdate.mock.calls[0]?.[0] as { data: Record<string, unknown> };
    expect(updateCall.data).not.toHaveProperty("spotApiKey");
    expect(updateCall.data).not.toHaveProperty("spotEncryptedSecret");
    expect(updateCall.data).not.toHaveProperty("spotKeyLabel");
    // status NOT reset because no creds changed.
    expect(updateCall.data.status).toBeUndefined();
    await app.close();
  });
});

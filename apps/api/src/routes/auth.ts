import type { FastifyInstance, FastifyReply, FastifyRequest } from "fastify";
import bcrypt from "bcryptjs";
import { prisma } from "../lib/prisma.js";

interface RegisterBody {
  email: string;
  password: string;
}

interface LoginBody {
  email: string;
  password: string;
}

const ACCESS_TOKEN_EXPIRY = "1h";
const REFRESH_TOKEN_EXPIRY = "7d";
const REFRESH_COOKIE_NAME = "refreshToken";
const REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60; // 7 days in seconds

function authProblem(reply: FastifyReply, status: number, detail: string) {
  const titles: Record<number, string> = { 400: "Bad Request", 401: "Unauthorized", 409: "Conflict" };
  return reply.status(status).send({ type: "about:blank", title: titles[status] ?? "Error", status, detail });
}

/** Set refresh token as httpOnly cookie. */
function setRefreshCookie(reply: FastifyReply, token: string) {
  const isProduction = process.env.NODE_ENV === "production";
  reply.header(
    "Set-Cookie",
    `${REFRESH_COOKIE_NAME}=${token}; HttpOnly; Path=/api; Max-Age=${REFRESH_COOKIE_MAX_AGE}; SameSite=Strict${isProduction ? "; Secure" : ""}`,
  );
}

/** Clear refresh token cookie. */
function clearRefreshCookie(reply: FastifyReply) {
  const isProduction = process.env.NODE_ENV === "production";
  reply.header(
    "Set-Cookie",
    `${REFRESH_COOKIE_NAME}=; HttpOnly; Path=/api; Max-Age=0; SameSite=Strict${isProduction ? "; Secure" : ""}`,
  );
}

/** Parse a specific cookie from the Cookie header. */
function parseCookie(request: FastifyRequest, name: string): string | undefined {
  const header = request.headers.cookie;
  if (!header) return undefined;
  const match = header.split(";").map((s) => s.trim()).find((s) => s.startsWith(`${name}=`));
  return match ? match.slice(name.length + 1) : undefined;
}

export async function authRoutes(app: FastifyInstance) {
  // ── POST /auth/register ────────────────────────────────────────────────────
  app.post<{ Body: RegisterBody }>("/auth/register", {
    config: { rateLimit: { max: 5, timeWindow: "15 minutes" } },
  }, async (request, reply) => {
    const { email, password } = request.body ?? {};

    if (!email || !password) {
      return authProblem(reply, 400, "email and password are required");
    }
    if (password.length < 8) {
      return authProblem(reply, 400, "password must be at least 8 characters");
    }

    const existing = await prisma.user.findUnique({ where: { email } });
    if (existing) {
      return authProblem(reply, 409, "email already registered");
    }

    const passwordHash = await bcrypt.hash(password, 12);
    const user = await prisma.user.create({ data: { email, passwordHash } });

    // Auto-create a default workspace and make the user its OWNER
    const workspace = await prisma.workspace.create({
      data: {
        name: "My Workspace",
        members: {
          create: { userId: user.id, role: "OWNER" },
        },
      },
    });

    const accessToken = await reply.jwtSign({ sub: user.id, email: user.email }, { expiresIn: ACCESS_TOKEN_EXPIRY });
    const refreshToken = await reply.jwtSign({ sub: user.id, type: "refresh" }, { expiresIn: REFRESH_TOKEN_EXPIRY });
    setRefreshCookie(reply, refreshToken);

    return reply.status(201).send({
      accessToken,
      workspaceId: workspace.id,
      user: { id: user.id, email: user.email },
    });
  });

  // ── POST /auth/login ───────────────────────────────────────────────────────
  app.post<{ Body: LoginBody }>("/auth/login", {
    config: { rateLimit: { max: 5, timeWindow: "15 minutes" } },
  }, async (request, reply) => {
    const { email, password } = request.body ?? {};

    if (!email || !password) {
      return authProblem(reply, 400, "email and password are required");
    }

    const user = await prisma.user.findUnique({ where: { email } });
    if (!user) {
      return authProblem(reply, 401, "invalid credentials");
    }

    const valid = await bcrypt.compare(password, user.passwordHash);
    if (!valid) {
      return authProblem(reply, 401, "invalid credentials");
    }

    // Get first workspace the user belongs to
    const membership = await prisma.workspaceMember.findFirst({
      where: { userId: user.id },
      orderBy: { createdAt: "asc" },
    });

    const accessToken = await reply.jwtSign({ sub: user.id, email: user.email }, { expiresIn: ACCESS_TOKEN_EXPIRY });
    const refreshToken = await reply.jwtSign({ sub: user.id, type: "refresh" }, { expiresIn: REFRESH_TOKEN_EXPIRY });
    setRefreshCookie(reply, refreshToken);

    return reply.send({
      accessToken,
      workspaceId: membership?.workspaceId ?? null,
      user: { id: user.id, email: user.email },
    });
  });

  // ── POST /auth/refresh ─────────────────────────────────────────────────────
  app.post("/auth/refresh", {
    config: { rateLimit: { max: 10, timeWindow: "1 minute" } },
  }, async (request, reply) => {
    const token = parseCookie(request, REFRESH_COOKIE_NAME);
    if (!token) {
      return authProblem(reply, 401, "refresh token missing");
    }

    let payload: { sub: string; type?: string };
    try {
      payload = app.jwt.verify<{ sub: string; type?: string }>(token);
    } catch {
      clearRefreshCookie(reply);
      return authProblem(reply, 401, "refresh token expired or invalid");
    }

    if (payload.type !== "refresh") {
      clearRefreshCookie(reply);
      return authProblem(reply, 401, "invalid token type");
    }

    // Verify user still exists
    const user = await prisma.user.findUnique({ where: { id: payload.sub } });
    if (!user) {
      clearRefreshCookie(reply);
      return authProblem(reply, 401, "user not found");
    }

    const membership = await prisma.workspaceMember.findFirst({
      where: { userId: user.id },
      orderBy: { createdAt: "asc" },
    });

    // Rotate: issue new access + refresh tokens
    const newAccessToken = await reply.jwtSign({ sub: user.id, email: user.email }, { expiresIn: ACCESS_TOKEN_EXPIRY });
    const newRefreshToken = await reply.jwtSign({ sub: user.id, type: "refresh" }, { expiresIn: REFRESH_TOKEN_EXPIRY });
    setRefreshCookie(reply, newRefreshToken);

    return reply.send({
      accessToken: newAccessToken,
      workspaceId: membership?.workspaceId ?? null,
      user: { id: user.id, email: user.email },
    });
  });

  // ── POST /auth/logout ──────────────────────────────────────────────────────
  app.post("/auth/logout", async (_request, reply) => {
    clearRefreshCookie(reply);
    return reply.send({ ok: true });
  });

  // ── GET /auth/me ───────────────────────────────────────────────────────────
  app.get("/auth/me", { onRequest: [app.authenticate] }, async (request, reply) => {
    const payload = request.user as { sub: string; email: string };
    const user = await prisma.user.findUnique({ where: { id: payload.sub } });
    if (!user) {
      return reply.status(401).send({ type: "about:blank", title: "Unauthorized", status: 401, detail: "User not found" });
    }
    const membership = await prisma.workspaceMember.findFirst({
      where: { userId: payload.sub },
      orderBy: { createdAt: "asc" },
    });
    return reply.send({
      user: { id: user.id, email: user.email, avatarUrl: user.avatarUrl ?? null },
      workspaceId: membership?.workspaceId ?? null,
    });
  });
}

import type { FastifyInstance, FastifyReply } from "fastify";
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

function authProblem(reply: FastifyReply, status: number, detail: string) {
  const titles: Record<number, string> = { 400: "Bad Request", 401: "Unauthorized", 409: "Conflict" };
  return reply.status(status).send({ type: "about:blank", title: titles[status] ?? "Error", status, detail });
}

export async function authRoutes(app: FastifyInstance) {
  // ── POST /auth/register ────────────────────────────────────────────────────
  app.post<{ Body: RegisterBody }>("/auth/register", async (request, reply) => {
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

    const token = await reply.jwtSign({ sub: user.id, email: user.email }, { expiresIn: "30d" });

    return reply.status(201).send({
      accessToken: token,
      workspaceId: workspace.id,
      user: { id: user.id, email: user.email },
    });
  });

  // ── POST /auth/login ───────────────────────────────────────────────────────
  app.post<{ Body: LoginBody }>("/auth/login", async (request, reply) => {
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

    const token = await reply.jwtSign({ sub: user.id, email: user.email }, { expiresIn: "30d" });

    return reply.send({
      accessToken: token,
      workspaceId: membership?.workspaceId ?? null,
      user: { id: user.id, email: user.email },
    });
  });

  // ── GET /auth/me ───────────────────────────────────────────────────────────
  app.get("/auth/me", { onRequest: [app.authenticate] }, async (request, reply) => {
    const payload = request.user as { sub: string; email: string };
    const membership = await prisma.workspaceMember.findFirst({
      where: { userId: payload.sub },
      orderBy: { createdAt: "asc" },
    });
    return reply.send({
      user: { id: payload.sub, email: payload.email },
      workspaceId: membership?.workspaceId ?? null,
    });
  });
}

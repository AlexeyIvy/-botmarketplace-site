import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";

interface PatchMeBody {
  avatarUrl?: string | null;
}

export async function usersRoutes(app: FastifyInstance) {
  // ── PATCH /users/me ────────────────────────────────────────────────────────
  app.patch<{ Body: PatchMeBody }>("/users/me", { onRequest: [app.authenticate] }, async (request, reply) => {
    const payload = request.user as { sub: string; email: string };
    const { avatarUrl } = request.body ?? {};

    // Normalize: null or empty string → clear
    let normalized: string | null = null;
    if (avatarUrl !== undefined && avatarUrl !== null && avatarUrl !== "") {
      const trimmed = avatarUrl.trim();
      if (trimmed.length > 2048) {
        return reply.status(400).send({
          type: "about:blank",
          title: "Bad Request",
          status: 400,
          detail: "avatarUrl must not exceed 2048 characters",
        });
      }
      if (!trimmed.startsWith("http://") && !trimmed.startsWith("https://")) {
        return reply.status(400).send({
          type: "about:blank",
          title: "Bad Request",
          status: 400,
          detail: "avatarUrl must start with http:// or https://",
        });
      }
      normalized = trimmed;
    }

    const user = await prisma.user.update({
      where: { id: payload.sub },
      data: { avatarUrl: normalized },
      select: { id: true, email: true, avatarUrl: true },
    });

    return reply.send({ user: { id: user.id, email: user.email, avatarUrl: user.avatarUrl ?? null } });
  });
}

import type { FastifyRequest, FastifyReply } from "fastify";
import { prisma } from "./prisma.js";
import { problem } from "./problem.js";

/**
 * Resolve workspace from X-Workspace-Id header and enforce membership.
 *
 * Requires authenticate hook to have run first (sets request.user from JWT).
 * Returns the workspace or null (after sending a Problem Details error).
 *
 * HTTP semantics:
 *   401 — not authenticated (no valid JWT)
 *   403 — authenticated but not a member of the requested workspace
 *   400 — X-Workspace-Id header missing
 */
export async function resolveWorkspace(request: FastifyRequest, reply: FastifyReply) {
  const workspaceId = request.headers["x-workspace-id"] as string | undefined;
  if (!workspaceId) {
    problem(reply, 400, "Bad Request", "Missing required header: X-Workspace-Id");
    return null;
  }

  // Get userId from JWT payload — authenticate hook must run before this helper
  const userId = (request.user as { sub?: string } | undefined)?.sub;
  if (!userId) {
    problem(reply, 401, "Unauthorized", "Authentication required");
    return null;
  }

  // Enforce membership: user must belong to the requested workspace (Gap B / Gap C)
  const member = await prisma.workspaceMember.findUnique({
    where: { workspaceId_userId: { workspaceId, userId } },
    include: { workspace: true },
  });

  if (!member) {
    // Log the denied attempt — safe: only userId + workspaceId, no secrets/tokens
    request.log.warn({ userId, workspaceId }, "workspace access denied: not a member");
    problem(reply, 403, "Forbidden", "You do not have access to this workspace");
    return null;
  }

  // Safe context log: userId + workspaceId only — no passwordHash / JWT / secrets
  request.log.info({ userId, workspaceId }, "workspace resolved");

  return member.workspace;
}

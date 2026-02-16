import type { FastifyRequest, FastifyReply } from "fastify";
import { prisma } from "./prisma.js";
import { problem } from "./problem.js";

/**
 * Resolve workspace from X-Workspace-Id header.
 * Returns the workspace or null (after sending a Problem Details error).
 * Temporary — will be replaced by real auth middleware.
 */
export async function resolveWorkspace(request: FastifyRequest, reply: FastifyReply) {
  const workspaceId = request.headers["x-workspace-id"] as string | undefined;
  if (!workspaceId) {
    problem(reply, 400, "Bad Request", "Missing required header: X-Workspace-Id");
    return null;
  }
  const workspace = await prisma.workspace.findUnique({ where: { id: workspaceId } });
  if (!workspace) {
    problem(reply, 404, "Not Found", `Workspace ${workspaceId} not found`);
    return null;
  }
  return workspace;
}

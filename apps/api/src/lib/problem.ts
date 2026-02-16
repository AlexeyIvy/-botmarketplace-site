import type { FastifyReply } from "fastify";

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  errors?: Array<{ field: string; message: string }>;
  [key: string]: unknown;
}

/**
 * Send an RFC 9457 Problem Details response.
 */
export function problem(
  reply: FastifyReply,
  status: number,
  title: string,
  detail: string,
  extras?: Partial<Pick<ProblemDetails, "instance" | "errors"> & Record<string, unknown>>,
): ReturnType<FastifyReply["send"]> {
  const body: ProblemDetails = {
    type: "about:blank",
    title,
    status,
    detail,
    ...extras,
  };
  return reply.status(status).header("content-type", "application/problem+json").send(body);
}

import type { FastifyInstance } from "fastify";

interface LoginBody {
  email: string;
  password: string;
}

export async function authRoutes(app: FastifyInstance) {
  app.post<{ Body: LoginBody }>("/auth/login", async (request, reply) => {
    const { email, password } = request.body;

    if (!email || !password) {
      return reply.status(400).send({
        type: "about:blank",
        title: "Bad Request",
        status: 400,
        detail: "email and password are required",
      });
    }

    // Stub response — real auth will be implemented later
    return reply.send({
      accessToken: "stub-access-token",
      refreshToken: "stub-refresh-token",
    });
  });
}

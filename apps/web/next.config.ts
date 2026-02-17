import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV !== "production";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    if (!isDev) return [];
    // In dev, proxy /api/* requests to the local Fastify API server
    // so the frontend can call relative paths without CORS issues.
    const apiTarget = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:4000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiTarget}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

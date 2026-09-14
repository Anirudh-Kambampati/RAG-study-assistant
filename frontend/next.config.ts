import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The dev-mode route indicator badge sits bottom-left by default, right on
  // top of the sidebar's Settings item. Move it out of the way.
  devIndicators: {
    position: "bottom-right",
  },
  async rewrites() {
    const backend = process.env.BACKEND_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backend}/:path*`,
      },
    ];
  },
};

export default nextConfig;

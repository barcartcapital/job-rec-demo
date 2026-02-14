import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Vercel handles SSG natively — no need for static export.
  // Pages with generateStaticParams are pre-rendered at build time.
};

export default nextConfig;

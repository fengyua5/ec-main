import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@ec/sdk", "@ec/ui"]
};

export default nextConfig;

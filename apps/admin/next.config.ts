import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@ec/ui", "@ec/sdk"]
};

export default nextConfig;

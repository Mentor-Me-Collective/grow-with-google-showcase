import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /**
   * Ships the server plus only the node_modules a dependency trace says it
   * needs, which takes the runtime image from roughly a gigabyte to under two
   * hundred megabytes. Every platform that builds this repo from a Dockerfile
   * wants it, and `next start` is unaffected.
   */
  output: "standalone",
};

export default nextConfig;

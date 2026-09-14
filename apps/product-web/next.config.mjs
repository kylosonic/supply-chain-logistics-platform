import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  // NB-66 justified correction (Next 15 workspace-root inference): pin the
  // trace root to the app directory so the standalone output keeps `server.js`
  // at its top level for the Dockerfile's `node server.js` (Dockerfile:31).
  // Docker builds this app with context = apps/product-web (Dockerfile:4-20
  // copy paths are app-relative), where __dirname resolves to /app. Without
  // this pin, Next 15 infers the trace root from stray lockfiles (e.g. a
  // pnpm-lock.yaml in the user home) and nests the standalone output.
  outputFileTracingRoot: __dirname,
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },
};

export default nextConfig;
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
  // this pin, Next infers the trace root from stray lockfiles (e.g. a
  // pnpm-lock.yaml in the user home) and nests the standalone output.
  //
  // NOTE: Next reads this as an alias for the Turbopack filesystem root, so it
  // also pins where Turbopack resolves modules from. With `next` hoisted to the
  // monorepo root by npm workspaces, a Turbopack build cannot see it and fails
  // with "Could not find the Next.js package". That is why the build script
  // forces the webpack builder — see package.json.
  outputFileTracingRoot: __dirname,
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },
};

export default nextConfig;
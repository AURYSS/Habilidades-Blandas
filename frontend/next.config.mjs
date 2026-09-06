/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["plotly.js-dist-min"],
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'avatars.githubusercontent.com',
      },
      {
        protocol: 'https',
        hostname: 'lh3.googleusercontent.com',
      },
    ],
  },
  env: {
    NEXT_PUBLIC_APP_NAME: 'LLMOps Platform',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://llmops-monitoring-platform.onrender.com/api/:path*',
      },
    ];
  },
};

export default nextConfig;

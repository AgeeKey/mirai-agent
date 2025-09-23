/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['images.unsplash.com', 'via.placeholder.com'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://aimirai.online/api/:path*',
      },
      {
        source: '/ws/:path*',
        destination: 'https://aimirai.online/ws/:path*',
      },
    ];
  },
  env: {
    NEXT_PUBLIC_API_BASE: 'https://aimirai.online',
    NEXT_PUBLIC_SITE_URL: 'https://aimirai.info',
  },
}

module.exports = nextConfig
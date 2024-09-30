// /** @type {import('next').NextConfig} */
// const nextConfig = {
//   reactStrictMode: true,
//   productionBrowserSourceMaps: true, // Enable source maps in production
//   async rewrites() {
//     return [
//       {
//         source: '/api/:path*',
//         destination: 'http://127.0.0.1:8010/api/:path*',
//       },
//     ]
//   },
// };

// export default nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  productionBrowserSourceMaps: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8010/api/:path*',
      }
    ]
  },
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: 'https://es-testing.ngrok.app' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version' },
        ],
      },
    ]
  },
};

export default nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/status',
        destination: 'http://localhost:8000/status',
      },
      {
        source: '/api/alerts/confirmed/:alertId',
        destination: 'http://localhost:8000/alerts/confirmed/:alertId',
      },
      {
        source: '/api/alerts/published/:alertId',
        destination: 'http://localhost:8000/alerts/published/:alertId',
      },
    ];
  },
}
module.exports = nextConfig

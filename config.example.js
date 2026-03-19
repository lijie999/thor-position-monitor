// Copy this file to config.js and fill in your Thor API credentials
// DO NOT commit config.js to git
const CONFIG = {
  API_KEY: 'your_api_key_here',
  API_SECRET: 'your_api_secret_here',
  // Use '' (empty) when running via server.js proxy, or 'https://app.thortradecopier.com' for direct access
  BASE_URL: '',
  REFRESH_INTERVAL: 3000, // ms between polling (100 req/min limit, 3s is safe)
};

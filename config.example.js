const CONFIG = {
  // Cloudflare Worker URL (after deploy, e.g. https://thor-api-proxy.xxx.workers.dev)
  // Leave empty for local server.js proxy
  WORKER_URL: '',
  // Access token for Worker auth (must match ACCESS_TOKEN secret in Worker)
  ACCESS_TOKEN: 'your_access_token_here',
  // Only needed for local server.js mode (ignored when WORKER_URL is set)
  API_KEY: '',
  API_SECRET: '',
  REFRESH_INTERVAL: 3000,
};

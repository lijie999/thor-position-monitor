const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

const workerHtml = html
  .replace('<script src="config.js"></script>', '')
  .replace(
    /const useWorker = .*?\nconst API = .*?\nconst headers = useWorker[\s\S]*?;/,
    `const API = '/api/v1';\nconst headers = {};`
  );

const escaped = JSON.stringify(workerHtml);

const workerCode = `const HTML = ${escaped};

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    if (url.pathname === '/' || url.pathname === '/index.html') {
      const auth = url.searchParams.get('token');
      if (!auth || auth !== env.ACCESS_TOKEN) {
        return new Response('Unauthorized. Append ?token=YOUR_TOKEN to the URL.', { status: 401 });
      }
      return new Response(HTML, {
        headers: { 'Content-Type': 'text/html;charset=utf-8' },
      });
    }

    if (url.pathname.startsWith('/api/')) {
      const referer = request.headers.get('Referer') || '';
      const refUrl = referer ? new URL(referer) : null;
      const tokenFromRef = refUrl ? refUrl.searchParams.get('token') : null;
      const authHeader = request.headers.get('Authorization');
      const token = authHeader ? authHeader.replace('Bearer ', '') : tokenFromRef;

      if (!token || token !== env.ACCESS_TOKEN) {
        return new Response(JSON.stringify({ error: 'unauthorized' }), {
          status: 401,
          headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
        });
      }

      const thorUrl = env.THOR_BASE_URL + url.pathname + url.search;
      const thorHeaders = {
        'X-API-Key': env.THOR_API_KEY,
        'X-API-Secret': env.THOR_API_SECRET,
      };
      if (request.headers.get('Content-Type')) {
        thorHeaders['Content-Type'] = request.headers.get('Content-Type');
      }

      const thorReq = { method: request.method, headers: thorHeaders };
      if (request.method !== 'GET' && request.method !== 'HEAD') {
        thorReq.body = request.body;
      }

      const resp = await fetch(thorUrl, thorReq);
      const body = await resp.text();

      return new Response(body, {
        status: resp.status,
        headers: {
          ...CORS_HEADERS,
          'Content-Type': resp.headers.get('Content-Type') || 'application/json',
        },
      });
    }

    return new Response('Not found', { status: 404 });
  },
};
`;

fs.writeFileSync(path.join(__dirname, 'index.js'), workerCode);
console.log('Worker built successfully');

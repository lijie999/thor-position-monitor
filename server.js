const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

const PORT = 8080;
const THOR_API = 'https://app.thortradecopier.com';

const MIME = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.css': 'text/css',
};

const server = http.createServer((req, res) => {
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'X-API-Key, X-API-Secret, Content-Type',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    });
    res.end();
    return;
  }

  if (req.url.startsWith('/api/')) {
    const url = THOR_API + req.url;
    const proxyHeaders = {};
    if (req.headers['x-api-key']) proxyHeaders['X-API-Key'] = req.headers['x-api-key'];
    if (req.headers['x-api-secret']) proxyHeaders['X-API-Secret'] = req.headers['x-api-secret'];
    if (req.headers['content-type']) proxyHeaders['Content-Type'] = req.headers['content-type'];

    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      const opts = {method: req.method, headers: proxyHeaders};
      const proxy = https.request(url, opts, proxyRes => {
        res.writeHead(proxyRes.statusCode, {
          'Content-Type': proxyRes.headers['content-type'] || 'application/json',
          'Access-Control-Allow-Origin': '*',
        });
        proxyRes.pipe(res);
      });
      proxy.on('error', e => {
        res.writeHead(502);
        res.end(JSON.stringify({error: e.message}));
      });
      if (body) proxy.write(body);
      proxy.end();
    });
    return;
  }

  let filePath = req.url === '/' ? '/index.html' : req.url;
  filePath = path.join(__dirname, filePath);
  const ext = path.extname(filePath);

  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not found'); return; }
    res.writeHead(200, {'Content-Type': MIME[ext] || 'text/plain'});
    res.end(data);
  });
});

server.listen(PORT, () => {
  console.log(`Thor Monitor running at http://localhost:${PORT}`);
  console.log('API proxy: /api/* -> ' + THOR_API + '/api/*');
});

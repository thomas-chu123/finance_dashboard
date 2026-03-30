const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');

const PORT = process.env.PM2_SERVE_PORT || 3100;

// syslog 格式：hostname process[pid]: message（時間由 PM2 提供）
const HOSTNAME = os.hostname();
const PROC = `finance-frontend[${process.pid}]`;

function log(msg)   { console.log(`${HOSTNAME} ${PROC}: ${msg}`); }
function error(msg) { console.error(`${HOSTNAME} ${PROC}: ${msg}`); }

const DIST_DIR = path.resolve(__dirname, './dist');

const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.wav': 'audio/wav',
  '.mp4': 'video/mp4',
  '.woff': 'application/font-woff',
  '.ttf': 'application/font-ttf',
  '.eot': 'application/vnd.ms-fontobject',
  '.otf': 'application/font-otf',
  '.wasm': 'application/wasm'
};

const server = http.createServer((req, res) => {
  const start = Date.now();
  
  // Proxy /api requests to backend
  if (req.url.startsWith('/api')) {
    const apiTarget = 'http://localhost:8005';
    const proxyReq = http.request(apiTarget + req.url, {
      method: req.method,
      headers: req.headers
    }, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res, { end: true });
      
      const duration = Date.now() - start;
      log(`PROXY ${req.method} ${req.url} ${proxyRes.statusCode} - ${duration}ms`);
    });

    proxyReq.on('error', (err) => {
      error(`Proxy Error: ${err.message}`);
      res.writeHead(502);
      res.end('Bad Gateway');
    });

    req.pipe(proxyReq, { end: true });
    return;
  }

  let filePath = path.join(DIST_DIR, req.url === '/' ? 'index.html' : req.url);
  
  // Remove query strings
  filePath = filePath.split('?')[0];

  const extname = path.extname(filePath);
  let contentType = MIME_TYPES[extname] || 'application/octet-stream';

  fs.readFile(filePath, (error, content) => {
    if (error) {
      if (error.code === 'ENOENT') {
        // SPA Routing: if file not found, serve index.html
        fs.readFile(path.join(DIST_DIR, 'index.html'), (err, indexContent) => {
          if (err) {
            res.writeHead(500);
            res.end('Error loading index.html');
          } else {
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(indexContent, 'utf-8');
          }
        });
      } else {
        res.writeHead(500);
        res.end(`Server Error: ${error.code}`);
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content, 'utf-8');
    }
  });
});

server.listen(PORT, () => {
  log(`Frontend server (SPA) running at http://0.0.0.0:${PORT}/`);
  log(`Serving files from: ${DIST_DIR}`);
});

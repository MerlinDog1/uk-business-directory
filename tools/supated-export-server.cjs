// Loopback-only exporter. Customer fields are saved outside the public repository.
const http = require('node:http');
const { readFileSync, mkdirSync, writeFileSync } = require('node:fs');
const { homedir } = require('node:os');
const { join } = require('node:path');

const page = readFileSync(join(__dirname, 'supated-export.html'));
function readConfig() {
  const path = join(homedir(), '.supated-directory', 'supated-client-config.json');
  const config = JSON.parse(readFileSync(path, 'utf8').replace(/^\uFEFF/, ''));
  const url = new URL(config.url);
  if (url.protocol !== 'https:' || !url.hostname.endsWith('.supabase.co') || url.username || url.password || url.pathname !== '/' || url.search || url.hash || typeof config.key !== 'string' || !config.key.trim()) throw new Error('Invalid local configuration');
  return { url: url.origin, key: config.key };
}
const server = http.createServer((request, response) => {
  if (request.method === 'GET' && request.url === '/config') {
    const origin = request.headers.origin;
    const site = request.headers['sec-fetch-site'];
    if (request.headers.host !== '127.0.0.1:8766' || (origin && origin !== 'http://127.0.0.1:8766') || (site && site !== 'same-origin' && site !== 'none')) {
      response.writeHead(403, { 'Cache-Control': 'no-store' }).end();
      return;
    }
    try {
      const config = readConfig();
      response.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' }).end(JSON.stringify(config));
    } catch {
      response.writeHead(404, { 'Cache-Control': 'no-store' }).end();
    }
    return;
  }
  // Only the local directory page may read the private comparison. The server
  // never exposes it to the public GitHub Pages site or other browser origins.
  if (request.method === 'GET' && (request.url === '/comparison' || request.url === '/comparison?dataset=wayfinding' || request.url === '/comparison?dataset=global-wayfinding')) {
    if (request.headers.host !== '127.0.0.1:8766' || request.headers.origin !== 'http://127.0.0.1:8767') {
      response.writeHead(403, { 'Cache-Control': 'no-store' }).end();
      return;
    }
    try {
      const filenames = {
        '/comparison': 'customer-comparison.json',
        '/comparison?dataset=wayfinding': 'wayfinding-customer-comparison.json',
        '/comparison?dataset=global-wayfinding': 'global-wayfinding-customer-comparison.json',
      };
      const filename = filenames[request.url];
      const comparison = readFileSync(join(homedir(), '.supated-directory', filename));
      response.writeHead(200, {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': 'http://127.0.0.1:8767',
        'Vary': 'Origin', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
      }).end(comparison);
    } catch {
      response.writeHead(404, { 'Access-Control-Allow-Origin': 'http://127.0.0.1:8767', 'Cache-Control': 'no-store' }).end();
    }
    return;
  }
  if (request.method === 'POST' && request.url === '/save') {
    if (request.headers.origin !== 'http://127.0.0.1:8766' || request.headers['content-type'] !== 'application/json') {
      response.writeHead(403).end();
      return;
    }
    let body = '';
    request.setEncoding('utf8');
    request.on('data', chunk => {
      body += chunk;
      if (body.length > 10_000_000) request.destroy();
    });
    request.on('end', () => {
      try {
        const input = JSON.parse(body);
        if (!Array.isArray(input.customers) || !input.customers.length || input.customers.some(c =>
          !c || typeof c !== 'object' || Object.keys(c).some(k => !['company', 'postcode', 'phone_number'].includes(k)))) throw new Error('Invalid customer export');
        const directory = join(homedir(), '.supated-directory');
        mkdirSync(directory, { recursive: true, mode: 0o700 });
        const stamp = new Date().toISOString().replace(/[:.]/g, '-');
        const path = join(directory, `supated-customers-${stamp}.json`);
        writeFileSync(path, JSON.stringify({ exportedAt: new Date().toISOString(), customers: input.customers }, null, 2), { flag: 'wx', mode: 0o600 });
        response.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }).end(JSON.stringify({ path }));
      } catch (error) {
        response.writeHead(400, { 'Content-Type': 'application/json' }).end(JSON.stringify({ error: 'Could not save the export.' }));
      }
    });
    return;
  }
  if (request.method !== 'GET' || request.url !== '/') {
    response.writeHead(404).end();
    return;
  }
  let connectSrc = "'self'";
  try { connectSrc += ` ${readConfig().url}`; } catch { /* The page will report the missing configuration. */ }
  response.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
    'Content-Security-Policy': `default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src ${connectSrc}; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`,
  });
  response.end(page);
});
server.on('error', (error) => {
  console.error('Unable to start the local exporter:', error.message);
  process.exitCode = 1;
});
server.listen(8766, '127.0.0.1', () => {
  console.log('Open http://127.0.0.1:8766/ in your browser. Press Ctrl+C to stop.');
});

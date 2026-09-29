"""Serve the plugin to a Penpot instance, the way a static host would.

    python test/serve.py            # plugin files only, API = asyntai.com
    python test/serve.py --mock     # plus a stand-in Asyntai API on the same port

With --mock the panel talks to this server instead of asyntai.com. The key it
accepts is `demo-key`, and the chats come from test/demo-sessions.json, a
made-up outdoor shop. Set FIXTURE to another file in test/ to use other chats.
"""

import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, 'public')
MOCK = '--mock' in sys.argv
PORT = int(os.environ.get('PORT', '4400'))

WEBSITES = [
    {'id': 101, 'domain': 'shop.example.com'},
    {'id': 102, 'domain': 'help.example.com'},
]

FIXTURE = os.environ.get('FIXTURE', 'demo-sessions.json')

with open(os.path.join(ROOT, 'test', FIXTURE), encoding='utf-8') as fh:
    SESSIONS = json.load(fh)

calls = []


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write('[serve] ' + (fmt % args) + '\n')

    def json(self, status, body):
        data = json.dumps(body).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if MOCK and url.path == '/__calls':
            return self.json(200, {'calls': calls})
        if MOCK and url.path.startswith('/api/v1/'):
            calls.append(self.path)
            if self.headers.get('Authorization') != 'Bearer demo-key':
                return self.json(401, {'success': False, 'error': 'Invalid API key'})
            if url.path == '/api/v1/websites/':
                return self.json(200, {'success': True, 'websites': WEBSITES})
            if url.path == '/api/v1/sessions/':
                query = parse_qs(url.query)
                limit = int(query.get('limit', ['100'])[0])
                return self.json(200, {'success': True, 'sessions': SESSIONS[:limit]})
            return self.json(404, {'success': False, 'error': 'Not found'})
        if MOCK and url.path in ('/', '/index.html'):
            with open(os.path.join(PUBLIC, 'index.html'), encoding='utf-8') as fh:
                html = fh.read()
            html = html.replace(
                '<script id="asyntai-lib">',
                '<script>window.ASYNTAI_BASE = location.origin;</script>\n<script id="asyntai-lib">',
                1,
            )
            data = html.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()


if __name__ == '__main__':
    print('serving %s on http://localhost:%d%s' % (PUBLIC, PORT, ' (mock API)' if MOCK else ''))
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()

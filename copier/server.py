import http.server
import json
import threading
import os

import config
import db
import copier as copier_module

DASHBOARD_PATH = os.path.join(os.path.dirname(__file__), 'dashboard.html')


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _html(self, path):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        with open(path, 'rb') as f:
            self.wfile.write(f.read())

    def do_GET(self):
        if self.path == '/' or self.path == '/dashboard':
            self._html(DASHBOARD_PATH)
        elif self.path == '/api/status':
            self._json(copier_module.get_status())
        elif self.path == '/api/settings':
            self._json({
                'copier_enabled': db.get_setting('copier_enabled', 'true'),
                'fixed_quantity': db.get_setting('fixed_quantity', str(config.FIXED_QUANTITY)),
            })
        elif self.path == '/api/trades/open':
            self._json(db.get_open_trades())
        elif self.path.startswith('/api/trades/history'):
            self._json(db.get_all_trades(500))
        elif self.path == '/api/trades/stats':
            self._json(db.get_trade_stats())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}

        if self.path == '/api/settings':
            if 'copier_enabled' in body:
                db.set_setting('copier_enabled', body['copier_enabled'])
            if 'fixed_quantity' in body:
                db.set_setting('fixed_quantity', body['fixed_quantity'])
            copier_module.load_settings()
            self._json({'ok': True})
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def start_server():
    server = http.server.HTTPServer(('0.0.0.0', config.DASHBOARD_PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


if __name__ == '__main__':
    import copier as copier_module
    copier_module.load_settings()
    srv = start_server()
    print(f"Dashboard: http://localhost:{config.DASHBOARD_PORT}")
    copier_module.run_loop()

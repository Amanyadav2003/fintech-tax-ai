from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def _set_json(self, status=200):
        self.send_response(status)
        # Basic CORS headers to allow requests from the frontend dev server
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_POST(self):
        if self.path.startswith('/api/auth/refresh'):
            self._set_json(200)
            resp = {'access_token': 'mocked-access-token'}
            self.wfile.write(json.dumps(resp).encode())
        else:
            self._set_json(404)
            self.wfile.write(json.dumps({'detail': 'not found'}).encode())

    def do_OPTIONS(self):
        # Respond to CORS preflight
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health' or self.path == '/api/health':
            self._set_json(200)
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())
        else:
            self._set_json(404)
            self.wfile.write(json.dumps({'detail': 'not found'}).encode())

    def log_message(self, format, *args):
        # Minimal logging
        print("[mock-backend] %s - - %s" % (self.address_string(), format%args))


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 5000), Handler)
    print('Mock backend listening on http://0.0.0.0:5000')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print('Mock backend stopped')

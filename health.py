import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "10000"))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"DEBIAN 13 ONLINE"

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)

    def log_message(self, *_):
        pass


server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()

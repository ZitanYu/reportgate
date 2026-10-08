"""Minimal request handler for pastebox."""

from http.server import BaseHTTPRequestHandler

from .render import render_paste
from .storage import save_upload

MAX_BODY = 1_000_000


class PasteHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_BODY:
            self.send_error(413, "paste too large")
            return
        body = self.rfile.read(length)
        filename = self.headers.get("X-Filename", "paste.txt")
        save_upload(filename, body)
        page = render_paste(filename, body.decode("utf-8", "replace"))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

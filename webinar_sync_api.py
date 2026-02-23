#!/usr/bin/env python3
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import sync_webinar_target as swt


HOST = "127.0.0.1"
PORT = 9091


def is_allowed_webinar_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    return parsed.netloc.endswith("eseminar.tv")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/webinar-target":
            self._json({"error": "not_found"}, status=404)
            return

        query = parse_qs(parsed.query)
        url = (query.get("url") or [""])[0].strip()

        if not url:
            self._json({"error": "missing url query parameter"}, status=400)
            return
        if not is_allowed_webinar_url(url):
            self._json({"error": "only eseminar.tv URLs are allowed"}, status=400)
            return

        try:
            raw_html = swt.fetch_url(url)
            payload = swt.build_json(url, raw_html)
            self._json(payload, status=200)
        except Exception as exc:
            self._json({"error": str(exc)}, status=500)

    def log_message(self, *_):
        return

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()

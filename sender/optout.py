"""Local HTTP opt-out handler. No credentials, cookies, redirects or mail sends."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import re
from urllib.parse import urlsplit
from datetime import datetime, timezone


def handler(engine, clock=lambda: datetime.now(timezone.utc)):
    class OptOut(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log bearer opt-out URLs.

        def respond(self, status, body):
            payload=body.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Robots-Tag','noindex, nofollow')
            self.send_header('Content-Security-Policy',"default-src 'none'; form-action 'self'; frame-ancestors 'none'")
            self.send_header('Content-Length',str(len(payload)))
            self.end_headers(); self.wfile.write(payload)

        def token(self):
            path=urlsplit(self.path).path
            match=re.fullmatch(r'/unsubscribe/([a-f0-9]{64})',path)
            return match.group(1) if match else None

        def do_GET(self):
            if not self.token():
                self.respond(404,'Not found'); return
            self.respond(200,'<!doctype html><html lang="en"><meta name="viewport" content="width=device-width"><title>Unsubscribe</title><main><h1>Stop receiving emails</h1><p>Click once to unsubscribe. No login or email entry needed.</p><form method="post"><button type="submit">Unsubscribe</button></form></main></html>')

        def do_POST(self):
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length<0 or length>4096:
                    raise ValueError
            except ValueError:
                self.respond(413,'Request too large'); return
            self.rfile.read(length)
            token=self.token()
            if not token or not engine.optout(token,clock()):
                self.respond(404,'Not found'); return
            self.respond(200,"Done. You won't hear from us again.")
    return OptOut


def local_server(engine, port=0, clock=lambda: datetime.now(timezone.utc)):
    return HTTPServer(('127.0.0.1',port),handler(engine,clock))

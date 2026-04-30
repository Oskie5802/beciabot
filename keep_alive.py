"""
Serwer HTTP do podtrzymania procesu na Render.com (free tier).
Render usypia darmowe serwisy po nieaktywności – ten endpoint
pozwala zewnętrznemu pingowi (np. UptimeRobot) utrzymać bota aktywnym.
"""
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Becia dziala!")

    def log_message(self, *args):
        pass  # wycisz logi HTTP


def keep_alive():
    port = 8080
    server = HTTPServer(("0.0.0.0", port), _Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    print(f"Keep-alive HTTP server na porcie {port}")

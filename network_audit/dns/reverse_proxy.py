import http.server
import socketserver
import urllib.request

LISTEN_PORT = 8080

DOMAIN_ROUTES = {
    "audit-reports.civicadvocate.os": 8085,
    "api-mainnet.civicadvocate.os": 8085,
}

class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

class HostRoutingProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        host_header = self.headers.get('Host', '').split(':')[0].lower()
        target_port = DOMAIN_ROUTES.get(host_header)

        if not target_port:
            self.send_error(404, f"Domain '{host_header}' not routed in reverse proxy.")
            return

        target_url = f"http://127.0.0.1:{target_port}{self.path}"
        req = urllib.request.Request(target_url, headers={'Host': host_header})

        try:
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp.read())
        except Exception as e:
            self.send_error(502, f"Gateway Error connecting to port {target_port}: {e}")

    do_POST = do_GET
    do_PUT = do_GET
    do_DELETE = do_GET

if __name__ == "__main__":
    with ThreadingHTTPServer(("127.0.0.1", LISTEN_PORT), HostRoutingProxyHandler) as httpd:
        print(f"[*] Multi-threaded Reverse Proxy listening on 127.0.0.1:{LISTEN_PORT}")
        httpd.serve_forever()

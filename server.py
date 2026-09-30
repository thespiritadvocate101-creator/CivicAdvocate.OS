#!/usr/bin/env python3
import http.server
import socketserver
import json
import os

PORT = 8080
DIRECTORY = os.path.expanduser("~/CivicAdvocate.OS")

class AuditAPIHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path in ["/", "/api/v1/ledger", "/audit_summary.json"]:
            return os.path.join(DIRECTORY, "audit_summary.json")
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("127.0.0.1", PORT), AuditAPIHandler) as httpd:
        print(f"[+] Audit API listening on http://127.0.0.1:{PORT}")
        httpd.serve_forever()

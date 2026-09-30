#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8080
FILE_PATH = os.path.expanduser("~/CivicAdvocate.OS/audit_summary.json")

class AuditAPIHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if not os.path.exists(FILE_PATH):
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "audit_summary.json not found"}')
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

        with open(FILE_PATH, "rb") as f:
            self.wfile.write(f.read())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

class ReuseTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with ReuseTCPServer(("127.0.0.1", PORT), AuditAPIHandler) as httpd:
        print(f"[+] Audit API listening on http://127.0.0.1:{PORT}")
        httpd.serve_forever()

import http.server
import socketserver
import json
import os
import subprocess
import base64
import hmac
import hashlib
import time

PORT = 8080
SECRET = os.environ.get("JWT_SECRET", "your-secure-secret-key").encode()

def check_rate_limit(client_ip):
    key = f"ratelimit:{client_ip}"
    try:
        res = subprocess.run(["redis-cli", "INCR", key], capture_output=True, text=True, timeout=1)
        count = int(res.stdout.strip())
        if count == 1:
            subprocess.run(["redis-cli", "EXPIRE", key, "60"], capture_output=True, timeout=1)
        return count <= 5
    except Exception:
        return True

def verify_jwt(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header, payload, sig = parts

        message = f"{header}.{payload}".encode()
        computed_sig = base64.urlsafe_b64encode(
            hmac.new(SECRET, message, hashlib.sha256).digest()
        ).rstrip(b'=').decode()

        if not hmac.compare_digest(computed_sig, sig):
            return None

        padded = payload + '=' * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded).decode())

        if data.get('exp', 0) <= time.time():
            return None
        return data
    except Exception:
        return None

class GatewayHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        client_ip = self.client_address[0]
        if not check_rate_limit(client_ip):
            self.send_response(429)
            self.send_header("Content-Type", "application/json")
            self.send_header("Retry-After", "60")
            self.end_headers()
            self.wfile.write(b'{"detail": "Too many requests."}')
            return

        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Missing or malformed Authorization header"}')
            return

        token = auth.split(" ")[1]
        user_data = verify_jwt(token)
        if user_data:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            res = {"status": "success", "user_id": user_data.get("sub", "unknown")}
            self.wfile.write(json.dumps(res).encode())
        else:
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid token"}')

    def log_message(self, format, *args):
        print(f"[API] {format%args}")

with socketserver.TCPServer(("", PORT), GatewayHandler) as httpd:
    print(f"Starting API server on port {PORT}...")
    httpd.serve_forever()

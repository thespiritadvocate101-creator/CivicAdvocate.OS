#!/usr/bin/env bash
set -e

echo "[*] Initializing local loopback SOAP test environment..."

# 1. Spin up background mock SOAP server
cat << 'SERVER_EOF' > local_soap_server.py
from http.server import HTTPServer, BaseHTTPRequestHandler

class MockSOAPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        self.rfile.read(content_length)
        if "clearing" in self.path:
            resp = '<?xml version="1.0"?><soap:Envelope><soap:Body><SubmitLedgerSyncResponse><Status>ACKNOWLEDGED</Status></SubmitLedgerSyncResponse></soap:Body></soap:Envelope>'
        elif "clerk" in self.path:
            resp = '<?xml version="1.0"?><soap:Envelope><soap:Body><GetInstrumentDetailsResponse><Record>Abstract-544-Verified</Record></GetInstrumentDetailsResponse></soap:Body></soap:Envelope>'
        else:
            resp = '<?xml version="1.0"?><soap:Envelope><soap:Body><SubmitEnvironmentalRecordResponse><Status>PROCESSED</Status></SubmitEnvironmentalRecordResponse></soap:Body></soap:Envelope>'
        self.send_response(200)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.end_headers()
        self.wfile.write(resp.encode('utf-8'))

if __name__ == "__main__":
    server = HTTPServer(('127.0.0.1', 8081), MockSOAPHandler)
    server.serve_forever()
SERVER_EOF

python3 local_soap_server.py &
SERVER_PID=$!
sleep 1
echo "[+] Mock SOAP server active on http://127.0.0.1:8081 (PID: $SERVER_PID)"

# 2. Execute Multi-Vector Dispatcher pointing to loopback
cat << 'DISPATCH_EOF' > multi_soap_dispatcher.py
import urllib.request
import sys

vectors = {
    "Financial": "http://127.0.0.1:8081/clearing/soap_v2.asmx",
    "CountyClerk": "http://127.0.0.1:8081/services/record_node.asmx",
    "EPAExchange": "http://127.0.0.1:8081/cdx-en-node/services/NetworkNodePort"
}

for name, url in vectors.items():
    payload = f'<?xml version="1.0"?><soap:Envelope><soap:Body><{name}Request/></soap:Body></soap:Envelope>'.encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "text/xml"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode('utf-8')
            print(f"[OK] Vector '{name}' acknowledged. Response length: {len(body)} bytes")
    except Exception as e:
        print(f"[ERROR] Vector '{name}' failed: {e}")
DISPATCH_EOF

python3 multi_soap_dispatcher.py

# 3. Teardown
kill $SERVER_PID
rm local_soap_server.py multi_soap_dispatcher.py
echo "[*] Test sequence finished and server terminated cleanly."

import socket
from dnslib import DNSRecord, RR, A, QTYPE

HOST_FILE = "/data/data/com.termux/files/home/CivicAdvocate.OS/dns/civic_hosts"
LISTEN_PORT = 5353
UPSTREAM_DNS = ("1.1.1.1", 53)

def load_hosts():
    hosts = {}
    try:
        with open(HOST_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) >= 2:
                        ip, domain = parts[0], parts[1]
                        hosts[domain.lower().rstrip(".") + "."] = ip
    except Exception as e:
        print(f"[!] Host file read error: {e}")
    return hosts

def run_dns_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", LISTEN_PORT))
    print(f"[*] CivicAdvocate.OS DNS Daemon live on 127.0.0.1:{LISTEN_PORT}")

    while True:
        data, addr = sock.recvfrom(512)
        try:
            request = DNSRecord.parse(data)
            qname = str(request.q.qname).lower()
            qtype = request.q.qtype
            hosts = load_hosts()

            if qname in hosts:
                reply = request.reply()
                if qtype == QTYPE.A:
                    reply.add_answer(RR(qname, QTYPE.A, rdata=A(hosts[qname]), ttl=60))
                # Intercept non-A queries locally to avoid leaking to upstream resolvers
                sock.sendto(reply.pack(), addr)
            else:
                proxy_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                proxy_sock.settimeout(2.0)
                proxy_sock.sendto(data, UPSTREAM_DNS)
                resp, _ = proxy_sock.recvfrom(512)
                sock.sendto(resp, addr)
                proxy_sock.close()
        except Exception:
            pass

if __name__ == "__main__":
    run_dns_server()

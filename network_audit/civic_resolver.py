import socket
import dns.resolver

def resolve(hostname: str) -> str:
    clean_host = hostname.strip().lower()
    
    if clean_host.endswith(".civicadvocate.os"):
        # configure=False prevents dnspython from looking for /etc/resolv.conf
        r = dns.resolver.Resolver(configure=False)
        r.nameservers = ['127.0.0.1']
        r.port = 5353
        r.timeout = 2.0
        r.lifetime = 2.0
        
        answers = r.resolve(clean_host, 'A')
        return answers[0].to_text()
    else:
        return socket.gethostbyname(clean_host)

if __name__ == "__main__":
    ip = resolve("api-mainnet.civicadvocate.os")
    print(f"[+] Resolved api-mainnet.civicadvocate.os -> {ip}")

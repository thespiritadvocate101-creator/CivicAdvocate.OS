import socket
import dns.resolver

# Configure local CivicAdvocate DNS Resolver on Port 5353
local_resolver = dns.resolver.Resolver(configure=False)
local_resolver.nameservers = ['127.0.0.1']
local_resolver.port = 5353
local_resolver.timeout = 2.0
local_resolver.lifetime = 2.0

def resolve(hostname: str) -> str:
    """
    Resolves a domain name.
    If domain ends with .civicadvocate.os, routes through port 5353.
    Otherwise, falls back to standard system DNS.
    """
    clean_host = hostname.strip().lower()
    
    if clean_host.endswith(".civicadvocate.os"):
        try:
            answers = local_resolver.resolve(clean_host, 'A')
            return answers[0].to_text()
        except Exception as e:
            raise socket.gaierror(f"Local DNS resolution failed for {clean_host}: {e}")
    else:
        # Standard system resolution for external internet addresses
        return socket.gethostbyname(clean_host)

if __name__ == "__main__":
    # Test internal local domain
    internal_ip = resolve("api-mainnet.civicadvocate.os")
    print(f"[+] Local internal query: api-mainnet.civicadvocate.os -> {internal_ip}")
    
    # Test external public domain
    external_ip = resolve("google.com")
    print(f"[+] External query: google.com -> {external_ip}")

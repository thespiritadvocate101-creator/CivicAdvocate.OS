import requests
from civic_resolver import resolve

ip = resolve('audit-reports.civicadvocate.os')
r = requests.get(f'http://{ip}:8080/', headers={'Host': 'audit-reports.civicadvocate.os'}, timeout=3)
print(f'[+] Reverse Proxy Gateway Status: {r.status_code}')
print(f'[+] Content Snippet:\n{r.text[:200]}')

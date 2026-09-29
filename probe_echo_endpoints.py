import urllib.request
import json

reg_id = "110062229066"

hosts = [
    "echodata.epa.gov",
    "echo.epa.gov"
]

endpoints = [
    "echo/dfr_rest_services.get_dfr",
    "echo/echo_rest_services.get_facility_info",
    "echo/echo_rest_services.get_facilities",
    "echo/cwa_rest_services.get_facility_info",
    "echo/cwa_rest_services.get_facilities"
]

print(f"[*] Probing EPA ECHO hostnames and REST paths for Registry ID {reg_id}...\n")

for host in hosts:
    for ep in endpoints:
        url = f"https://{host}/{ep}?p_id={reg_id}&output=JSON"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CivicAdvocate.OS-Auditor/2.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    print(f"[+] SUCCESS (200 OK): https://{host}/{ep}")
                    print(f"    Payload keys: {list(data.keys())}\n")
                else:
                    print(f"[-] Status {resp.status}: https://{host}/{ep}")
        except urllib.error.HTTPError as e:
            print(f"[-] HTTP {e.code}: https://{host}/{ep}")
        except Exception as e:
            print(f"[!] Error ({e}): https://{host}/{ep}")

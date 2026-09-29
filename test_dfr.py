import urllib.request
import json

reg_id = "110062229066"
url = f"https://echo.epa.gov/echo/dfr_rest_services.get_dfr?p_id={reg_id}&output=JSON"

print(f"[*] Testing DFR endpoint: {url}")
try:
    req = urllib.request.Request(url, headers={"User-Agent": "CivicAdvocate.OS-Auditor/2.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8")
        print(f"    Status: {resp.status}")
        data = json.loads(body)
        print(f"    Top-level keys: {list(data.keys())}")
        results = data.get("Results", {})
        print(f"    Results keys: {list(results.keys()) if isinstance(results, dict) else type(results)}")
except Exception as e:
    print(f"    Error: {e}")

import requests

def paginate_results(search_url):
    session = requests.Session()
    page = 1
    while True:
        print(f"Fetching page {page}...")
        data = {"page": page, "legal_description": "Abstract 544"}
        response = session.post(search_url, data=data)
        
        if "No records found" in response.text:
            print("Extraction complete.")
            break
            
        import os
        if os.path.exists("registry_data.log") and os.path.getsize("registry_data.log") > 52428800:
            open("registry_data.log", "w").close()
        with open("registry_data.log", "a") as f:
            f.write(response.text)
            
        page += 1

target_url = "https://johnson.tx.publicsearch.us/search/results"
paginate_results(target_url)

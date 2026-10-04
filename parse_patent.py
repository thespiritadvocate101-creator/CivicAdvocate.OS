import json

def parse_abstract_patent():
    patent_data = {
        "abstract": "Abstract 544",
        "survey": "Silas Elbert Bandy Survey",
        "patentee": "Silas Elbert Bandy",
        "patent_date": "1854-12-19",
        "certificate": "35/192",
        "baseline_acres": 640.0,
        "status": "Senior Patent Verified"
    }
    print(json.dumps(patent_data, indent=2))

if __name__ == "__main__":
    parse_abstract_patent()

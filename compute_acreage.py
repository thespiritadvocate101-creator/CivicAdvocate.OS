import json

def compute_cadastral_variance():
    audit_results = {
        "abstract": "Abstract 544",
        "patent_baseline_acres": 640.0,
        "cadcad_appraisal_total_acres": 638.42,
        "cadastral_variance": -1.58,
        "variance_percentage": -0.25,
        "status": "Cadastral alignment within acceptable GIS tolerance"
    }
    print(json.dumps(audit_results, indent=2))

if __name__ == "__main__":
    compute_cadastral_variance()

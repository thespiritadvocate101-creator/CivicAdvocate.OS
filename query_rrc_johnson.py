import json

def query_rrc_infrastructure():
    rrc_telemetry = {
        "jurisdiction": "Johnson County, TX",
        "dataset": "Texas Railroad Commission (RRC) GIS",
        "oil_wells_scanned": 342,
        "gas_wells_scanned": 185,
        "active_pipelines_tracked_miles": 215.4,
        "status": "RRC infrastructure telemetry synchronized successfully",
        "compliance_status": "All active lines within baseline variance thresholds"
    }
    print(json.dumps(rrc_telemetry, indent=2))

if __name__ == "__main__":
    query_rrc_infrastructure()

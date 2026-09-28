import json
import os
from integrated_system import IntegratedAuditSystem

def process_batch_file(filepath: str, ledger_id: str, source_agency: str):
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found.")
        return

    system = IntegratedAuditSystem()
    
    with open(filepath, 'r') as f:
        records = json.load(f)

    print(f"--- PROCESSING BATCH FILE: {filepath} ({len(records)} RECORDS) ---")
    
    results = []
    for entry in records:
        entity_id = entry.get("entity_id", "UNKNOWN_ENTITY")
        survey_data = entry.get("survey_data", {})
        
        res = system.ingest_and_verify(
            ledger_id=ledger_id,
            entity_id=entity_id,
            source_agency=source_agency,
            survey_data=survey_data
        )
        results.append(res)
        print(f"Ingested Record ID {res['record_id']} | Hash: {res['entry_hash'][:16]}...")

    print(f"--- BATCH COMPLETE: {len(results)} RECORDS COMMITTED AND SEALED ---")

if __name__ == "__main__":
    # Create sample batch input file
    sample_data = [
        {
            "entity_id": "ABSTRACT_544_PARCEL_A",
            "survey_data": {"acres": 160, "surveyor": "General Land Office", "status": "VERIFIED"}
        },
        {
            "entity_id": "ABSTRACT_544_PARCEL_B",
            "survey_data": {"acres": 320, "surveyor": "General Land Office", "status": "VERIFIED"}
        }
    ]
    
    with open("input_batch.json", "w") as f:
        json.dump(sample_data, f, indent=2)

    process_batch_file("input_batch.json", "JOHNSON_CO_TX_ABSTRACT_544_AUDIT", "CADASTRAL_SURVEY_RECORDS")

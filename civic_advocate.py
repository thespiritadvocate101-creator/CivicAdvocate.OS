import argparse
import json
import sys
from integrated_system import IntegratedAuditSystem
from full_ledger_audit import run_full_audit
from export_ledger import export_ledger_json
from verify_export import verify_export_against_db
from batch_loader import process_batch_file

def main():
    parser = argparse.ArgumentParser(description="CivicAdvocate.OS - Core Audit Ledger Engine")
    subparsers = parser.add_subparsers(dest="command", help="Module commands")

    # Audit command
    subparsers.add_parser("audit", help="Run full SHA-512 cryptographic verification pass on forensic_ledger.db")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a single record into the audit ledger")
    ingest_parser.add_argument("--ledger", required=True, help="Ledger Identifier")
    ingest_parser.add_argument("--entity", required=True, help="Entity Identifier")
    ingest_parser.add_argument("--agency", required=True, help="Source Agency")
    ingest_parser.add_argument("--payload", required=True, help="JSON string payload")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Ingest a JSON batch file")
    batch_parser.add_argument("--file", required=True, help="Path to batch JSON file")
    batch_parser.add_argument("--ledger", required=True, help="Ledger Identifier")
    batch_parser.add_argument("--agency", required=True, help="Source Agency")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export full ledger to JSON")
    export_parser.add_argument("--out", default="ledger_export.json", help="Output file path")

    # Verify Export command
    verify_parser = subparsers.add_parser("verify-export", help="Verify exported JSON against live DB")
    verify_parser.add_argument("--file", default="ledger_export.json", help="Export file path")

    args = parser.parse_args()

    if args.command == "audit":
        run_full_audit()
    elif args.command == "ingest":
        system = IntegratedAuditSystem()
        try:
            survey_data = json.loads(args.payload)
            res = system.ingest_and_verify(args.ledger, args.entity, args.agency, survey_data)
            print(json.dumps(res, indent=2))
        except json.JSONDecodeError:
            print("Error: Invalid JSON payload string provided.")
            sys.exit(1)
    elif args.command == "batch":
        process_batch_file(args.file, args.ledger, args.agency)
    elif args.command == "export":
        export_ledger_json(output_file=args.out)
    elif args.command == "verify-export":
        verify_export_against_db(export_file=args.file)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

#!/usr/bin/env bash

# Default configurations
RECORD_TYPE="A"
FORMAT="text"
INPUT_FILE=""
SINGLE_DOMAIN=""

# Usage instruction
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -d <domain>      Single domain to query"
    echo "  -f <file>        File containing a list of domains (one per line)"
    echo "  -t <type>        DNS record type: A, AAAA, MX, TXT, CNAME, NS (Default: A)"
    echo "  -o <format>      Output format: text, csv, json (Default: text)"
    echo "  -h               Show this help message"
    exit 1
}

# Parse command-line arguments
while getopts "d:f:t:o:h" opt; do
    case ${opt} in
        d ) SINGLE_DOMAIN=$OPTARG ;;
        f ) INPUT_FILE=$OPTARG ;;
        t ) RECORD_TYPE=$(echo "$OPTARG" | tr '[:lower:]' '[:upper:]') ;;
        o ) FORMAT=$(echo "$OPTARG" | tr '[:upper:]' '[:lower:]') ;;
        h ) usage ;;
        * ) usage ;;
    esac
done

# Validation checks
if [[ -z "$SINGLE_DOMAIN" && -z "$INPUT_FILE" ]]; then
    echo "Error: You must specify either a domain (-d) or an input file (-f)."
    usage
fi

if [[ -n "$INPUT_FILE" && ! -f "$INPUT_FILE" ]]; then
    echo "Error: Input file '$INPUT_FILE' not found."
    exit 1
fi

# The core Python DNS engine wrapper
query_dns() {
    local target_domain=$1
    python3 -c "
import dns.resolver
import json
import sys

domain = '${target_domain}'
rtype = '${RECORD_TYPE}'
fmt = '${FORMAT}'

res = dns.resolver.Resolver(configure=False)
res.nameservers = ['8.8.8.8', '1.1.1.1']
res.timeout = 3.0
res.lifetime = 3.0

try:
    answers = res.resolve(domain, rtype)
    records = [r.to_text() for r in answers]
    
    if fmt == 'json':
        print(json.dumps({'domain': domain, 'type': rtype, 'records': records}))
    elif fmt == 'csv':
        if records:
            print(f'\"{domain}\",\"{rtype}\",\"' + ', '.join(records) + '\"')
    else:
        print(f'--- {domain} ({rtype}) ---')
        print('\n'.join(records))
except Exception as e:
    # Handle missing records safely depending on output format
    if fmt == 'json':
        print(json.dumps({'domain': domain, 'type': rtype, 'records': [], 'error': str(e)}))
    elif fmt == 'csv':
        print(f'\"{domain}\",\"{rtype}\",\"ERROR: {str(e)}\"')
    else:
        print(f'--- {domain} ({rtype}) ---')
        print(f'Error: {e}')
"
}

# Print headers for structured formats if doing file batch operations
if [[ -n "$INPUT_FILE" ]]; then
    if [[ "$FORMAT" == "csv" ]]; then
        echo '"Domain","RecordType","Data"'
    elif [[ "$FORMAT" == "json" ]]; then
        echo '['
    fi
fi

# Execution loop
if [[ -n "$SINGLE_DOMAIN" ]]; then
    query_dns "$SINGLE_DOMAIN"
elif [[ -n "$INPUT_FILE" ]]; then
    first=true
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Strip whitespaces, carriage returns, and ignore empty lines/comments
        domain=$(echo "$line" | xargs | tr -d '\r')
        [[ -z "$domain" || "$domain" =~ ^# ]] && continue
        
        # Handle trailing commas for valid multi-line JSON structures
        if [[ "$FORMAT" == "json" ]]; then
            if [ "$first" = true ]; then
                first=false
            else
                echo ","
            fi
        fi
        
        query_dns "$domain"
    done < "$INPUT_FILE"
    
    if [[ "$FORMAT" == "json" ]]; then
        echo -e "\n]"
    fi
fi

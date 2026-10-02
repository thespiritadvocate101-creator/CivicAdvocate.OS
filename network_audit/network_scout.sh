#!/usr/bin/env bash

# Terminal Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global Configuration Default
WORDLIST="subdomains_wordlist.txt"

# Core Python Engine
run_py_dns() {
    local domain=$1
    local rtype=$2
    python3 -c "
import dns.resolver
res = dns.resolver.Resolver(configure=False)
res.nameservers = ['8.8.8.8', '1.1.1.1']
res.timeout = 1.5
res.lifetime = 1.5
try:
    print('\n'.join([r.to_text() for r in res.resolve('${domain}', '${rtype}')]))
except:
    pass
"
}

# 1. Multi-Record Scanner Menu Action
menu_multi_record() {
    clear
    echo -e "${CYAN}=== Multi-Record Scanner ===${NC}"
    read -p "Enter Target Domain (e.g., google.com): " domain
    [[ -z "$domain" ]] && return

    echo -e "\n${YELLOW}[*] Querying DNS infrastructure for $domain...${NC}"
    for type in A AAAA MX TXT CNAME NS; do
        echo -e "\n${GREEN}--- $type Records ---${NC}"
        res=$(run_py_dns "$domain" "$type")
        if [[ -n "$res" ]]; then
            echo "$res"
            if [[ "$type" == "TXT" ]]; then
                echo "$res" | grep -q "v=spf1" && echo -e "${YELLOW}[!] Passive Intel: SPF Policy Discovered (Check for vulnerabilities).${NC}"
            fi
        else
            echo "None found."
        fi
    done
    echo ""
    read -p "Press Enter to return to menu..." temp
}

# 2. Subdomain Enumeration & Passive Intelligence Menu Action
menu_subdomain_enum() {
    clear
    echo -e "${CYAN}=== Subdomain Enumeration & Intel Mapping ===${NC}"
    read -p "Enter Base Domain (e.g., github.com): " base_domain
    [[ -z "$base_domain" ]] && return

    if [[ ! -f "$WORDLIST" ]]; then
        echo -e "${RED}[!] Error: Wordlist $WORDLIST missing.${NC}"
        read -p "Press Enter to return..." temp
        return
    fi

    echo -e "\n${YELLOW}[*] Brute-forcing subdomains and profiling network landscape...${NC}"
    echo -e "${BLUE}Subdomain,IP_Address,Status${NC}"
    
    base_ip=$(run_py_dns "$base_domain" "A" | head -n 1)
    if [[ -n "$base_ip" ]]; then
        echo -e "${GREEN}${base_domain},${base_ip},ACTIVE${NC}"
    fi

    while IFS= read -r sub || [[ -n "$sub" ]]; do
        sub=$(echo "$sub" | xargs)
        [[ -z "$sub" || "$sub" =~ ^# ]] && continue
        
        target="${sub}.${base_domain}"
        ip=$(run_py_dns "$target" "A" | head -n 1)
        
        if [[ -n "$ip" ]]; then
            port_status="Closed"
            nc -z -w 1 "$ip" 80 2>/dev/null && port_status="HTTP(80)"
            nc -z -w 1 "$ip" 443 2>/dev/null && port_status="HTTPS(443)"
            echo -e "${GREEN}${target},${ip},${port_status}${NC}"
        fi
    done < "$WORDLIST"
    
    echo ""
    read -p "Scanning complete. Press Enter to return to menu..." temp
}

# 3. Upgraded Batch Exporter Engine Action (With Filtering & IP Sorting)
menu_batch_export() {
    clear
    echo -e "${CYAN}=== Batch Processing & Output Export ===${NC}"
    read -p "Enter path to domain list file: " infile
    if [[ ! -f "$infile" ]]; then
        echo -e "${RED}[!] File not found.${NC}"
        sleep 2; return
    fi
    
    echo -e "Select Format:\n1) CSV Spreadsheet\n2) JSON Document"
    read -p "Choice [1-2]: " fmt_choice
    
    read -p "Enter output filename (e.g. report.csv / report.json): " outfile
    [[ -z "$outfile" ]] && return

    local temp_raw=$(mktemp)
    echo -e "${YELLOW}[*] Validating strings and querying records...${NC}"

    while IFS= read -r line || [[ -n "$line" ]]; do
        domain=$(echo "$line" | xargs | tr -d '\r')
        
        [[ -z "$domain" || "$domain" =~ ^# ]] && continue
        if [[ ! "$domain" =~ ^([a-zA-Z0-9](([a-zA-Z0-9-]){0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$ ]]; then
            echo -e "${RED}[!] Skipping invalid domain string: $domain${NC}"
            continue
        fi

        records=$(run_py_dns "$domain" "A" | xargs)
        
        if [[ -n "$records" ]]; then
            echo "$records|$domain" >> "$temp_raw"
        else
            echo "No-IP|$domain" >> "$temp_raw"
        fi
    done < "$infile"

    if [[ "$fmt_choice" == "1" ]]; then
        echo '"Domain","RecordType","Data"' > "$outfile"
        sort -t'|' -k1 "$temp_raw" | while IFS='|' read -r ips dom; do
            csv_ips=$(echo "$ips" | sed 's/ /, /g')
            echo "\"$dom\",\"A\",\"$csv_ips\"" >> "$outfile"
        done
        echo -e "${GREEN}[+] Validated, sorted by IP, and exported to CSV!${NC}"
    else
        echo "[" > "$outfile"
        local first=true
        sort -t'|' -k1 "$temp_raw" | while IFS='|' read -r ips dom; do
            if [ "$first" = true ]; then first=false; else echo "," >> "$outfile"; fi
            json_ips=$(echo "$ips" | python3 -c "import sys, json; print(json.dumps(sys.stdin.read().strip().split()))")
            echo "  {\"domain\": \"$dom\", \"type\": \"A\", \"records\": $json_ips}" >> "$outfile"
        done
        echo -e "\n]" >> "$outfile"
        echo -e "${GREEN}[+] Validated, sorted by IP, and exported to JSON!${NC}"
    fi

    rm -f "$temp_raw"
    sleep 3
}

# Interactive Dashboard Loop
while true; do
    clear
    echo -e "${BLUE}===============================================${NC}"
    echo -e "${CYAN}      CivicAdvocate.OS Network Recon Dashboard   ${NC}"
    echo -e "${BLUE}===============================================${NC}"
    echo -e "1) Multi-Record Infrastructure Scanner"
    echo -e "2) Subdomain Enumeration & Passive Mapping"
    echo -e "3) Batch Domain Exporter (CSV/JSON)"
    echo -e "4) Exit Console Environment"
    echo -e "${BLUE}===============================================${NC}"
    read -p "Select module option [1-4]: " option

    case $option in
        1) menu_multi_record ;;
        2) menu_subdomain_enum ;;
        3) menu_batch_export ;;
        4) echo -e "${YELLOW}Exiting environment system framework...${NC}"; exit 0 ;;
        *) echo -e "${RED}Invalid directive selections.${NC}"; sleep 1 ;;
    esac
done

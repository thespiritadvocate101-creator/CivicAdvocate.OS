#!/usr/bin/env bash
# CivicAdvocate.OS API Gateway - Bash Socket Handler / Test Runner

# --- 1. Rate Limiting Function ---
check_rate_limit() {
    local client_ip="$1"
    local limit="${2:-5}"      # Low limit for testing
    local window="${3:-60}"     # Window size in seconds
    
    local safe_ip="${client_ip//:/_}"
    local rate_dir="/tmp/api_ratelimit/$safe_ip"
    
    mkdir -p "$rate_dir"
    local current_time
    current_time=$(date +%s)
    
    # Purge timestamps outside the active window
    for req_file in "$rate_dir"/*; do
        if [[ -f "$req_file" ]]; then
            local req_time
            req_time=$(basename "$req_file")
            if (( current_time - req_time > window )); then
                rm -f "$req_file"
            fi
        fi
    done
    
    # Count current active requests in window
    local request_count
    request_count=$(find "$rate_dir" -maxdepth 1 -type f | wc -l)
    
    if (( request_count >= limit )); then
        return 1
    fi
    
    # Record current request timestamp
    touch "$rate_dir/$current_time"
    return 0
}

# --- 2. JWT Verification Function ---
verify_jwt() {
    local token="$1"
    local secret="${JWT_SECRET:-your-secure-secret-key}"
    
    IFS='.' read -r header payload sig <<< "$token"
    if [[ -z "$header" || -z "$payload" || -z "$sig" ]]; then
        echo "{\"error\": \"Invalid token structure\"}" >&2
        return 1
    fi
    
    local padded_payload="$payload"
    while (( ${#padded_payload} % 4 )); do padded_payload+="${padded_payload}="; done
    
    local decoded_payload
    decoded_payload=$(echo "$padded_payload" | tr '_-' '/+' | base64 -d 2>/dev/null)
    if [[ -z "$decoded_payload" ]]; then
        echo "{\"error\": \"Failed to decode payload\"}" >&2
        return 1
    fi
    
    local exp current_time
    exp=$(echo "$decoded_payload" | jq -r '.exp // 0')
    current_time=$(date +%s)
    
    if (( current_time >= exp )); then
        echo "{\"error\": \"Token has expired\"}" >&2
        return 1
    fi
    
    local computed_sig
    computed_sig=$(echo -n "$header.$payload" | openssl dgst -sha256 -hmac "$secret" -binary | base64 | tr '/+' '_-' | tr -d '=')
    
    if [[ "$computed_sig" != "$sig" ]]; then
        echo "{\"error\": \"Invalid signature\"}" >&2
        return 1
    fi
    
    echo "$decoded_payload"
    return 0
}

# --- 3. Request Orchestrator / Test Runner ---
handle_request() {
    local client_ip="$1"
    local auth_header="$2"

    echo "Incoming Request from IP: $client_ip"

    # Step A: Enforce Rate Limit
    if ! check_rate_limit "$client_ip" 5 60; then
        echo "HTTP/1.1 429 Too Many Requests"
        echo "Retry-After: 60"
        echo '{"detail": "Too many requests. Please try again later."}'
        echo "--------------------------------------------------"
        return 1
    fi

    # Step B: Validate Authorization Header
    if [[ ! "$auth_header" =~ ^Bearer[[:space:]]+(.+)$ ]]; then
        echo "HTTP/1.1 401 Unauthorized"
        echo '{"error": "Missing or malformed Authorization header"}'
        echo "--------------------------------------------------"
        return 1
    fi

    local token="${BASH_REMATCH[1]}"
    local user_data
    
    if user_data=$(verify_jwt "$token"); then
        local user_sub
        user_sub=$(echo "$user_data" | jq -r '.sub // "unknown"')
        echo "HTTP/1.1 200 OK"
        echo "Content-Type: application/json"
        echo "{\"status\": \"success\", \"message\": \"Access granted.\", \"user_id\": \"$user_sub\"}"
    else
        echo "HTTP/1.1 401 Unauthorized"
        echo "Content-Type: application/json"
        echo '{"error": "Unauthorized access or invalid token"}'
    fi
    echo "--------------------------------------------------"
}

# --- Execution Test Simulation ---
# Generate a valid test JWT (Expires 1 hour from now)
SECRET="your-secure-secret-key"
HEADER='{"alg":"HS256","typ":"JWT"}'
EXP_TIME=$(( $(date +%s) + 3600 ))
PAYLOAD="{\"sub\":\"system_admin\",\"exp\":$EXP_TIME}"

b64url() { base64 | tr '/+' '_-' | tr -d '=\n'; }

ENC_HEADER=$(echo -n "$HEADER" | b64url)
ENC_PAYLOAD=$(echo -n "$PAYLOAD" | b64url)
SIG=$(echo -n "$ENC_HEADER.$ENC_PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" -binary | b64url)
VALID_TOKEN="$ENC_HEADER.$ENC_PAYLOAD.$SIG"

echo "=== Running Gateway Simulations ==="
# Test 1: Valid Request
handle_request "127.0.0.1" "Bearer $VALID_TOKEN"

# Test 2: Invalid/Tampered Token
handle_request "127.0.0.1" "Bearer eyJhbGciOiJIUzI1NiJ9.invalidpayload.invalidsig"

# Test 3: Rate Limit Stress Test (Hitting 5 more times to trip threshold)
for i in {1..5}; do
    handle_request "192.168.1.100" "Bearer $VALID_TOKEN"
done


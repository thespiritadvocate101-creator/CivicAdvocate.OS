#!/usr/bin/env bash
PORT=8080
SECRET="${JWT_SECRET:-your-secure-secret-key}"

check_rate_limit() {
    local client_ip="$1"
    local key="ratelimit:$client_ip"
    local current_count
    current_count=$(redis-cli INCR "$key" 2>/dev/null)
    [[ -z "$current_count" ]] && return 0
    [[ "$current_count" -eq 1 ]] && redis-cli EXPIRE "$key" 60 >/dev/null 2>&1
    (( current_count > 5 )) && return 1
    return 0
}

verify_jwt() {
    local token="$1"
    IFS='.' read -r header payload sig <<< "$token"
    [[ -z "$header" || -z "$payload" || -z "$sig" ]] && return 1
    local padded_payload="$payload"
    while (( ${#padded_payload} % 4 )); do padded_payload+="${padded_payload}="; done
    local decoded_payload
    decoded_payload=$(echo "$padded_payload" | tr '_-' '/+' | base64 -d 2>/dev/null)
    [[ -z "$decoded_payload" ]] && return 1
    local exp=$(echo "$decoded_payload" | jq -r '.exp // 0')
    (( $(date +%s) >= exp )) && return 1
    local computed_sig
    computed_sig=$(echo -n "$header.$payload" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64 | tr '/+' '_-' | tr -d '=')
    [[ "$computed_sig" != "$sig" ]] && return 1
    echo "$decoded_payload"
    return 0
}

handle_request() {
    local client_ip="127.0.0.1"
    local request_line="$1"
    local auth_header="$2"

    if ! check_rate_limit "$client_ip" 5 60; then
        echo -e "HTTP/1.1 429 Too Many Requests\r"
        echo -e "Retry-After: 60\r"
        echo -e "Content-Type: application/json\r"
        echo -e "Connection: close\r\n\r"
        echo '{"detail": "Too many requests."}'
        return
    fi

    if [[ ! "$auth_header" =~ ^Bearer[[:space:]]+(.+)$ ]]; then
        echo -e "HTTP/1.1 401 Unauthorized\r"
        echo -e "Content-Type: application/json\r"
        echo -e "Connection: close\r\n\r"
        echo '{"error": "Missing or malformed Authorization header"}'
        return
    fi

    local token="${BASH_REMATCH[1]}"
    local user_data
    if user_data=$(verify_jwt "$token"); then
        local user_sub=$(echo "$user_data" | jq -r '.sub // "unknown"')
        echo -e "HTTP/1.1 200 OK\r"
        echo -e "Content-Type: application/json\r"
        echo -e "Connection: close\r\n\r"
        echo "{\"status\": \"success\", \"user_id\": \"$user_sub\"}"
    else
        echo -e "HTTP/1.1 401 Unauthorized\r"
        echo -e "Content-Type: application/json\r"
        echo -e "Connection: close\r\n\r"
        echo '{"error": "Invalid token"}'
    fi
}

echo "Starting pure Bash API server on port $PORT..."
while true; do
    ncat -l -k -p "$PORT" --sh-exec '
        read -r request_line
        auth_header=""
        while read -r header_line; do
            header_line=$(echo "$header_line" | tr -d "\r")
            [[ -z "$header_line" ]] && break
            if [[ "$header_line" =~ ^Authorization:[[:space:]]*(.+) ]]; then
                auth_header="${BASH_REMATCH[1]}"
            fi
        done
        handle_request "$request_line" "$auth_header"
    '
done

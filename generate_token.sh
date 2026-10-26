#!/usr/bin/env bash
SECRET="${JWT_SECRET:-your-secure-secret-key}"
HEADER='{"alg":"HS256","typ":"JWT"}'
EXP_TIME=$(( $(date +%s) + 3600 ))
PAYLOAD="{\"sub\":\"system_admin\",\"exp\":$EXP_TIME}"

b64url() { base64 | tr '/+' '_-' | tr -d '=\n'; }

ENC_HEADER=$(echo -n "$HEADER" | b64url)
ENC_PAYLOAD=$(echo -n "$PAYLOAD" | b64url)
SIG=$(echo -n "$ENC_HEADER.$ENC_PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" -binary | b64url)

echo "$ENC_HEADER.$ENC_PAYLOAD.$SIG"

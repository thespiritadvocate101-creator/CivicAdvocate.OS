#!/usr/bin/env bash
# ==============================================================================
# vault_ccrypt.sh - ccrypt Execution Wrapper for Termux
# ==============================================================================

set -euo pipefail

# Verify system dependency
check_dependencies() {
    if ! command -v ccrypt &> /dev/null; then
        echo "[!] Error: 'ccrypt' utility is not installed in current PATH."
        echo "[*] Run 'pkg install ccrypt' in Termux to install it."
        exit 1
    fi
}

# Encrypt individual target file
encrypt_file() {
    local target="$1"
    if [[ ! -f "$target" ]]; then
        echo "[!] Error: Target file '$target' does not exist."
        return 1
    fi

    if [[ "$target" == *.cpt ]]; then
        echo "[!] Warning: Target file '$target' already appears to be encrypted (.cpt)."
        return 1
    fi

    echo "[*] Encrypting file: $target"
    ccrypt -e "$target"
    echo "[+] Encryption successful: ${target}.cpt created."
}

# Decrypt individual target file
decrypt_file() {
    local target="$1"
    if [[ ! -f "$target" ]]; then
        echo "[!] Error: Target file '$target' does not exist."
        return 1
    fi

    if [[ "$target" != *.cpt ]]; then
        echo "[!] Warning: Target file '$target' does not have a .cpt extension."
        return 1
    fi

    echo "[*] Decrypting file: $target"
    ccrypt -d "$target"
    echo "[+] Decryption successful: Restored unencrypted file."
}

# Batch encrypt files within a directory
batch_encrypt() {
    local target_dir="$1"
    if [[ ! -d "$target_dir" ]]; then
        echo "[!] Error: Directory '$target_dir' does not exist."
        return 1
    fi

    echo "[*] Scanning directory '$target_dir' for unencrypted files..."
    local count=0
    for file in "$target_dir"/*; do
        if [[ -f "$file" && "$file" != *.cpt ]]; then
            echo "[*] Processing: $file"
            ccrypt -e "$file"
            ((count++))
        fi
    done
    echo "[+] Batch operation completed. $count file(s) encrypted."
}

usage() {
    echo "Usage: $0 [mode] [file|directory]"
    echo ""
    echo "Options:"
    echo "  -e, --encrypt <file>       Encrypt a single file into .cpt"
    echo "  -d, --decrypt <file.cpt>   Decrypt a .cpt file back to original"
    echo "  -b, --batch   <dir>        Batch encrypt all unencrypted files in directory"
    exit 1
}

main() {
    check_dependencies

    if [[ $# -lt 2 ]]; then
        usage
    fi

    local mode="$1"
    local target="$2"

    case "$mode" in
        -e|--encrypt)
            encrypt_file "$target"
            ;;
        -d|--decrypt)
            decrypt_file "$target"
            ;;
        -b|--batch)
            batch_encrypt "$target"
            ;;
        *)
            usage
            ;;
    esac
}

main "$@"

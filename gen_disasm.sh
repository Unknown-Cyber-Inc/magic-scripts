#!/usr/bin/env bash
set -euo pipefail

mkdir -p binary/disasm

for f in malware/*; do
  [ -f "$f" ] || continue
  base="$(basename "$f")"

  objdump -h "$f" > "binary/disasm/${base}.headers.txt"
  objdump -d -M intel --wide "$f" > "binary/disasm/${base}.disasm.txt"

  echo "[+] wrote binary/disasm/${base}.{headers,disasm}.txt"
done

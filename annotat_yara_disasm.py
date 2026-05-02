#!/usr/bin/env python3
import argparse
import bisect
import os
import re
from pathlib import Path

SECTION_RE = re.compile(
    r"^\s*\d+\s+(\S+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+"
    r"([0-9a-fA-F]+)\s+([0-9a-fA-F]+)"
)

YARA_FILE_RE = re.compile(r"^\S+\s+(.+)$")
YARA_HIT_RE = re.compile(r"^0x([0-9a-fA-F]+):([^:]+):\s*(.*)$")
DISASM_ADDR_RE = re.compile(r"^\s*([0-9a-fA-F]+):")


def parse_sections(header_file):
    sections = []

    with open(header_file, "r", errors="replace") as f:
        for line in f:
            m = SECTION_RE.match(line)
            if not m:
                continue

            name, size, vma, lma, fileoff = m.groups()
            size = int(size, 16)
            vma = int(vma, 16)
            fileoff = int(fileoff, 16)

            if size == 0:
                continue

            sections.append({
                "name": name,
                "size": size,
                "vma": vma,
                "fileoff": fileoff,
                "end_fileoff": fileoff + size,
            })

    return sections


def fileoff_to_vma(fileoff, sections):
    for s in sections:
        if s["fileoff"] <= fileoff < s["end_fileoff"]:
            return s["vma"] + (fileoff - s["fileoff"]), s["name"]

    return None, None


def parse_yara_hits(yara_file):
    hits = {}
    current_file = None

    with open(yara_file, "r", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")

            hm = YARA_HIT_RE.match(line)
            if hm and current_file:
                off = int(hm.group(1), 16)
                rule_string = hm.group(2)
                bytestr = hm.group(3)
                base = os.path.basename(current_file)
                hits.setdefault(base, []).append((off, rule_string, bytestr))
                continue

            fm = YARA_FILE_RE.match(line)
            if fm and not line.startswith("0x"):
                current_file = fm.group(1).strip()

    return hits


def disasm_addresses(disasm_file):
    addrs = []
    lines = []

    with open(disasm_file, "r", errors="replace") as f:
        for idx, line in enumerate(f):
            lines.append(line)
            m = DISASM_ADDR_RE.match(line)
            if m:
                addrs.append((int(m.group(1), 16), idx))

    return lines, addrs


def nearest_instruction_index(vma, addrs):
    only_addrs = [a for a, _ in addrs]
    pos = bisect.bisect_left(only_addrs, vma)

    candidates = []
    if pos < len(addrs):
        candidates.append(addrs[pos])
    if pos > 0:
        candidates.append(addrs[pos - 1])

    if not candidates:
        return None, None

    best_addr, best_idx = min(candidates, key=lambda x: abs(x[0] - vma))
    return best_idx, best_addr


def annotate_one(base, hits, disasm_dir, out_dir):
    header_file = disasm_dir / f"{base}.headers.txt"
    disasm_file = disasm_dir / f"{base}.disasm.txt"
    out_file = out_dir / f"{base}.annotated.disasm.txt"

    if not header_file.exists() or not disasm_file.exists():
        print(f"[!] missing disassembly/header for {base}")
        return

    sections = parse_sections(header_file)
    lines, addrs = disasm_addresses(disasm_file)

    inserts = {}

    for fileoff, rule_string, bytestr in hits:
        vma, secname = fileoff_to_vma(fileoff, sections)

        if vma is None:
            comment = (
                f";; YARA HIT {rule_string} fileoff=0x{fileoff:x} "
                f"bytes={bytestr} -- no containing section found\n"
            )
            inserts.setdefault(0, []).append(comment)
            continue

        idx, inst_addr = nearest_instruction_index(vma, addrs)
        delta = None if inst_addr is None else vma - inst_addr

        comment = (
            f";; YARA HIT {rule_string} fileoff=0x{fileoff:x} "
            f"mapped_addr=0x{vma:x} section={secname} "
            f"nearest_inst=0x{inst_addr:x} delta={delta:+d} "
            f"bytes={bytestr}\n"
        )

        if idx is None:
            inserts.setdefault(0, []).append(comment)
        else:
            inserts.setdefault(idx, []).append(comment)

    with open(out_file, "w") as out:
        for i, line in enumerate(lines):
            if i in inserts:
                for comment in inserts[i]:
                    out.write(comment)
            out.write(line)

    print(f"[+] wrote {out_file}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("yara_output", help="YARA output generated with -s")
    ap.add_argument("--disasm-dir", default="binary/disasm")
    ap.add_argument("--out-dir", default="binary/annotated")
    args = ap.parse_args()

    disasm_dir = Path(args.disasm_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    yara_hits = parse_yara_hits(args.yara_output)

    for base, hits in yara_hits.items():
        annotate_one(base, hits, disasm_dir, out_dir)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Replicate projects by calling set-tags.sh for each hash in each project."
    )
    parser.add_argument("file", help="Path to JSON file containing the project list")
    args = parser.parse_args()

    json_path = Path(args.file)
    if not json_path.is_file():
        print(f"Error: file not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    projects = data.get("projects", [])
    if not projects:
        print("No projects found in the input file.")
        sys.exit(0)

    script = "./set-tags.sh"

    for i, project in enumerate(projects, start=1):
        name = project["name"]
        hashes = project.get("hashes", [])
        print(f"\n[{i}/{len(projects)}] Starting project: {name}  ({len(hashes)} hashes)")

        for j, filehash in enumerate(hashes, start=1):
            print(f"  [{j}/{len(hashes)}] {name} <- {filehash}")
            result = subprocess.run(
                [script, name, filehash],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"    WARNING: set-tags.sh exited with code {result.returncode}", file=sys.stderr)
                if result.stderr.strip():
                    print(f"    stderr: {result.stderr.strip()}", file=sys.stderr)

    print(f"\nDone. Processed {len(projects)} projects.")


if __name__ == "__main__":
    main()

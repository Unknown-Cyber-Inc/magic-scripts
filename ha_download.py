#!/usr/bin/env python3
"""Download malware samples from Hybrid Analysis."""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from gzip import GzipFile
from io import BytesIO
from pathlib import Path

import requests

log = logging.getLogger(__name__)

HA_URL = "https://hybrid-analysis.com/api/v2"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
DEFAULT_THROTTLE_WAIT = 60


def is_sha256(h: str) -> bool:
    return bool(SHA256_RE.match(h))


def ha_get(url: str, key: str, **kwargs) -> requests.Response:
    """GET with automatic throttle-retry on 429."""
    while True:
        res = requests.get(url, headers={"api-key": key}, **kwargs)
        if res.status_code == 429:
            wait = int(res.headers.get("Retry-After", DEFAULT_THROTTLE_WAIT))
            log.warning("Rate-limited – retrying in %ds", wait)
            time.sleep(wait)
            continue
        return res


# ---------------------------------------------------------------------------
# HA API primitives
# ---------------------------------------------------------------------------

def get_remaining_quota(key: str) -> dict:
    res = ha_get(f"{HA_URL}/key/current", key)
    res.raise_for_status()
    limits = json.loads(res.headers["api-limits"])
    quotas = json.loads(res.headers["sample-download-limits"])
    return {
        "api": {
            "minute": {
                "allowed": limits["limits"]["minute"],
                "used": limits["used"]["minute"],
            },
            "hour": {
                "allowed": limits["limits"]["hour"],
                "used": limits["used"]["hour"],
            },
        },
        "download": {
            "day": {
                "allowed": quotas["limits"]["day"],
                "used": quotas["used"]["day"],
            },
        },
    }


def fetch_sha256(hash_val: str, key: str) -> str | None:
    res = ha_get(f"{HA_URL}/search/hash", key, params={"hash": hash_val})
    if res.status_code == 404:
        return None
    res.raise_for_status()
    sha_list = res.json().get("sha256s")
    if not sha_list:
        return None
    return sha_list[0]


def fetch_report(hash_val: str, key: str) -> dict:
    res = ha_get(f"{HA_URL}/overview/{hash_val}", key)
    res.raise_for_status()
    return res.json()


def fetch_file(hash_val: str, key: str) -> BytesIO:
    res = ha_get(f"{HA_URL}/overview/{hash_val}/sample", key)
    res.raise_for_status()
    return BytesIO(GzipFile(fileobj=BytesIO(res.content), mode="rb").read())


# ---------------------------------------------------------------------------
# Local sha256 map (avoids repeat lookups)
# ---------------------------------------------------------------------------

def load_sha256_map(map_path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if map_path.exists():
        with open(map_path, newline="") as f:
            for row in csv.reader(f):
                if len(row) >= 2:
                    mapping[row[0].strip().lower()] = row[1].strip().lower()
    return mapping


def append_sha256_map(map_path: Path, input_hash: str, sha256: str) -> None:
    with open(map_path, "a", newline="") as f:
        csv.writer(f).writerow([input_hash, sha256])


# ---------------------------------------------------------------------------
# Misses log – hashes HA couldn't resolve or files HA didn't have
#   columns: hash, sha256, reason
#   reason: no_sha256_mapping | file_not_found
# ---------------------------------------------------------------------------

MISS_NO_SHA256 = "no_sha256_mapping"
MISS_NOT_FOUND = "file_not_found"


def load_misses(miss_path: Path) -> dict[str, str]:
    """Return {lowercase_hash: reason} for every recorded miss."""
    misses: dict[str, str] = {}
    if miss_path.exists():
        with open(miss_path, newline="") as f:
            for row in csv.reader(f):
                if len(row) >= 3:
                    misses[row[0].strip().lower()] = row[2].strip()
    return misses


def append_miss(miss_path: Path, input_hash: str, sha256: str, reason: str) -> None:
    with open(miss_path, "a", newline="") as f:
        csv.writer(f).writerow([input_hash, sha256, reason])


# ---------------------------------------------------------------------------
# Download logic
# ---------------------------------------------------------------------------

def already_downloaded(outdir: Path, sha256: str) -> bool:
    return any(outdir.glob(f"{sha256}*"))


def download_sample(
    hash_val: str,
    key: str,
    outdir: Path,
    password: str | None = None,
    skip_download: bool = False,
    *,
    map_path: Path,
    miss_path: Path,
    sha256_map: dict[str, str],
    misses: dict[str, str],
) -> bool:
    """Download a single sample.  Mutates sha256_map/misses in-place."""
    input_lower = hash_val.lower()

    if input_lower in misses:
        log.debug("Previously missed %s (%s) – skipping", hash_val, misses[input_lower])
        return False

    if is_sha256(hash_val):
        sha256 = input_lower
    elif input_lower in sha256_map:
        sha256 = sha256_map[input_lower]
        log.debug("Resolved %s -> %s (cached)", hash_val, sha256)
    else:
        log.info("Looking up sha256 for %s …", hash_val)
        sha256 = fetch_sha256(hash_val, key)
        if sha256 is None:
            log.error("HA has no record for %s", hash_val)
            append_miss(miss_path, input_lower, "", MISS_NO_SHA256)
            misses[input_lower] = MISS_NO_SHA256
            return False
        sha256 = sha256.lower()
        append_sha256_map(map_path, input_lower, sha256)
        sha256_map[input_lower] = sha256
        log.info("Resolved %s -> %s", hash_val, sha256)

    if sha256 in misses:
        log.debug("Previously missed %s (%s) – skipping", sha256, misses[sha256])
        return False

    if already_downloaded(outdir, sha256):
        log.debug("Already have %s – skipping", sha256)
        return True

    if skip_download:
        log.debug("Resolved sha256 %s – skipping download", sha256)
        return True

    log.info("Downloading %s …", sha256)
    try:
        data = fetch_file(sha256, key)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            log.error("File not available on HA for %s", sha256)
            append_miss(miss_path, input_lower, sha256, MISS_NOT_FOUND)
            misses[input_lower] = MISS_NOT_FOUND
            misses[sha256] = MISS_NOT_FOUND
            return False
        raise

    if password:
        try:
            import pyzipper
        except ImportError:
            log.error("pyzipper is required for password-protected zips: pip install pyzipper")
            sys.exit(1)
        dest = outdir / f"{sha256}.zip"
        with pyzipper.AESZipFile(
            dest, "w",
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zf:
            zf.setpassword(password.encode())
            zf.writestr(f"{sha256}-sample-bin", data.read())
        log.debug("Saved %s", dest)
    else:
        dest = outdir / f"{sha256}-sample-bin"
        dest.write_bytes(data.read())
        log.debug("Saved %s", dest)

    return True


def process_hashes(
    hashes: list[str],
    key: str,
    outdir: Path,
    password: str | None = None,
    skip_download: bool = False,
) -> int:
    """Process a list of hashes. Returns count of failures."""
    map_path = outdir / "sha256-map.csv"
    miss_path = outdir / "ha-misses.csv"
    sha256_map = load_sha256_map(map_path)
    misses = load_misses(miss_path)

    failures = 0
    for i, h in enumerate(hashes, 1):
        log.debug("[%d/%d] %s", i, len(hashes), h)
        ok = download_sample(
            h, key, outdir, password, skip_download,
            map_path=map_path, miss_path=miss_path,
            sha256_map=sha256_map, misses=misses,
        )
        if not ok:
            failures += 1
    return failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def read_hash_file(path: str) -> list[str]:
    """Read one hash per line, stripping blanks and # comments."""
    hashes: list[str] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                hashes.append(line.split()[0])
    return hashes


def main():
    parser = argparse.ArgumentParser(
        description="Download malware samples from Hybrid Analysis",
    )
    parser.add_argument(
        "hash", nargs="?", default=None,
        help="Single file hash (MD5, SHA1, or SHA256)",
    )
    parser.add_argument(
        "-f", "--file",
        help="File containing one hash per line",
    )
    parser.add_argument(
        "-o", "--outdir", default="./malware",
        help="Output directory (default: ./malware)",
    )
    parser.add_argument(
        "-s", "--skip-download", default=False,
        action="store_true",
        help="Do not download file, just update sha256 hashmap",
    )
    parser.add_argument(
        "-k", "--key", default=os.environ.get("HA_API_KEY"),
        help="HA API key (default: $HA_API_KEY env var)",
    )
    parser.add_argument(
        "-p", "--password",
        help="Save sample inside an AES-encrypted zip with this password",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Verbose output (DEBUG level); default is INFO and above",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not args.hash and not args.file:
        parser.error("provide a hash or -f FILE")
    if not args.key:
        log.error("API key required – pass -k KEY or set HA_API_KEY")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    hashes: list[str] = []
    if args.file:
        hashes.extend(read_hash_file(args.file))
    if args.hash:
        hashes.append(args.hash)

    if not hashes:
        log.error("No hashes to process")
        sys.exit(1)

    if args.skip_download:
        log.warning("Skipping file downloads; will only update sha256 map")

    failures = process_hashes(hashes, args.key, outdir, args.password, args.skip_download)
    if failures:
        log.warning("%d of %d hashes failed", failures, len(hashes))
    sys.exit(1 if failures == len(hashes) else 0)


if __name__ == "__main__":
    main()

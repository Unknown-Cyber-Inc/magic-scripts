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
# Download logic
# ---------------------------------------------------------------------------

def already_downloaded(outdir: Path, sha256: str) -> bool:
    return any(outdir.glob(f"{sha256}*"))


def download_sample(
    hash_val: str,
    key: str,
    outdir: Path,
    password: str | None = None,
) -> bool:
    map_path = outdir / "sha256-map.csv"
    sha256_map = load_sha256_map(map_path)
    input_lower = hash_val.lower()

    if is_sha256(hash_val):
        sha256 = input_lower
    elif input_lower in sha256_map:
        sha256 = sha256_map[input_lower]
        log.info("Resolved %s -> %s (cached)", hash_val, sha256)
    else:
        log.info("Looking up sha256 for %s …", hash_val)
        sha256 = fetch_sha256(hash_val, key)
        if sha256 is None:
            log.error("HA has no record for %s", hash_val)
            return False
        sha256 = sha256.lower()
        append_sha256_map(map_path, input_lower, sha256)
        log.info("Resolved %s -> %s", hash_val, sha256)

    if already_downloaded(outdir, sha256):
        log.info("Already have %s – skipping", sha256)
        return True

    log.info("Downloading %s …", sha256)
    try:
        data = fetch_file(sha256, key)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            log.error("File not available on HA for %s", sha256)
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
        log.info("Saved %s", dest)
    else:
        dest = outdir / f"{sha256}-sample-bin"
        dest.write_bytes(data.read())
        log.info("Saved %s", dest)

    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Download malware samples from Hybrid Analysis",
    )
    parser.add_argument("hash", help="File hash (MD5, SHA1, or SHA256)")
    parser.add_argument(
        "-o", "--outdir", default="./malware",
        help="Output directory (default: ./malware)",
    )
    parser.add_argument(
        "-k", "--key", default=os.environ.get("HA_API_KEY"),
        help="HA API key (default: $HA_API_KEY env var)",
    )
    parser.add_argument(
        "-p", "--password",
        help="Save sample inside an AES-encrypted zip with this password",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not args.key:
        log.error("API key required – pass -k KEY or set HA_API_KEY")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    ok = download_sample(args.hash, args.key, outdir, args.password)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

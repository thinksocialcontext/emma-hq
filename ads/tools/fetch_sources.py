#!/usr/bin/env python3
"""Download the public source images the ads are built from.

Reads a list of public URLs (default ads/assets/source-urls.tsv), one per line:

  file<TAB>what it is<TAB>https://public/url

and saves each file to ads/assets/photos/ (or ads/assets/logo/ for .svg files).
It writes ads/assets/photos/sources.csv (file, product, url, fetched) so every
still's record can name the public URL of every photo it uses.

  python3 ads/tools/fetch_sources.py                  fetch what is missing
  python3 ads/tools/fetch_sources.py my-list.tsv      another list
  python3 ads/tools/fetch_sources.py --force          fetch everything again
  python3 ads/tools/fetch_sources.py --dry-run        show what it would do

The images stay on this computer (git ignores assets/photos and assets/logo).
Only the URL list is committed. Read only on the web: plain HTTPS GETs, nothing sent.
"""

from __future__ import annotations

import csv
import datetime as dt
import sys
import time
import urllib.request
from pathlib import Path

ADS = Path(__file__).resolve().parent.parent
DEFAULT_LIST = ADS / "assets" / "source-urls.tsv"
PHOTOS = ADS / "assets" / "photos"
LOGO = ADS / "assets" / "logo"
UA = "Mozilla/5.0 (EmmaHQ fetch_sources; public product images)"


def read_list(path: Path) -> list[tuple[str, str, str]]:
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) == 2:
            parts = [parts[0], "", parts[1]]
        if len(parts) != 3:
            sys.exit(f"{path}:{n}: expected file<TAB>what it is<TAB>url")
        name, what, url = (p.strip() for p in parts)
        if "/" in name or name.startswith("."):
            sys.exit(f"{path}:{n}: file must be a plain file name, got {name!r}")
        if not url.startswith("https://"):
            sys.exit(f"{path}:{n}: only https URLs are fetched, got {url!r}")
        rows.append((name, what, url))
    return rows


def dest_for(name: str) -> Path:
    return (LOGO if name.lower().endswith(".svg") else PHOTOS) / name


def fetch(url: str, dest: Path, tries: int = 3) -> int:
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if not data:
                raise ValueError("empty response")
            tmp = dest.with_suffix(dest.suffix + ".part")
            tmp.write_bytes(data)
            tmp.replace(dest)
            return len(data)
        except Exception as e:  # network errors are retried, then reported
            last = e
            time.sleep(1 + attempt)
    raise RuntimeError(f"could not fetch {url}: {last}")


def load_csv(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        return {r["file"]: r for r in csv.DictReader(fh)}


def main(argv: list[str]) -> int:
    force, dry = "--force" in argv, "--dry-run" in argv
    args = [a for a in argv if not a.startswith("--")]
    lst = Path(args[0]) if args else DEFAULT_LIST
    if not lst.exists():
        sys.exit(f"no URL list at {lst}")
    rows = read_list(lst)
    PHOTOS.mkdir(parents=True, exist_ok=True)
    LOGO.mkdir(parents=True, exist_ok=True)
    csv_path = PHOTOS / "sources.csv"
    known = load_csv(csv_path)
    today = dt.date.today().isoformat()
    failed = 0
    for name, what, url in rows:
        dest = dest_for(name)
        rel = str(dest.relative_to(ADS))
        if dest.exists() and not force and known.get(rel, {}).get("url") == url:
            print(f"have    {rel}")
            continue
        if dry:
            print(f"would   {rel}  <-  {url}")
            continue
        try:
            n = fetch(url, dest)
            print(f"fetched {rel}  ({n // 1024} KB)")
            known[rel] = {"file": rel, "product": what, "url": url, "fetched": today}
        except RuntimeError as e:
            print(f"FAILED  {rel}: {e}", file=sys.stderr)
            failed += 1
            continue
        known.setdefault(rel, {"file": rel, "product": what, "url": url, "fetched": today})
    for name, what, url in rows:  # keep the record complete for files that were already here
        rel = str(dest_for(name).relative_to(ADS))
        if dest_for(name).exists():
            known.setdefault(rel, {"file": rel, "product": what, "url": url, "fetched": today})
            known[rel]["product"] = known[rel].get("product") or what
    if not dry:
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=["file", "product", "url", "fetched"])
            wr.writeheader()
            for rel in sorted(known):
                wr.writerow({k: known[rel].get(k, "") for k in ("file", "product", "url", "fetched")})
        print(f"record: {csv_path.relative_to(ADS.parent)}")
    if failed:
        print(f"{failed} file(s) failed. Check the URLs, then run again.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

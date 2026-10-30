#!/usr/bin/env python3
"""Emma HQ dashboard. A few pages, one command, Python standard library only.

  python3 scripts/dashboard.py            then open http://localhost:8765
  python3 scripts/dashboard.py --once     print the page data as JSON and exit

Pages:
  /          Overview: what is waiting on the owner, the agents, ads, store sales, the ledger
  /launch    Weekly launch: countdown, recommended stills, what is winning, the short F.O.C.U.S. bucket
  /tracker   Ads tracker: every ad that spent in 30 days, best to worst, with kill switch flags
  /focus     F.O.C.U.S. coverage: live and tested ads per bucket, the gap highlighted
  /batches   Batch gallery: each weekly batch with its stills, copy, critic result and variety score
  /memory    Memory: every memory file, click to read (read only)

The numbers come from JSON files the agents refresh in data/. Until those exist it shows
the sample files in data/examples/ and labels them SAMPLE.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import mimetypes
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("HQ_DATA_DIR") or ROOT / "data")
APPROVALS = Path(os.environ.get("HQ_APPROVALS_DIR") or ROOT / "approvals")
MEMORY = Path(os.environ.get("HQ_MEMORY_DIR") or ROOT / "memory")
MEMORY_SEED = Path(os.environ.get("HQ_MEMORY_SEED_DIR") or ROOT / "memory-seed")
BATCHES = Path(os.environ.get("HQ_BATCHES_DIR") or ROOT / "ads" / "batches")

FOCUS = {"F": "Frustration", "O": "Outcome", "C": "Constraint", "U": "Unspoken cost", "S": "Skepticism"}
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
LAUNCH_DEFAULT = {"day": "Wednesday", "time": "10:00", "timezone": "America/Chicago"}
SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.\-]{0,95}")
IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


# ---------------------------------------------------------------- data in

def load_data(name: str) -> dict[str, Any]:
    live, sample = DATA / f"{name}.json", DATA / "examples" / f"{name}.json"
    for path, is_sample in ((live, False), (sample, True)):
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                data["_sample"] = is_sample
                return data
            except json.JSONDecodeError as error:
                return {"_error": f"{path.name}: {error}", "_sample": is_sample}
    return {"_missing": True, "_sample": True}


def run_json(cmd: list[str], timeout: float = 8) -> Any:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
        return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else None
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def agents() -> list[dict[str, str]]:
    result = run_json([str(ROOT / "scripts" / "hq"), "list", "--json"])
    return result if isinstance(result, list) else []


def ledger() -> list[dict[str, Any]]:
    result = run_json([sys.executable, str(ROOT / "scripts" / "ledger"), "recent", "--limit", "12", "--json"])
    return result if isinstance(result, list) else []


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    return fields


def approvals() -> list[dict[str, str]]:
    items = []
    for path in sorted(APPROVALS.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        meta = frontmatter(path.read_text(encoding="utf-8"))
        if meta.get("status", "waiting") == "waiting":
            items.append({"file": f"approvals/{path.name}", "title": meta.get("title", path.stem),
                          "from": meta.get("from", ""), "kind": meta.get("kind", ""),
                          "asked": meta.get("asked", "")})
    return items


def num(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


# ---------------------------------------------------------------- the money rules

def kpi_numbers(kpi: dict[str, Any]) -> dict[str, Any]:
    """Break even and target numbers from data/kpi.json.

    break even CPA  = average order value minus cost per order (what one sale can pay for ads)
    break even ROAS = average order value / break even CPA
    target ROAS     = break even ROAS x uplift (1.25, so 25% better)
    target CPA      = break even CPA / uplift
    kill spend      = 10 x target CPA (with 7 days live, the kill switch)
    """
    out: dict[str, Any] = {"breakeven_roas": None, "target_roas": None, "breakeven_cpa": None,
                           "target_cpa": None, "kill_spend": None}
    aov = num(kpi.get("average_order_value"))
    costs = [num(kpi.get(k)) for k in ("product_cost_per_order", "shipping_cost_per_order", "fees_per_order")]
    uplift = num(kpi.get("target_uplift")) or 1.25
    if aov is None or aov <= 0 or any(c is None for c in costs):
        return out
    margin = aov - sum(c for c in costs if c is not None)
    if margin <= 0:
        return out
    be_roas = aov / margin
    target_cpa = margin / uplift
    out.update(breakeven_roas=round(be_roas, 2), target_roas=round(be_roas * uplift, 2),
               breakeven_cpa=round(margin, 2), target_cpa=round(target_cpa, 2),
               kill_spend=round(10 * target_cpa, 2))
    return out


def breakeven_roas(kpi: dict[str, Any]) -> float | None:
    """Break even ROAS = average order value / (average order value minus cost per order)."""
    return kpi_numbers(kpi)["breakeven_roas"]


def ad_rows(ads: dict[str, Any], k: dict[str, Any]) -> list[dict[str, Any]]:
    """Every ad that spent in the window, with ROAS, CPA, share, verdict and kill switch, best to worst."""
    rows = []
    for raw in ads.get("ads", []) if isinstance(ads.get("ads"), list) else []:
        if not isinstance(raw, dict):
            continue
        spend = num(raw.get("spend", raw.get("spend_7d"))) or 0.0
        if spend <= 0:
            continue
        revenue = num(raw.get("revenue")) or 0.0
        purchases = num(raw.get("purchases")) or 0.0
        roas = revenue / spend if revenue else (num(raw.get("roas", raw.get("roas_7d"))) or 0.0)
        focus = str(raw.get("focus") or "").strip().upper()[:1]
        rows.append({
            "id": str(raw.get("id") or raw.get("name") or ""), "name": str(raw.get("name") or "unnamed ad"),
            "focus": focus if focus in FOCUS else "", "batch": str(raw.get("batch") or ""),
            "format": str(raw.get("format") or ""), "status": str(raw.get("status") or "").lower(),
            "spend": spend, "purchases": purchases, "revenue": revenue, "roas": roas,
            "cpa": spend / purchases if purchases else None, "ctr": num(raw.get("ctr")),
            "days_live": num(raw.get("days_live")),
        })
    total = sum(r["spend"] for r in rows) or 1.0
    for r in rows:
        r["share"] = r["spend"] / total
        r["verdict"] = verdict(r, k)
        r["kill"] = kill_switch(r, k)
    rows.sort(key=lambda r: (-r["roas"], -r["spend"]))
    return rows


def verdict(row: dict[str, Any], k: dict[str, Any]) -> str:
    if row["status"] and row["status"] != "active":
        return "Paused"
    target = k.get("target_roas")
    if target and row["share"] >= 0.03 and row["roas"] >= target:
        return "Winner"
    return "Testing"


def kill_switch(row: dict[str, Any], k: dict[str, Any]) -> str:
    """The kill switch: 10x target CPA spent, 7 days live, and still under break even. Only ever a proposal."""
    if row["status"] and row["status"] != "active":
        return ""
    be, kill = k.get("breakeven_roas"), k.get("kill_spend")
    if be is None or kill is None:
        return "Set data/kpi.json"
    if row["days_live"] is None:
        return "Days live unknown"
    if row["days_live"] < 7:
        return "Too early"
    if row["spend"] < kill:
        return "Under kill threshold"
    if row["roas"] < be:
        return "Kill candidate"
    return "Above break even"


def focus_coverage(rows: list[dict[str, Any]], drafted: dict[str, int]) -> dict[str, Any]:
    buckets = {}
    live_total = sum(r["spend"] for r in rows if r["status"] == "active")
    for letter, name in FOCUS.items():
        mine = [r for r in rows if r["focus"] == letter]
        live = [r for r in mine if r["status"] == "active"]
        spend = sum(r["spend"] for r in live)
        revenue = sum(r["revenue"] for r in live)
        buckets[letter] = {"letter": letter, "name": name, "live": len(live), "tested": len(mine),
                           "live_spend": spend, "share": spend / live_total if live_total else 0.0,
                           "roas": revenue / spend if spend else None, "drafted": drafted.get(letter, 0)}
    ordered = sorted(buckets.values(), key=lambda b: (b["live_spend"], b["live"], b["tested"]))
    untagged = sum(1 for r in rows if not r["focus"])
    return {"buckets": buckets, "short": ordered[0]["letter"], "untagged": untagged}


def batch_size(daily: float, video_share: float) -> dict[str, Any]:
    """How many new ads this week, from daily spend: under $300 a day is 3 to 5, under $2000 is 5 to 10."""
    if daily < 300:
        tier, low, high = 1, 3, 5
    elif daily < 2000:
        tier, low, high = 2, 5, 10
    else:
        tier, low, high = 3, 10, 20
    total = max(low, min(high, round(daily / 100)))
    videos = max(0, min(total - 1, round(total * video_share))) if video_share > 0 else 0
    return {"tier": tier, "range": f"{low} to {high}", "total": total, "videos": videos, "stills": total - videos}


# ---------------------------------------------------------------- launch time

def launch_settings(kpi: dict[str, Any]) -> dict[str, str]:
    launch = kpi.get("launch") if isinstance(kpi.get("launch"), dict) else {}
    return {key: str(launch.get(key) or default) for key, default in LAUNCH_DEFAULT.items()}


def next_launch(now: datetime, settings: dict[str, str]) -> tuple[datetime, str]:
    """The next launch moment after now, in the owner's time zone. Returns (moment, zone note)."""
    note = ""
    try:
        from zoneinfo import ZoneInfo
        tz: Any = ZoneInfo(settings["timezone"])
    except Exception:  # unknown zone or no time zone database
        tz, note = timezone.utc, f"Time zone {settings['timezone']} not found, so this uses UTC."
    day = settings["day"].strip().lower()
    weekday = WEEKDAYS.index(day) if day in WEEKDAYS else 2
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", settings["time"].strip())
    hour, minute = (int(match.group(1)) % 24, int(match.group(2)) % 60) if match else (10, 0)
    local = now.astimezone(tz)
    for add in range(0, 8):
        d = (local + timedelta(days=add)).date()
        if d.weekday() != weekday:
            continue
        moment = datetime(d.year, d.month, d.day, hour, minute, tzinfo=tz)
        if moment > now:
            return moment, note
    return local + timedelta(days=7), note


def until(delta: timedelta) -> str:
    seconds = max(0, int(delta.total_seconds()))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    return f"{days}d {hours}h {seconds // 60}m"


# ---------------------------------------------------------------- batches

def is_batch(path: Path) -> bool:
    return path.is_dir() and bool(SAFE_NAME.fullmatch(path.name)) and \
        ((path / "copy.json").exists() or (path / "final").is_dir())


def batch_root() -> tuple[Path, bool]:
    """ads/batches when it holds a real batch, else the sample batch in data/examples/batches."""
    if BATCHES.is_dir() and any(is_batch(p) for p in BATCHES.iterdir()):
        return BATCHES, False
    return DATA / "examples" / "batches", True


def parse_critic(text: str, ids: list[str]) -> dict[str, Any]:
    per: dict[str, str] = {}
    for line in text.splitlines():
        for ad_id in ids:
            if ad_id in per or not re.search(rf"(?<![A-Za-z0-9_]){re.escape(ad_id)}(?![A-Za-z0-9_])", line):
                continue
            found = re.search(r"\b(pass(?:ed|es)?|fail(?:ed|s)?)\b", line, re.I)
            if found:
                per[ad_id] = "pass" if found.group(1).lower().startswith("pass") else "fail"
    fails = [i for i in ids if per.get(i) == "fail"]
    if not text.strip():
        summary = "not checked"
    elif fails:
        summary = f"{len(fails)} failed"
    elif ids and all(per.get(i) == "pass" for i in ids):
        summary = "passed"
    else:
        summary = "partly checked"
    return {"per_ad": per, "summary": summary}


def parse_diversity(text: str) -> float | None:
    match = re.search(r"overall[^0-9\n]{0,60}(\d+(?:\.\d+)?)\s*(?:/|out of)\s*10", text, re.I)
    return float(match.group(1)) if match else None


def batches() -> dict[str, Any]:
    root, is_sample = batch_root()
    folders = sorted((p for p in root.iterdir() if is_batch(p)), key=lambda p: p.name, reverse=True) \
        if root.is_dir() else []
    items = []
    for path in folders:
        try:
            spec = json.loads(read_text(path / "copy.json") or "{}")
        except json.JSONDecodeError:
            spec = {}
        ads = [a for a in spec.get("ads", []) if isinstance(a, dict) and a.get("id")] if isinstance(spec, dict) else []
        by_id = {str(a["id"]): a for a in ads}
        final = path / "final"
        stills = sorted(p.name for p in final.iterdir()
                        if p.suffix.lower() in IMAGE_TYPES and SAFE_NAME.fullmatch(p.name)
                        and p.resolve().is_relative_to(root.resolve())) if final.is_dir() else []
        ids = list(by_id) or [Path(s).stem for s in stills]
        critic = parse_critic(read_text(path / "critic.md"), ids)
        items.append({
            "name": path.name, "focus": str(spec.get("focus") or "") if isinstance(spec, dict) else "",
            "stills": [{"file": s, "id": Path(s).stem, "ad": by_id.get(Path(s).stem, {}),
                        "critic": critic["per_ad"].get(Path(s).stem, "")} for s in stills],
            "ads": ads, "critic": critic["summary"], "diversity": parse_diversity(read_text(path / "diversity.md")),
            "sheet": (path / "sheet.jpg").is_file(),
        })
    return {"root": str(root.relative_to(ROOT)) if root.is_relative_to(ROOT) else root.name,
            "sample": is_sample, "items": items}


def batch_file(batch: str, name: str) -> Path | None:
    """Resolve an image inside a batch folder. Anything outside the batch root, or not an image, is refused."""
    if not (SAFE_NAME.fullmatch(batch) and SAFE_NAME.fullmatch(name)) or ".." in batch or ".." in name:
        return None
    if Path(name).suffix.lower() not in IMAGE_TYPES:
        return None
    root = batch_root()[0].resolve()
    candidates = [root / batch / "final" / name] + ([root / batch / name] if name == "sheet.jpg" else [])
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.is_file() and resolved.is_relative_to(root):
            return resolved
    return None


# ---------------------------------------------------------------- memory

def memory_dir() -> tuple[Path, bool]:
    if MEMORY.is_dir() and any(MEMORY.glob("*.md")):
        return MEMORY, False
    return MEMORY_SEED, True


def memories() -> dict[str, Any]:
    root, starter = memory_dir()
    items = []
    for path in sorted(root.glob("*.md")) if root.is_dir() else []:
        if path.name == "MEMORY.md" or not SAFE_NAME.fullmatch(path.name):
            continue
        meta = frontmatter(read_text(path))
        items.append({"file": path.name, "name": meta.get("name", path.stem),
                      "description": meta.get("description", ""), "type": meta.get("type", "")})
    return {"starter": starter, "items": items}


def memory_file(name: str) -> tuple[str, str] | None:
    if not SAFE_NAME.fullmatch(name) or ".." in name or not name.endswith(".md"):
        return None
    root = memory_dir()[0]
    try:
        resolved = (root / name).resolve()
    except OSError:
        return None
    if not resolved.is_file() or not resolved.is_relative_to(root.resolve()):
        return None
    return name, read_text(resolved)


# ---------------------------------------------------------------- state

def state(now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    ads, shop, kpi = load_data("ads"), load_data("shopify"), load_data("kpi")
    k = kpi_numbers(kpi)
    rows = ad_rows(ads, k)
    gallery = batches()
    launched = {r["batch"] for r in rows if r["batch"]}
    upcoming = next((b for b in gallery["items"] if b["name"] not in launched), None)
    drafted: dict[str, int] = {}
    for ad in (upcoming or {}).get("ads", []):
        letter = str(ad.get("focus") or "").upper()[:1]
        if letter in FOCUS:
            drafted[letter] = drafted.get(letter, 0) + 1
    coverage = focus_coverage(rows, drafted)

    settings = launch_settings(kpi)
    moment, zone_note = next_launch(now, settings)
    spend_7d = num(ads.get("spend_7d"))
    total_spend = sum(r["spend"] for r in rows)
    window = num(ads.get("window_days")) or 30
    daily = spend_7d / 7 if spend_7d is not None else total_spend / window
    video_spend = sum(r["spend"] for r in rows if r["format"] == "video")
    size = batch_size(daily, video_spend / total_spend if total_spend else 0.0)

    recommended, held = [], []
    if upcoming:
        def rank(still: dict[str, Any]) -> tuple[int, int, str]:
            letter = str(still["ad"].get("focus") or "").upper()[:1]
            return (0 if letter == coverage["short"] else 1, 0 if still["critic"] == "pass" else 1, still["id"])
        for still in sorted(upcoming["stills"], key=rank):
            if still["critic"] == "fail":
                held.append(still)
            elif len(recommended) < size["stills"]:
                recommended.append(still)
    winners = sorted((r for r in rows if r["verdict"] == "Winner"), key=lambda r: -r["spend"])[:4]
    proven = [b for b in coverage["buckets"].values()
              if b["roas"] is not None and k["kill_spend"] is not None and b["live_spend"] >= k["kill_spend"]]
    best_bucket = max(proven, key=lambda b: b["roas"], default=None)
    return {
        "agents": agents(), "approvals": approvals(), "ledger": ledger(),
        "ads": ads, "shopify": shop, "kpi": {**kpi, **k, "launch": settings},
        "tracker": rows, "focus": coverage, "batches": gallery, "memory": memories(),
        "launch": {
            "next": moment.isoformat(), "epoch_ms": int(moment.timestamp() * 1000), "until": until(moment - now),
            "label": f"{moment.strftime('%A')} {moment.day} {moment.strftime('%B')}, "
                     f"{moment.hour % 12 or 12}:{moment.minute:02d} {'AM' if moment.hour < 12 else 'PM'}",
            "zone": settings["timezone"], "zone_note": zone_note, "daily_spend": round(daily, 2), "size": size,
            "upcoming": upcoming["name"] if upcoming else None, "recommended": recommended, "held": held,
            "winners": winners, "best_bucket": best_bucket,
            "kill_candidates": [r for r in rows if r["kill"] == "Kill candidate"],
        },
    }


# ---------------------------------------------------------------- html

def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def money(value: Any) -> str:
    v = num(value)
    return f"${v:,.2f}" if v is not None else "n/a"


def ratio(value: Any) -> str:
    v = num(value)
    return f"{v:.2f}" if v is not None else "n/a"


def pct(value: Any, digits: int = 2) -> str:
    v = num(value)
    return f"{v:.{digits}f}%" if v is not None else "n/a"


def sample_tag(data: Any) -> str:
    flag = data.get("_sample") if isinstance(data, dict) else bool(data)
    return '<span class="tag">SAMPLE</span>' if flag else ""


def img_url(batch: str, file: str) -> str:
    return f"/img/{esc(batch)}/{esc(file)}"


def pill(text: str, cls: str = "") -> str:
    return f'<span class="pill {esc(cls or text)}">{esc(text)}</span>' if text else ""


NAV = [("/", "Overview"), ("/launch", "Weekly launch"), ("/tracker", "Ads tracker"), ("/focus", "F.O.C.U.S."),
       ("/batches", "Batches"), ("/memory", "Memory")]

CSS = """
:root { --bg:#fbf7f4; --card:#fff; --ink:#2b2330; --muted:#857a8a; --line:#ece4ea; --accent:#c25b8a;
  --ok:#3f9b6b; --warn:#d99a2b; --bad:#c84b4b; --okbg:#d8efe2; --okink:#245c3f; --badbg:#f6d9d9; --badink:#7a2626;
  --warnbg:#f8ead0; --warnink:#7a5513; }
@media (prefers-color-scheme: dark) { :root { --bg:#1b171d; --card:#251f28; --ink:#f3eef5; --muted:#a99cad;
  --line:#3a3140; --accent:#e58ab3; --okbg:#1f3a2c; --okink:#a7dcbd; --badbg:#432326; --badink:#f2b3b3;
  --warnbg:#3f3220; --warnink:#f0d29a; } }
* { box-sizing:border-box }
body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.45 system-ui, sans-serif }
header { padding:18px 24px 6px; display:flex; align-items:baseline; gap:12px; flex-wrap:wrap }
h1 { margin:0; font-size:22px } h1 span { color:var(--accent) }
nav { display:flex; gap:6px; flex-wrap:wrap; padding:6px 24px 0 }
nav a { color:var(--ink); text-decoration:none; padding:5px 12px; border-radius:99px; border:1px solid var(--line);
  background:var(--card); font-size:14px }
nav a.on { background:var(--accent); border-color:var(--accent); color:#fff }
main { display:grid; gap:16px; padding:16px 24px 32px; grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr)) }
section { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 18px; min-width:0 }
h2 { margin:0 0 10px; font-size:14px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted) }
h3 { margin:14px 0 6px; font-size:15px }
a { color:var(--accent) }
.scroll { overflow-x:auto }
table { width:100%; border-collapse:collapse } td, th { padding:6px; border-top:1px solid var(--line); vertical-align:top }
th { text-align:left; font-size:12px; color:var(--muted); font-weight:600; white-space:nowrap }
td.n, th.n { text-align:right; white-space:nowrap }
.muted { color:var(--muted) } code { font-size:12px }
.big { display:flex; gap:22px; flex-wrap:wrap; margin-bottom:8px } .big div b { display:block; font-size:24px }
.dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:6px; background:var(--muted) }
.dot.working { background:var(--warn) } .dot.idle, .dot.done { background:var(--ok) } .dot.blocked { background:var(--bad) }
.pill { font-size:12px; padding:1px 8px; border-radius:99px; background:var(--line); white-space:nowrap }
.pill.done, .pill.pass, .pill.Winner, .pill.good { background:var(--okbg); color:var(--okink) }
.pill.failed, .pill.blocked, .pill.fail, .pill.kill { background:var(--badbg); color:var(--badink) }
.pill.waiting_approval, .pill.warn { background:var(--warnbg); color:var(--warnink) }
.tag { font-size:11px; background:var(--warn); color:#fff; padding:1px 6px; border-radius:4px; margin-left:6px;
  letter-spacing:0; text-transform:none }
ul { margin:0; padding-left:18px } li { margin:6px 0 }
.wide { grid-column:1/-1 }
.count { font-size:40px; font-weight:700; font-variant-numeric:tabular-nums }
.thumbs { display:grid; gap:12px; grid-template-columns:repeat(auto-fill,minmax(140px,1fr)) }
.thumbs figure { margin:0; min-width:0 }
.thumbs img { width:100%; aspect-ratio:4/5; object-fit:cover; border-radius:8px; border:1px solid var(--line);
  background:var(--line); display:block }
.thumbs figcaption { font-size:13px; margin-top:4px }
.buckets { display:grid; gap:10px; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)) }
.bucket { border:1px solid var(--line); border-radius:12px; padding:12px }
.bucket b.l { font-size:28px; color:var(--accent) }
.bucket.short { border-color:var(--bad); background:var(--badbg) } .bucket.short b.l { color:var(--badink) }
tr.short td { background:var(--badbg) }
pre.doc { white-space:pre-wrap; overflow-wrap:anywhere; font:14px/1.55 ui-monospace, monospace; margin:0 }
@media (max-width:600px) { header, nav { padding-left:16px; padding-right:16px } main { padding:12px 16px 28px }
  .count { font-size:32px } }
"""

COUNTDOWN_JS = """<script>
(function(){var el=document.getElementById('count');if(!el)return;var t=+el.dataset.target;
function tick(){var s=Math.max(0,Math.floor((t-Date.now())/1000));var d=Math.floor(s/86400);s%=86400;
var h=Math.floor(s/3600);s%=3600;var m=Math.floor(s/60);s%=60;el.textContent=d+'d '+h+'h '+m+'m '+s+'s';}
tick();setInterval(tick,1000);})();
</script>"""


def shell(title: str, path: str, body: str, refresh: bool = True, script: str = "") -> str:
    nav = "".join(f'<a href="{href}"{" class=on" if href == path else ""}>{esc(label)}</a>' for href, label in NAV)
    meta = '<meta http-equiv="refresh" content="30">' if refresh else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{meta}<title>{esc(title)} | Emma HQ</title>
<style>{CSS}</style></head><body>
<header><h1>Emma <span>HQ</span></h1><span class="muted">Earrings by Emma agent desk.</span></header>
<nav>{nav}</nav>
<main>
{body}
</main>{script}</body></html>"""


def table(head: list[tuple[str, str]], rows: list[str], empty: str) -> str:
    th = "".join(f'<th class="{cls}">{esc(label)}</th>' for label, cls in head)
    body = "".join(rows) or f'<tr><td colspan="{len(head)}" class="muted">{empty}</td></tr>'
    return f'<div class="scroll"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def kill_pill(kill: str) -> str:
    cls = {"Kill candidate": "kill", "Above break even": "good", "Too early": "none",
           "Under kill threshold": "none"}.get(kill, "warn")
    return pill(kill, cls)


def page(s: dict[str, Any]) -> str:
    """The overview page (the original dashboard)."""
    agent_rows = "".join(
        f'<tr><td>{esc(a.get("name"))}</td><td><span class="dot {esc(a.get("state"))}"></span>{esc(a.get("state"))}</td>'
        f'<td class="muted">{esc(a.get("detail"))}</td></tr>' for a in s["agents"]
    ) or '<tr><td colspan="3" class="muted">No agents running. Start them with <code>scripts/hq start</code>.</td></tr>'

    approval_rows = "".join(
        f'<li><b>{esc(a["title"])}</b><br><span class="muted">{esc(a["from"])} {esc(a["kind"])} {esc(a["asked"])} '
        f'<code>{esc(a["file"])}</code></span></li>' for a in s["approvals"]
    ) or '<li class="muted">Nothing is waiting on you.</li>'

    ledger_rows = "".join(
        f'<tr><td class="muted">{esc(str(j.get("updated", ""))[5:16].replace("T", " "))}</td><td>{esc(j.get("agent"))}</td>'
        f'<td>{pill(str(j.get("status", "")))}</td><td>{esc(j.get("title"))}</td></tr>'
        for j in s["ledger"]
    ) or '<tr><td colspan="4" class="muted">No work recorded yet.</td></tr>'

    ads, shop, kpi, rows = s["ads"], s["shopify"], s["kpi"], s["tracker"]
    spend, revenue = num(ads.get("spend_7d")), num(ads.get("purchase_value_7d"))
    window = "last 7 days"
    if spend is None:
        spend, revenue = sum(r["spend"] for r in rows), sum(r["revenue"] for r in rows)
        window = f"last {int(num(ads.get('window_days')) or 30)} days"
    roas = f"{revenue / spend:.2f}" if spend and revenue is not None else "n/a"
    be = kpi.get("breakeven_roas")
    be_text = esc(be) if be else "set data/kpi.json"
    ad_rows_html = "".join(
        f'<tr><td>{esc(r["name"])}</td><td>{esc(r["focus"])}</td><td class="n">{money(r["spend"])}</td>'
        f'<td class="n">{ratio(r["roas"])}</td></tr>' for r in sorted(rows, key=lambda r: -r["spend"])[:8]
    )
    top_rows = "".join(
        f'<tr><td>{esc(p.get("title"))}</td><td>{esc(p.get("units_7d"))}</td></tr>' for p in shop.get("top_products", [])[:6]
    )
    body = f"""<section><h2>Waiting on you</h2><ul>{approval_rows}</ul></section>
<section><h2>Agents</h2><table>{agent_rows}</table></section>
<section><h2>Meta ads, {window} {sample_tag(ads)}</h2>
<div class="big"><div><b>{money(spend)}</b><span class="muted">spend</span></div>
<div><b>{roas}</b><span class="muted">ROAS</span></div>
<div><b>{be_text}</b><span class="muted">break even ROAS</span></div></div>
<table>{ad_rows_html}</table><p class="muted">Updated {esc(ads.get("updated", "never"))}.
Next launch in {esc(s["launch"]["until"])}. <a href="/launch">Weekly launch</a></p></section>
<section><h2>Store sales {sample_tag(shop)}</h2>
<div class="big"><div><b>{money(shop.get("sales_today"))}</b><span class="muted">today</span></div>
<div><b>{money(shop.get("sales_7d"))}</b><span class="muted">7 days</span></div>
<div><b>{esc(shop.get("orders_7d", "n/a"))}</b><span class="muted">orders, 7 days</span></div></div>
<table>{top_rows}</table><p class="muted">Updated {esc(shop.get("updated", "never"))}</p></section>
<section class="wide"><h2>Recent work (ledger)</h2><table>{ledger_rows}</table></section>"""
    return shell("Overview", "/", body)


def thumb(batch: str, still: dict[str, Any], caption: str) -> str:
    url = img_url(batch, still["file"])
    alt = esc(still["ad"].get("on_image") or still["id"])
    return f'<figure><a href="{url}"><img loading="lazy" src="{url}" alt="{alt}"></a><figcaption>{caption}</figcaption></figure>'


def still_caption(still: dict[str, Any], text_key: str) -> str:
    critic = pill(still["critic"]) if still["critic"] else pill("not checked", "warn")
    return (f'<b>{esc(still["id"])}</b> {esc(still["ad"].get("focus", ""))} {critic}'
            f'<br>{esc(still["ad"].get(text_key, ""))}')


def launch_page(s: dict[str, Any]) -> str:
    L, k, cov, ads, gallery = s["launch"], s["kpi"], s["focus"], s["ads"], s["batches"]
    short = cov["buckets"][cov["short"]]
    size = L["size"]
    if not L["upcoming"]:
        rec_html = '<p class="muted">No batch waiting. Run <code>/batch</code> in HQ to plan and build the next one.</p>'
    else:
        rec = "".join(thumb(L["upcoming"], st, still_caption(st, "headline")) for st in L["recommended"]) \
            or '<p class="muted">No still is ready yet.</p>'
        held = "".join(f'<li><b>{esc(st["id"])}</b> failed the critic gate. Fix and rebuild it before it can go.</li>'
                       for st in L["held"])
        rec_html = (f'<p>From <a href="/batches#b-{esc(L["upcoming"])}"><code>{esc(L["upcoming"])}</code></a>'
                    f'{sample_tag(gallery["sample"])}. Up to {size["stills"]} stills, the short bucket first, '
                    f'critic passes only.</p><div class="thumbs">{rec}</div>' + (f"<ul>{held}</ul>" if held else ""))
    win_rows = [f'<tr><td>{esc(r["name"])}</td><td>{esc(r["focus"])}</td><td class="n">{money(r["spend"])}</td>'
                f'<td class="n">{ratio(r["roas"])}</td><td class="n">{pct(r["share"] * 100, 0)}</td></tr>'
                for r in L["winners"]]
    best = L["best_bucket"]
    if best:
        best_line = (f'<p>Best running bucket: <b>{esc(best["letter"])} {esc(best["name"])}</b>, '
                     f'ROAS {ratio(best["roas"])} on {money(best["live_spend"])}.</p>')
    else:
        best_line = '<p class="muted">No bucket has spent the kill threshold yet, so none is proven.</p>'
    kills = "".join(f'<li>{esc(r["name"])}: {money(r["spend"])} spent, ROAS {ratio(r["roas"])}, '
                    f'{int(r["days_live"] or 0)} days live</li>' for r in L["kill_candidates"]) \
        or '<li class="muted">Nothing has hit the kill switch.</li>'
    winners_table = table([("Ad", ""), ("Bucket", ""), ("Spend", "n"), ("ROAS", "n"), ("Share", "n")], win_rows,
                          "No winner yet. A winner beats target ROAS on at least 3% of spend.")
    body = f"""<section><h2>Next launch {sample_tag(k)}</h2>
<div class="count" id="count" data-target="{L["epoch_ms"]}">{esc(L["until"])}</div>
<p><b>{esc(L["label"])}</b> <span class="muted">{esc(L["zone"])}</span><br>
<span class="muted">Change the day, time and zone in <code>data/kpi.json</code> under <code>launch</code>.
{esc(L["zone_note"])}</span></p></section>
<section><h2>This week's batch size {sample_tag(ads)}</h2>
<div class="big"><div><b>{size["total"]}</b><span class="muted">new ads</span></div>
<div><b>{size["stills"]}</b><span class="muted">stills 4:5</span></div>
<div><b>{size["videos"]}</b><span class="muted">videos 9:16</span></div></div>
<p class="muted">Spend is about {money(L["daily_spend"])} a day, so tier {size["tier"]}: {size["range"]} new ads,
one new ad set, one testing focus.</p></section>
<section><h2>Short bucket {sample_tag(ads)}</h2>
<div class="big"><div><b>{esc(short["letter"])}</b><span class="muted">{esc(short["name"])}</span></div>
<div><b>{short["live"]}</b><span class="muted">running ads</span></div>
<div><b>{money(short["live_spend"])}</b><span class="muted">running spend</span></div></div>
<p class="muted">The bucket with the least running spend. Give it at least two ads in the next batch.
<a href="/focus">All buckets</a></p></section>
<section class="wide"><h2>Recommended stills for the next batch</h2>{rec_html}</section>
<section><h2>What is winning {sample_tag(ads)}</h2>{winners_table}
{best_line}<p class="muted">Target ROAS {ratio(k.get("target_roas"))}, break even {ratio(k.get("breakeven_roas"))}.</p></section>
<section><h2>Kill switch proposals {sample_tag(ads)}</h2><ul>{kills}</ul>
<p class="muted">A proposal only. The owner pauses ads, never an agent. <a href="/tracker">Ads tracker</a></p></section>"""
    return shell("Weekly launch", "/launch", body, refresh=False, script=COUNTDOWN_JS)


def tracker_page(s: dict[str, Any]) -> str:
    k, ads, rows = s["kpi"], s["ads"], s["tracker"]
    lines = []
    for i, r in enumerate(rows, 1):
        cpa = money(r["cpa"]) if r["cpa"] is not None else "none"
        days = "" if r["days_live"] is None else str(int(r["days_live"]))
        lines.append(f'<tr><td class="n muted">{i}</td><td>{esc(r["name"])}<br><span class="muted">{esc(r["batch"])} '
                     f'{esc(r["format"])}</span></td><td>{esc(r["focus"])}</td><td>{pill(r["verdict"])}</td>'
                     f'<td class="n">{money(r["spend"])}</td><td class="n">{ratio(r["roas"])}</td><td class="n">{cpa}</td>'
                     f'<td class="n">{pct(r["ctr"])}</td><td class="n">{int(r["purchases"])}</td>'
                     f'<td class="n">{days}</td><td>{kill_pill(r["kill"])}</td></tr>')
    ranked = table([("#", "n"), ("Ad", ""), ("Bucket", ""), ("Verdict", ""), ("Spend", "n"), ("ROAS", "n"),
                    ("CPA", "n"), ("CTR", "n"), ("Buys", "n"), ("Days", "n"), ("Kill switch", "")], lines,
                   "No ad spent in this window. The ads agent fills <code>data/ads.json</code> "
                   "with <code>ads/tools/meta_pull.py</code>.")
    body = f"""<section class="wide"><h2>The money rules {sample_tag(k)}</h2>
<div class="big"><div><b>{ratio(k.get("breakeven_roas"))}</b><span class="muted">break even ROAS</span></div>
<div><b>{ratio(k.get("target_roas"))}</b><span class="muted">target ROAS</span></div>
<div><b>{money(k.get("breakeven_cpa"))}</b><span class="muted">break even CPA</span></div>
<div><b>{money(k.get("target_cpa"))}</b><span class="muted">target CPA</span></div>
<div><b>{money(k.get("kill_spend"))}</b><span class="muted">kill threshold</span></div></div>
<p class="muted">Break even ROAS is average order value divided by what is left after product, shipping and fees.
Target is 25% better. Kill switch: an ad with 10x target CPA spent, 7 days live and ROAS under break even
is proposed for pausing. The owner decides.</p></section>
<section class="wide"><h2>Every ad that spent, best to worst {sample_tag(ads)}</h2>{ranked}
<p class="muted">Last {int(num(ads.get("window_days")) or 30)} days. Source {esc(ads.get("source", "unknown"))}.
Updated {esc(ads.get("updated", "never"))}.</p></section>"""
    return shell("Ads tracker", "/tracker", body)


def focus_page(s: dict[str, Any]) -> str:
    cov, ads = s["focus"], s["ads"]
    cards, lines = [], []
    for letter, b in cov["buckets"].items():
        short = letter == cov["short"] or b["live"] == 0
        gap = "<br><b>The gap</b>" if letter == cov["short"] else ""
        cards.append(f'<div class="bucket{" short" if short else ""}"><b class="l">{letter}</b> {esc(b["name"])}<br>'
                     f'<b>{b["live"]}</b> live, <b>{b["tested"]}</b> tested{gap}</div>')
        lines.append(f'<tr class="{"short" if short else ""}"><td><b>{letter}</b> {esc(b["name"])}</td>'
                     f'<td class="n">{b["live"]}</td><td class="n">{b["tested"]}</td><td class="n">{money(b["live_spend"])}</td>'
                     f'<td class="n">{pct(b["share"] * 100, 0)}</td><td class="n">{ratio(b["roas"])}</td>'
                     f'<td class="n">{b["drafted"]}</td></tr>')
    upcoming = s["launch"]["upcoming"]
    where = f"<code>{esc(upcoming)}</code>" if upcoming else "no batch yet"
    untagged = f'{cov["untagged"]} ads have no bucket letter in their name.' if cov["untagged"] else ""
    by_bucket = table([("Bucket", ""), ("Live", "n"), ("Tested", "n"), ("Running spend", "n"), ("Share", "n"),
                       ("ROAS", "n"), ("In next batch", "n")], lines, "")
    body = f"""<section class="wide"><h2>F.O.C.U.S. coverage {sample_tag(ads)}</h2>
<div class="buckets">{"".join(cards)}</div>
<p class="muted">Live means running now. Tested means it spent in the last 30 days, running or paused.
The gap is the bucket with the least running spend; a bucket with nothing running is highlighted too.</p></section>
<section class="wide"><h2>By bucket</h2>{by_bucket}
<p class="muted">In next batch counts the drafts in {where}. {untagged}</p></section>
<section class="wide"><h2>What the letters mean</h2><ul>
<li><b>F Frustration:</b> the pain they live with now.</li><li><b>O Outcome:</b> the life after.</li>
<li><b>C Constraint:</b> what stops them buying, removed.</li><li><b>U Unspoken cost:</b> the hidden cost of doing nothing.</li>
<li><b>S Skepticism:</b> "I've tried everything."</li></ul>
<p class="muted">More in <code>ads/docs/focus.md</code>.</p></section>"""
    return shell("F.O.C.U.S.", "/focus", body)


def batches_page(s: dict[str, Any]) -> str:
    gallery = s["batches"]
    parts = []
    for b in gallery["items"]:
        stills = "".join(thumb(b["name"], st, still_caption(st, "on_image")) for st in b["stills"]) \
            or '<p class="muted">No stills built yet.</p>'
        copy = [f'<tr><td><b>{esc(a.get("id"))}</b></td><td>{esc(a.get("focus"))}</td><td>{esc(a.get("headline"))}</td>'
                f'<td>{esc(a.get("primary_text"))}</td></tr>' for a in b["ads"]]
        critic_cls = "pass" if b["critic"] == "passed" else ("fail" if "failed" in b["critic"] else "warn")
        score = f'{b["diversity"]:g}/10' if b["diversity"] is not None else "not rated"
        sheet = f' <a href="{img_url(b["name"], "sheet.jpg")}">Contact sheet</a>' if b["sheet"] else ""
        copy_table = table([("Ad", ""), ("Bucket", ""), ("Headline", ""), ("Primary text", "")], copy,
                           "No copy.json yet.")
        parts.append(f"""<section class="wide" id="b-{esc(b["name"])}"><h2>{esc(b["name"])} {sample_tag(gallery["sample"])}</h2>
<p>Testing focus <b>{esc(b["focus"] or "not set")}</b>. Critic gate {pill(b["critic"], critic_cls)}
Variety <b>{esc(score)}</b>.{sheet}</p>
<div class="thumbs">{stills}</div>
<h3>Copy</h3>{copy_table}</section>""")
    body = "".join(parts) or ('<section class="wide"><h2>Batches</h2><p class="muted">No batches yet. '
                              'Run <code>/batch</code> in HQ.</p></section>')
    return shell("Batches", "/batches", body)


def memory_page(s: dict[str, Any]) -> str:
    mem = s["memory"]
    tag = '<span class="tag">STARTER</span>' if mem["starter"] else ""
    lines = [f'<tr><td><a href="/memory/{esc(m["file"])}">{esc(m["name"])}</a></td><td>{esc(m["type"])}</td>'
             f'<td>{esc(m["description"])}</td></tr>' for m in mem["items"]]
    note = ("These are the starter memories in <code>memory-seed/</code>. Run <code>./setup.sh</code> "
            "to copy them into <code>memory/</code>." if mem["starter"] else
            "Read only. Teach the agents with <code>/remember</code> in HQ.")
    body = f"""<section class="wide"><h2>Memory {tag}</h2>
{table([("Name", ""), ("Type", ""), ("Description", "")], lines, "No memories yet.")}
<p class="muted">{note}</p></section>"""
    return shell("Memory", "/memory", body)


def memory_doc_page(name: str, text: str) -> str:
    body = (f'<section class="wide"><h2>{esc(name)}</h2><pre class="doc">{esc(text)}</pre>'
            f'<p><a href="/memory">All memories</a></p></section>')
    return shell(name, "/memory", body, refresh=False)


# ---------------------------------------------------------------- server

PAGES = {"/": page, "/index.html": page, "/launch": launch_page, "/tracker": tracker_page,
         "/focus": focus_page, "/batches": batches_page, "/memory": memory_page}


class Handler(BaseHTTPRequestHandler):
    def send(self, body: bytes, kind: str, extra: dict[str, str] | None = None) -> None:
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        parts = [unquote(p) for p in path.split("/")[1:]]
        if path.startswith("/api/state"):
            self.send(json.dumps(state(), default=str).encode(), "application/json")
        elif path in PAGES:
            self.send(PAGES[path](state()).encode(), "text/html; charset=utf-8")
        elif len(parts) == 3 and parts[0] == "img":
            found = batch_file(parts[1], parts[2])
            if not found:
                self.send_error(404)
                return
            kind = mimetypes.guess_type(found.name)[0] or "application/octet-stream"
            self.send(found.read_bytes(), kind, {"Cache-Control": "max-age=60"})
        elif len(parts) == 2 and parts[0] == "memory":
            doc = memory_file(parts[1])
            if not doc:
                self.send_error(404)
                return
            self.send(memory_doc_page(*doc).encode(), "text/html; charset=utf-8")
        else:
            self.send_error(404)

    def log_message(self, *args: Any) -> None:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Emma HQ dashboard")
    parser.add_argument("--port", type=int, default=int(os.environ.get("HQ_DASHBOARD_PORT", 8765)))
    parser.add_argument("--host", default="127.0.0.1", help="keep 127.0.0.1 so only this computer can see it")
    parser.add_argument("--once", action="store_true", help="print the data as JSON and exit")
    args = parser.parse_args()
    if args.once:
        print(json.dumps(state(), indent=2, default=str))
        return 0
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Emma HQ dashboard: http://localhost:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

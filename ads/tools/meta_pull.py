#!/usr/bin/env python3
"""Fill data/ads.json with the last 30 days of Meta ad numbers. Read only. Python standard library only.

Three ways in:

  python3 ads/tools/meta_pull.py --check            test the token in .env (prints the account name, never the token)
  python3 ads/tools/meta_pull.py                    pull from the Meta Marketing API (Graph API insights, read only)
  python3 ads/tools/meta_pull.py --csv export.csv   import an Ads Manager export instead (no token needed)

Other options:
  --out PATH           where to write (default data/ads.json)
  --from-json PATH     build from a saved API response bundle (for tests and dry runs; no network)
  --dry-run            print the summary, write nothing
  --today YYYY-MM-DD   pretend today is this date (for tests)

The token and ad account id come from .env (META_ACCESS_TOKEN, META_AD_ACCOUNT_ID) or the environment.
The token is sent only in a request header to graph.facebook.com and is never printed, logged or saved.
The script only ever sends GET requests. It cannot change, pause or fund an ad.

Each ad's F.O.C.U.S. letter and batch come from its name: start the ad name with the letter
("S | Tried every metal") or put it in brackets ("[S]"), and name the ad set after the batch's launch
date ("2026-11-04"). data/ad-tags.json can override both by ad id: {"1203...": {"focus": "S", "batch": "2026-11-04"}}.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUT = ROOT / "data" / "ads.json"
GRAPH = os.environ.get("META_GRAPH_URL", "https://graph.facebook.com").rstrip("/")
VERSION = os.environ.get("META_API_VERSION", "v23.0")
PURCHASE_TYPES = ("omni_purchase", "purchase", "offsite_conversion.fb_pixel_purchase")
INSIGHT_FIELDS = "ad_id,ad_name,adset_name,campaign_name,spend,impressions,inline_link_clicks,inline_link_click_ctr,ctr,actions,action_values"
AD_FIELDS = "id,name,effective_status,created_time,adset{name},creative{object_type,video_id}"
FOCUS_LETTERS = "FOCUS"

_SECRETS: list[str] = []


class PullError(Exception):
    pass


# ---------------------------------------------------------------- output that never shows a secret

def redact(text: str) -> str:
    for secret in _SECRETS:
        if secret:
            text = text.replace(secret, "[hidden]")
    return re.sub(r"(access_token=)[^&\s\"']+", r"\1[hidden]", text)


def say(text: str, err: bool = False) -> None:
    print(redact(text), file=sys.stderr if err else sys.stdout)


# ---------------------------------------------------------------- settings

def load_env(path: Path) -> dict[str, str]:
    """Read KEY=VALUE lines from .env. The real environment wins over the file."""
    values: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    for key in ("META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"):
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def credentials() -> tuple[str, str]:
    env = load_env(Path(os.environ.get("HQ_ENV_FILE") or ROOT / ".env"))
    token = env.get("META_ACCESS_TOKEN", "").strip()
    account = re.sub(r"^act_", "", env.get("META_AD_ACCOUNT_ID", "").strip())
    if token:
        _SECRETS.append(token)
    missing = [name for name, value in (("META_ACCESS_TOKEN", token), ("META_AD_ACCOUNT_ID", account)) if not value]
    if missing:
        raise PullError(f"{' and '.join(missing)} missing from .env. See docs/connect-meta.md, "
                        "or use --csv with an Ads Manager export.")
    if not account.isdigit():
        raise PullError("META_AD_ACCOUNT_ID should be the ad account number (digits only, act_ is optional).")
    return token, account


# ---------------------------------------------------------------- Graph API (GET only)

def graph_get(url: str, token: str) -> dict[str, Any]:
    parts = urllib.parse.urlsplit(url)
    if f"{parts.scheme}://{parts.netloc}" != GRAPH:
        raise PullError("Refusing to send the token to a host that is not the Graph API.")
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True) if k != "access_token"]
    clean = urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))
    request = urllib.request.Request(clean, method="GET", headers={"Authorization": f"Bearer {token}",
                                                                  "User-Agent": "emma-hq-meta-pull"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            problem = json.loads(error.read().decode("utf-8")).get("error", {})
        except (ValueError, AttributeError):
            problem = {}
        code = f" (error {problem['code']})" if isinstance(problem, dict) and problem.get("code") else ""
        detail = problem.get("message", "") if isinstance(problem, dict) else ""
        raise PullError(f"Meta said HTTP {error.code}{code}: {detail or error.reason}") from None
    except (urllib.error.URLError, TimeoutError) as error:
        raise PullError(f"Could not reach Meta: {getattr(error, 'reason', error)}") from None


def graph_all(path: str, params: dict[str, str], token: str) -> list[dict[str, Any]]:
    url = f"{GRAPH}/{VERSION}/{path}?{urllib.parse.urlencode(params)}"
    rows: list[dict[str, Any]] = []
    for _ in range(200):  # paging guard
        page = graph_get(url, token)
        rows.extend(page.get("data", []))
        url = page.get("paging", {}).get("next")
        if not url:
            break
    return rows


def check(token: str, account: str) -> str:
    info = graph_get(f"{GRAPH}/{VERSION}/act_{account}?fields=name,currency,account_status", token)
    status = {1: "active", 2: "disabled", 3: "unsettled", 7: "pending review", 9: "in grace period",
              101: "closed"}.get(info.get("account_status"), str(info.get("account_status", "unknown")))
    return (f"Connected to ad account \"{info.get('name', 'unnamed')}\" ({info.get('currency', '?')}, {status}). "
            "The token works and was not printed.")


def pull_bundle(token: str, account: str) -> dict[str, Any]:
    act = f"act_{account}"
    return {
        "insights": {"data": graph_all(f"{act}/insights", {"level": "ad", "date_preset": "last_30d",
                                                           "fields": INSIGHT_FIELDS, "limit": "500"}, token)},
        "ads": {"data": graph_all(f"{act}/ads", {"fields": AD_FIELDS, "limit": "500"}, token)},
        "account_7d": {"data": graph_all(f"{act}/insights", {"level": "account", "date_preset": "last_7d",
                                                             "fields": "spend,actions,action_values"}, token)},
    }


# ---------------------------------------------------------------- shaping

def number(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().replace(",", "").replace("$", "").replace("%", "")
    try:
        return float(text) if text not in ("", "-", "—", "–") else 0.0
    except ValueError:
        return 0.0


def first_action(items: Any) -> float:
    """Purchases (or purchase value), taking one action type so nothing is counted twice."""
    found = {i.get("action_type"): number(i.get("value")) for i in items or [] if isinstance(i, dict)}
    for kind in PURCHASE_TYPES:
        if kind in found:
            return found[kind]
    return 0.0


def focus_from(*names: str) -> str:
    for name in names:
        match = re.match(r"\s*([FOCUS])\s*[|:]\s", name or "") or re.search(r"\[([FOCUS])\]", name or "")
        if match:
            return match.group(1)
    return ""


def batch_from(*names: str) -> str:
    for name in names:
        match = re.search(r"\d{4}-\d{2}-\d{2}", name or "")
        if match:
            return match.group(0)
    return ""


def status_from(value: str) -> str:
    v = (value or "").strip().lower().replace("_", " ")
    if v in ("active", "on") or v.startswith("active"):
        return "active"
    if not v:
        return ""
    if "pause" in v or v in ("off", "inactive", "ad set off", "campaign off", "not delivering"):
        return "paused"
    return v


def finish(row: dict[str, Any], tags: dict[str, Any]) -> dict[str, Any]:
    override = tags.get(row["id"], {}) if isinstance(tags, dict) else {}
    for key in ("focus", "batch", "format"):
        if isinstance(override, dict) and override.get(key):
            row[key] = override[key]
    spend, purchases, revenue = row["spend"], row["purchases"], row["revenue"]
    row["roas"] = round(revenue / spend, 2) if spend else 0.0
    row["cpa"] = round(spend / purchases, 2) if purchases else None
    return row


def build_from_bundle(bundle: dict[str, Any], today: date, tags: dict[str, Any]) -> dict[str, Any]:
    meta = {str(a.get("id")): a for a in bundle.get("ads", {}).get("data", []) if isinstance(a, dict)}
    rows = []
    for item in bundle.get("insights", {}).get("data", []):
        spend = number(item.get("spend"))
        if spend <= 0:
            continue
        ad_id = str(item.get("ad_id", ""))
        info = meta.get(ad_id, {})
        name = item.get("ad_name") or info.get("name") or ad_id
        adset = item.get("adset_name") or (info.get("adset") or {}).get("name", "")
        creative = info.get("creative") or {}
        video = creative.get("object_type") == "VIDEO" or bool(creative.get("video_id")) or "video" in name.lower()
        created = info.get("created_time", "")
        days = None
        if created:
            try:
                days = max(0, (today - datetime.fromisoformat(created[:10]).date()).days)
            except ValueError:
                days = None
        ctr = item.get("inline_link_click_ctr", item.get("ctr"))
        rows.append(finish({
            "id": ad_id, "name": name, "focus": focus_from(name, adset), "batch": batch_from(adset, name),
            "format": "video" if video else "still", "status": status_from(info.get("effective_status", "")),
            "spend": round(spend, 2), "purchases": int(first_action(item.get("actions"))),
            "revenue": round(first_action(item.get("action_values")), 2),
            "ctr": round(number(ctr), 2) if ctr is not None else None, "days_live": days,
        }, tags))
    account = (bundle.get("account_7d", {}).get("data") or [{}])[0]
    out = wrap(rows, "meta_api", today)
    out["spend_7d"] = round(number(account.get("spend")), 2)
    out["purchase_value_7d"] = round(first_action(account.get("action_values")), 2)
    return out


def wrap(rows: list[dict[str, Any]], source: str, today: date) -> dict[str, Any]:
    rows.sort(key=lambda r: -r["spend"])
    return {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "as_of": today.isoformat(),
            "source": source, "window_days": 30, "currency": "USD", "ads": rows}


# ---------------------------------------------------------------- CSV from Ads Manager

def norm(header: str) -> str:
    return re.sub(r"\s+", " ", header.replace("﻿", "")).strip().lower()


def pick(row: dict[str, str], *wanted: str, prefix: bool = False) -> str | None:
    """The value of the first column whose name matches (exactly, or by prefix)."""
    keys = {norm(k): k for k in row if k}
    for want in wanted:
        if want in keys:
            return row[keys[want]]
        if prefix:
            for k, original in keys.items():
                if k.startswith(want):
                    return row[original]
    return None


def parse_day(text: str | None) -> date | None:
    if not text:
        return None
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def build_from_csv(path: Path, today: date, tags: dict[str, Any]) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not any(norm(f) == "ad name" for f in reader.fieldnames if f):
            raise PullError("This CSV has no \"Ad name\" column. Export at the Ads level in Ads Manager "
                            "(see docs/connect-meta.md).")
        rows = []
        for row in reader:
            name = (pick(row, "ad name") or "").strip()
            spend = number(pick(row, "amount spent", prefix=True))
            if not name or spend <= 0:
                continue
            adset = pick(row, "ad set name") or ""
            ends = parse_day(pick(row, "reporting ends")) or today
            starts = parse_day(pick(row, "starts", "ad start", "ad set start", "start date"))
            days_text = pick(row, "days live")
            days = int(number(days_text)) if days_text else ((ends - starts).days if starts else None)
            ctr = pick(row, "ctr (link click-through rate)", "ctr (link)", prefix=True)
            if ctr is None:
                ctr = pick(row, "ctr (all)", "ctr")
            ad_id = (pick(row, "ad id") or "").strip() or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            fmt = "video" if "video" in name.lower() else "still"
            rows.append(finish({
                "id": ad_id, "name": name, "focus": focus_from(name, adset), "batch": batch_from(adset, name),
                "format": fmt, "status": status_from(pick(row, "delivery", "ad delivery", "delivery status") or ""),
                "spend": round(spend, 2),
                "purchases": int(number(pick(row, "purchases", "website purchases", "results"))),
                "revenue": round(number(pick(row, "purchases conversion value", "website purchases conversion value",
                                             "purchase conversion value")), 2),
                "ctr": round(number(ctr), 2) if ctr not in (None, "") else None, "days_live": days,
            }, tags))
    if not rows:
        raise PullError("No ad in this CSV spent money. Check the date range (last 30 days) and the Ads level.")
    return wrap(rows, "ads_manager_csv", today)


# ---------------------------------------------------------------- main

def load_tags() -> dict[str, Any]:
    path = Path(os.environ.get("HQ_AD_TAGS") or ROOT / "data" / "ad-tags.json")
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except json.JSONDecodeError:
        say(f"Ignoring {path.name}: it is not valid JSON.", err=True)
        return {}


def summary(doc: dict[str, Any]) -> str:
    ads = doc["ads"]
    spend = sum(a["spend"] for a in ads)
    revenue = sum(a["revenue"] for a in ads)
    untagged = sum(1 for a in ads if not a["focus"])
    roas = f"{revenue / spend:.2f}" if spend else "n/a"
    text = f"{len(ads)} ads spent ${spend:,.2f} in 30 days, ROAS {roas} (source {doc['source']})."
    if untagged:
        text += f" {untagged} have no F.O.C.U.S. letter in their name."
    return text


def write(doc: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    tmp.replace(out)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fill data/ads.json from Meta, read only.")
    parser.add_argument("--check", action="store_true", help="test the token and ad account, print nothing secret")
    parser.add_argument("--csv", type=Path, help="an Ads Manager export (Ads level, last 30 days)")
    parser.add_argument("--from-json", type=Path, help="a saved API response bundle (no network)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--today", help="YYYY-MM-DD, for tests")
    args = parser.parse_args(list(argv) if argv is not None else None)
    today = date.fromisoformat(args.today) if args.today else date.today()
    try:
        if args.check:
            say(check(*credentials()))
            return 0
        tags = load_tags()
        if args.csv:
            doc = build_from_csv(args.csv, today, tags)
        elif args.from_json:
            doc = build_from_bundle(json.loads(args.from_json.read_text(encoding="utf-8")), today, tags)
        else:
            doc = build_from_bundle(pull_bundle(*credentials()), today, tags)
        say(summary(doc))
        if args.dry_run:
            say("Dry run, nothing written.")
        else:
            write(doc, args.out)
            shown = args.out.relative_to(ROOT) if args.out.resolve().is_relative_to(ROOT) else args.out.name
            say(f"Wrote {shown}.")
        return 0
    except PullError as error:
        say(f"meta_pull: {error}", err=True)
        return 1
    except Exception as error:  # never let a traceback carry a secret
        say(f"meta_pull: unexpected {type(error).__name__}: {error}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Emma HQ dashboard. One page, one command, Python standard library only.

  python3 scripts/dashboard.py            then open http://localhost:8765
  python3 scripts/dashboard.py --once     print the page data as JSON and exit

It shows: the agents and their state, approvals waiting on the owner, the ledger's
recent work, ad spend and ROAS, and store sales. The numbers come from JSON files the
agents refresh in data/. Until those exist it shows the sample files in data/examples/
and labels them SAMPLE.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("HQ_DATA_DIR") or ROOT / "data")
APPROVALS = Path(os.environ.get("HQ_APPROVALS_DIR") or ROOT / "approvals")


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
    match = re.match(r"---\n(.*?)\n---", text, re.S)
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


def breakeven_roas(kpi: dict[str, Any]) -> float | None:
    """Break even ROAS = average order value / (average order value minus cost per order)."""
    try:
        aov = float(kpi["average_order_value"])
        cost = sum(float(kpi[k]) for k in ("product_cost_per_order", "shipping_cost_per_order", "fees_per_order"))
    except (KeyError, TypeError, ValueError):
        return None
    margin = aov - cost
    return round(aov / margin, 2) if aov > 0 and margin > 0 else None


def state() -> dict[str, Any]:
    ads, shop, kpi = load_data("ads"), load_data("shopify"), load_data("kpi")
    be = breakeven_roas(kpi)
    return {
        "agents": agents(),
        "approvals": approvals(),
        "ledger": ledger(),
        "ads": ads,
        "shopify": shop,
        "kpi": {**kpi, "breakeven_roas": be, "target_roas": round(be * 1.25, 2) if be else None},
    }


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def money(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "n/a"


def sample_tag(data: dict[str, Any]) -> str:
    return '<span class="tag">SAMPLE</span>' if data.get("_sample") else ""


def page(s: dict[str, Any]) -> str:
    agent_rows = "".join(
        f'<tr><td>{esc(a.get("name"))}</td><td><span class="dot {esc(a.get("state"))}"></span>{esc(a.get("state"))}</td>'
        f'<td class="muted">{esc(a.get("detail"))}</td></tr>' for a in s["agents"]
    ) or '<tr><td colspan="3" class="muted">No agents running. Start them with <code>scripts/hq start</code>.</td></tr>'

    approval_rows = "".join(
        f'<li><b>{esc(a["title"])}</b><br><span class="muted">{esc(a["from"])} {esc(a["kind"])} {esc(a["asked"])} '
        f'<code>{esc(a["file"])}</code></span></li>' for a in s["approvals"]
    ) or '<li class="muted">Nothing is waiting on you.</li>'

    ledger_rows = "".join(
        f'<tr><td class="muted">{esc(j["updated"][5:16].replace("T", " "))}</td><td>{esc(j["agent"])}</td>'
        f'<td><span class="pill {esc(j["status"])}">{esc(j["status"])}</span></td><td>{esc(j["title"])}</td></tr>'
        for j in s["ledger"]
    ) or '<tr><td colspan="4" class="muted">No work recorded yet.</td></tr>'

    ads, shop, kpi = s["ads"], s["shopify"], s["kpi"]
    spend, revenue = ads.get("spend_7d"), ads.get("purchase_value_7d")
    try:
        roas = f"{float(revenue) / float(spend):.2f}" if float(spend) > 0 else "n/a"
    except (TypeError, ValueError):
        roas = "n/a"
    be = kpi.get("breakeven_roas")
    ad_rows = "".join(
        f'<tr><td>{esc(a.get("name"))}</td><td>{esc(a.get("focus"))}</td><td>{money(a.get("spend_7d"))}</td>'
        f'<td>{esc(a.get("roas_7d"))}</td></tr>' for a in ads.get("ads", [])[:8]
    )
    top_rows = "".join(
        f'<tr><td>{esc(p.get("title"))}</td><td>{esc(p.get("units_7d"))}</td></tr>' for p in shop.get("top_products", [])[:6]
    )

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>Emma HQ</title>
<style>
:root {{ --bg:#fbf7f4; --card:#fff; --ink:#2b2330; --muted:#857a8a; --line:#ece4ea; --accent:#c25b8a;
  --ok:#3f9b6b; --warn:#d99a2b; --bad:#c84b4b; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1b171d; --card:#251f28; --ink:#f3eef5; --muted:#a99cad;
  --line:#3a3140; --accent:#e58ab3; }} }}
* {{ box-sizing:border-box }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.45 system-ui, sans-serif }}
header {{ padding:20px 24px 8px; display:flex; align-items:baseline; gap:12px; flex-wrap:wrap }}
h1 {{ margin:0; font-size:22px }} h1 span {{ color:var(--accent) }}
main {{ display:grid; gap:16px; padding:16px 24px 32px; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)) }}
section {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 18px }}
h2 {{ margin:0 0 10px; font-size:14px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted) }}
table {{ width:100%; border-collapse:collapse }} td {{ padding:6px 4px; border-top:1px solid var(--line); vertical-align:top }}
.muted {{ color:var(--muted) }} code {{ font-size:12px }}
.big {{ display:flex; gap:22px; flex-wrap:wrap; margin-bottom:8px }} .big div b {{ display:block; font-size:24px }}
.dot {{ display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:6px; background:var(--muted) }}
.dot.working {{ background:var(--warn) }} .dot.idle, .dot.done {{ background:var(--ok) }} .dot.blocked {{ background:var(--bad) }}
.pill {{ font-size:12px; padding:1px 8px; border-radius:99px; background:var(--line) }}
.pill.done {{ background:#d8efe2; color:#245c3f }} .pill.failed, .pill.blocked {{ background:#f6d9d9; color:#7a2626 }}
.pill.waiting_approval {{ background:#f8ead0; color:#7a5513 }}
.tag {{ font-size:11px; background:var(--warn); color:#fff; padding:1px 6px; border-radius:4px; margin-left:6px }}
ul {{ margin:0; padding-left:18px }} li {{ margin:6px 0 }}
.wide {{ grid-column:1/-1 }}
</style></head><body>
<header><h1>Emma <span>HQ</span></h1><span class="muted">Earrings by Emma agent desk. Refreshes every 30 seconds.</span></header>
<main>
<section><h2>Waiting on you</h2><ul>{approval_rows}</ul></section>
<section><h2>Agents</h2><table>{agent_rows}</table></section>
<section><h2>Meta ads, last 7 days {sample_tag(ads)}</h2>
<div class="big"><div><b>{money(spend)}</b><span class="muted">spend</span></div>
<div><b>{roas}</b><span class="muted">ROAS</span></div>
<div><b>{esc(be) if be else "set data/kpi.json"}</b><span class="muted">break even ROAS</span></div></div>
<table>{ad_rows}</table><p class="muted">Updated {esc(ads.get("updated", "never"))}</p></section>
<section><h2>Store sales {sample_tag(shop)}</h2>
<div class="big"><div><b>{money(shop.get("sales_today"))}</b><span class="muted">today</span></div>
<div><b>{money(shop.get("sales_7d"))}</b><span class="muted">7 days</span></div>
<div><b>{esc(shop.get("orders_7d", "n/a"))}</b><span class="muted">orders, 7 days</span></div></div>
<table>{top_rows}</table><p class="muted">Updated {esc(shop.get("updated", "never"))}</p></section>
<section class="wide"><h2>Recent work (ledger)</h2><table>{ledger_rows}</table></section>
</main></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/api/state"):
            body, kind = json.dumps(state()).encode(), "application/json"
        elif self.path in ("/", "/index.html"):
            body, kind = page(state()).encode(), "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Emma HQ dashboard")
    parser.add_argument("--port", type=int, default=int(os.environ.get("HQ_DASHBOARD_PORT", 8765)))
    parser.add_argument("--host", default="127.0.0.1", help="keep 127.0.0.1 so only this computer can see it")
    parser.add_argument("--once", action="store_true", help="print the data as JSON and exit")
    args = parser.parse_args()
    if args.once:
        print(json.dumps(state(), indent=2))
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

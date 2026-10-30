#!/usr/bin/env bash
# Smoke test for scripts/hq on the tmux backend. Uses its own tmux socket, so it never
# touches a tmux or herdr session you already have open. Agents are plain shells here.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export HQ_BACKEND=tmux HQ_TMUX_SOCKET="hqtest$$" HQ_TMUX_SESSION=hqtest HQ_AGENT_CMD="" HQ_STATE_SAMPLE=0.3 HQ_QUIET_SECONDS=2 HQ_YES=1
HQ="$ROOT/scripts/hq"
pass=0
ok() { echo "ok  $1"; pass=$((pass + 1)); }
fail() { echo "FAIL $1"; tmux -L "$HQ_TMUX_SOCKET" kill-server 2>/dev/null || true; exit 1; }
trap 'tmux -L "$HQ_TMUX_SOCKET" kill-server 2>/dev/null || true' EXIT

[[ "$("$HQ" backend)" == tmux ]] && ok backend || fail backend
"$HQ" list | grep -q "not running" && ok "list before start" || fail "list before start"
"$HQ" start | grep -q "HQ started" && ok start || fail start
"$HQ" start | grep -q "already running" && ok "start is idempotent" || fail "start is idempotent"
n="$("$HQ" list --json | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')"
[[ "$n" == 5 ]] && ok "five agents listed" || fail "five agents listed ($n)"
"$HQ" list --json | python3 -c 'import json,sys; d={a["name"] for a in json.load(sys.stdin)}; assert d=={"hq","ads","social","shopify","email"}' \
  && ok "agent names" || fail "agent names"
sleep 1
"$HQ" prompt ads "pwd; echo HQ_MARK_\$((40+2))" >/dev/null && ok prompt || fail prompt
[[ "$("$HQ" wait ads 20)" == idle ]] && ok "wait returns idle" || fail "wait returns idle"
out="$("$HQ" read ads 30)"
grep -q "HQ_MARK_42" <<<"$out" && ok "read shows output" || fail "read shows output"
grep -q "/ads$" <<<"$out" && ok "ads runs in ads/" || fail "ads runs in ads/"
"$HQ" prompt social "echo '> half typed'" >/dev/null; "$HQ" wait social 20 >/dev/null
if "$HQ" prompt social "echo nope" 2>/dev/null; then fail "refuses when input box has text"; else ok "refuses when input box has text"; fi
"$HQ" prompt email "echo 'Do you want to proceed? (y/n)'" >/dev/null
[[ "$("$HQ" wait email 20)" == blocked ]] && ok "wait sees a dialog" || fail "wait sees a dialog"
"$HQ" list --json | python3 -c 'import json,sys; d={a["name"]:a["state"] for a in json.load(sys.stdin)}; assert d["email"]=="blocked", d' \
  && ok "list marks blocked" || fail "list marks blocked"
if "$HQ" prompt email "echo hi" 2>/dev/null; then fail "refuses a blocked agent"; else ok "refuses a blocked agent"; fi
if "$HQ" read nobody 2>/dev/null; then fail "unknown agent"; else ok "unknown agent rejected"; fi
"$HQ" stop | grep -q stopped && ok stop || fail stop
echo "hq smoke: $pass passed"

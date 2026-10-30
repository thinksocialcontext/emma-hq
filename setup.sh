#!/usr/bin/env bash
# Emma HQ setup for WSL (Ubuntu). Safe to run again at any time.
# It asks before installing anything and never writes a secret into the repository.
#
#   ./setup.sh           check, ask, install what is missing, prepare the folders
#   ./setup.sh --check   only report what is installed; change nothing
#   ./setup.sh --yes     answer yes to every install question
set -uo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
MODE=ask
case "${1:-}" in --check) MODE=check ;; --yes) MODE=yes ;; "") ;; *) echo "usage: ./setup.sh [--check|--yes]"; exit 2 ;; esac

bold() { printf '\n\033[1m%s\033[0m\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }
status() { if have "$1"; then printf '  %-10s installed\n' "$1"; else printf '  %-10s missing\n' "$1"; fi; }
ask() {  # ask "question" -> 0 for yes
  [[ $MODE == yes ]] && return 0
  [[ $MODE == check ]] && return 1
  local reply; read -r -p "$1 [y/N] " reply; [[ "$reply" =~ ^[Yy] ]]
}

bold "Emma HQ setup"
if grep -qi microsoft /proc/version 2>/dev/null; then echo "  Running inside WSL. Good."
else echo "  Not WSL. That is fine on any Ubuntu or Debian machine."; fi

bold "1. What is installed"
for tool in git curl python3 tmux node npm claude gh herdr magick convert jq; do status "$tool"; done

bold "2. Basic tools (git, curl, Python, tmux, ImageMagick, jq, unzip)"
need=()
for pair in git:git curl:curl python3:python3 tmux:tmux jq:jq unzip:unzip; do have "${pair%%:*}" || need+=("${pair##*:}"); done
have magick || have convert || need+=(imagemagick)
if (( ${#need[@]} )); then
  if ask "Install ${need[*]} with apt (needs your Ubuntu password)?"; then
    sudo apt-get update && sudo apt-get install -y "${need[@]}"
  else echo "  Skipped. Missing: ${need[*]}"; fi
else echo "  All present."; fi

bold "3. Node.js LTS (needed by some Claude Code tools and connectors)"
if have node; then echo "  Node $(node --version) present."
elif ask "Install Node.js LTS with nvm (official script from github.com/nvm-sh/nvm)?"; then
  curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
  export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh" && nvm install --lts
else echo "  Skipped."; fi

bold "4. Claude Code"
if have claude; then echo "  Claude Code present."
elif ask "Install Claude Code with the official installer (claude.ai/install.sh)?"; then
  curl -fsSL https://claude.ai/install.sh | bash
  echo "  Open a new terminal, run 'claude' once and sign in with your Claude account."
else echo "  Skipped. Install later from https://claude.com/claude-code"; fi

bold "5. GitHub CLI (optional, for backing this folder up to a private repository)"
if have gh; then echo "  gh present."
elif ask "Install the GitHub CLI with apt?"; then sudo apt-get install -y gh
else echo "  Skipped."; fi

bold "6. herdr (optional, recommended; tmux works without it)"
if have herdr; then
  echo "  herdr present."
  if ask "Let herdr see Claude Code's state (herdr integration install claude)?"; then herdr integration install claude; fi
elif ask "Install herdr from the official installer (herdr.dev, Apache 2.0)?"; then
  curl -fsSL https://herdr.dev/install.sh | sh
  echo "  Then run: herdr integration install claude"
else echo "  Skipped. scripts/hq will use tmux."; fi

if [[ $MODE == check ]]; then bold "Check only. Nothing was changed."; exit 0; fi

bold "7. Folders and private files"
if [[ ! -f .env ]]; then cp .env.example .env && chmod 600 .env && echo "  Created .env (private, ignored by git). Fill in keys only when you need them."
else echo "  .env already exists. Left alone."; fi
if [[ ! -f memory/MEMORY.md ]]; then mkdir -p memory && cp -n memory-seed/*.md memory/ && echo "  Copied the starter memories into memory/."
else echo "  memory/ already set up. Left alone."; fi
mkdir -p work/briefs data email/triage reports
chmod +x scripts/hq scripts/ledger scripts/dashboard.py tests/*.sh 2>/dev/null
echo "  work/, data/ and reports/ ready."

bold "8. Brand fonts for ad stills (Fjalla One and Poppins, free Google Fonts)"
if ls ads/assets/fonts/*.ttf >/dev/null 2>&1; then echo "  Fonts present."
elif ask "Download them from the Google Fonts GitHub repository?"; then
  base=https://raw.githubusercontent.com/google/fonts/main
  for f in ofl/fjallaone/FjallaOne-Regular.ttf ofl/poppins/Poppins-Regular.ttf ofl/poppins/Poppins-Bold.ttf apache/permanentmarker/PermanentMarker-Regular.ttf; do
    curl -fsSL "$base/$f" -o "ads/assets/fonts/${f##*/}" && echo "  ${f##*/}"
  done
else echo "  Skipped. Stills will use ImageMagick's default font."; fi

bold "9. Quick self test"
if bash tests/run.sh >/tmp/emma-hq-tests.log 2>&1; then echo "  All tests passed."
else echo "  Some tests failed. See /tmp/emma-hq-tests.log"; fi

bold "Done. Next:"
cat <<'NEXT'
  scripts/hq start                  open HQ and the four specialists
  scripts/hq attach                 look at them (tmux), or use the herdr window
  python3 scripts/dashboard.py      the dashboard at http://localhost:8765
In the HQ window, try:  /status
NEXT

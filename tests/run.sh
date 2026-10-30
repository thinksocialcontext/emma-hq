#!/usr/bin/env bash
# Run every Emma HQ test. Safe: temp folders and a private tmux socket only.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -v
bash tests/test_hq.sh
bash -n setup.sh && echo "ok  setup.sh parses"

---
description: Read every agent, the ledger and the approvals, then report what needs the owner
---

Read the live state; do not answer from memory.

1. `scripts/hq list`, then `scripts/hq read <agent> 60` for any agent that is working or blocked.
2. `scripts/ledger recent --limit 15`
3. Every file in `approvals/` whose status is `waiting`.

Report in this order, one line each, naming the file or decision:

* Decisions waiting on the owner
* Blocked work (quote the dialog's question; never answer it)
* Finished since the last report
* Important work still running
* Idle agents, only if useful

If nothing needs the owner, say so in one sentence. No dashes.

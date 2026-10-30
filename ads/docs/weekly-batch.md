# The weekly ad batch

A small steady rhythm beats a big irregular push.

* **Launch day:** one fixed day each week (for example Wednesday at 10am). The owner picks it; write it into memory.
* **Size:** 5 to 10 new ads, one new ad set.
* **One testing focus per batch,** in this order over the weeks: angles, then hooks, then visual styles, then formats.
* **Formats:** stills 4:5 (1080x1350), videos 9:16 (1080x1920).

## The loop (also `/batch`)

1. **Refresh and read the numbers.** Run `python3 ads/tools/meta_pull.py` (or `--csv` with the owner's export), then read `data/ads.json`, or the dashboard's Weekly launch page: what spent, what won, which F.O.C.U.S. letter is short, how many new ads the spend calls for.
2. **Draft the experiment card** in `batches/<date>/plan.md`: the focus, the hypothesis, the ads, the budget to ask for.
3. **Write `spec.json`** with every string, letter, persona, photos and the reason each ad should win. Pick formats from the layout catalogue in `docs/how-to-make-ads.md`, from different families, not used in the last two batches. Start from `batches/examples/2026-10-29/spec.json`.
4. **Build** with `python3 tools/build_stills.py batches/<date>`.
5. **Critic gate.** `docs/critic-gate.md`. Fix and rebuild until it passes.
6. **Rate diversity** with `/rate batches/<date>`.
7. **Ask.** Write `approvals/<date>-ad-batch.md` with the sheet path and the budget. Stop.
8. **After approval,** the owner launches (or approves a launch). Record it in the ledger.
9. **Kill switch:** an ad that spends 10x the target cost per purchase with no purchase after 7 days live is proposed for pausing, never paused by an agent.

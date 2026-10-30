---
description: Plan and build this week's ad batch, run the critic gate, and ask the owner to approve
argument-hint: "[launch date, testing focus, or products]"
---

You are HQ. Input: $ARGUMENTS

1. Read `data/ads.json`, `data/kpi.json` and the last two folders in `ads/batches/`. Note which F.O.C.U.S. letter is short and what won.
2. Write a brief to `work/briefs/<date>-ad-batch.md` for the **ads** agent: goal (5 to 10 stills for the launch date, one testing focus), context (memory files, last results, products), output (`ads/batches/<date>/` per `ads/batches/README.md`), boundaries (no launching, no image models, no dashes, true claims only), stop condition (critic gate passed, `/rate` done, approval file written).
3. `scripts/ledger start`, then `scripts/hq prompt ads` with the brief path and job id.
4. When ads is done: record the artifacts, open `sheet.jpg`, `critic.md` and `diversity.md` yourself, and check them. Send back anything that fails.
5. Confirm `approvals/<date>-ad-batch.md` exists, finish the ledger record, and tell the owner where the sheet is and what it asks for.

Never launch, schedule or fund an ad.

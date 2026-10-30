# The work ledger

The ledger is the shared record of every real job: who was asked, what the brief said, what happened, what was produced, and how it ended. It means nobody has to scroll an agent's terminal to find out what happened yesterday.

* **Records:** `work/<date>-<title>-<id>.md`, one readable Markdown file per job.
* **Journal:** `work/.ledger/events.jsonl`, one line per change, append only.
* **State:** `work/.ledger/jobs/<id>.json`.

`work/` is not committed to git.

## Commands

```
id=$(scripts/ledger start --key 2026-11-02-holiday-batch --agent ads \
      --title "Holiday stills batch" --brief work/briefs/2026-11-02-holiday-batch.md)
scripts/ledger event "$id" --state running --note "Building stills."
scripts/ledger artifact "$id" ads/batches/2026-11-04/sheet.jpg --note "contact sheet"
scripts/ledger event "$id" --state waiting_approval --note "Approval file written."
scripts/ledger finish "$id" --status done --outcome "Six stills passed the critic gate; owner approved."
scripts/ledger recent --limit 10
scripts/ledger show "$id"
```

States: `dispatched`, `running`, `blocked`, `waiting_approval`, then one of `done`, `failed`, `abandoned`.

## The rules

1. **What gets a record:** delegated work, research that reaches a conclusion, anything that makes files or media, anything that changes something outside. Quick questions and status checks do not.
2. **The dispatcher owns the record.** HQ opens it *before* prompting a specialist, puts the job id in the brief, records the artifacts and closes it *after* inspecting the result. A specialist may add events and artifacts, but correctness never depends on it remembering.
3. **Everything ends.** A crash, a rate limit, or a job the owner cancels still gets `finish --status failed` or `abandoned` with the reason.
4. **One record per assignment,** including retries. A retry is an event, not a new job.
5. **`--key` makes `start` safe to repeat.** Use something stable like the date plus a slug. Running `start` twice with the same key returns the same job.
6. **No secrets.** The ledger refuses text that looks like a password, token or API key.
7. **Session start:** HQ runs `scripts/ledger recent` before saying what anyone last did.

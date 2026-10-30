# The standing loops

A loop is a job that repeats on a rhythm with the same steps every time. Each one ends at the owner's approval, never at publishing.

```
research → concepts → build → critic gate → approval file → owner says yes → owner acts
```

The numbers that come back in `data/` feed the next round of research.

| Loop | Rhythm | Command | Who | Ends at |
| --- | --- | --- | --- | --- |
| Research to concepts | when a new angle or product needs it | ask HQ | ads-research, then ads | concepts saved, owner picks |
| Weekly ad batch | once a week, fixed launch day | `/batch` then `/rate` | ads | `approvals/<date>-ad-batch.md` |
| Social week | once a week | `/social-week` | social | `approvals/<date>-social-week.md` |
| Inbox triage | daily or twice daily | `/triage` | email | drafts waiting in the mail tool |
| Store numbers | daily | ask HQ, or schedule | shopify | `data/shopify.json` refreshed |
| Friday report | Friday | `/friday-report` | HQ | `reports/<date>-weekly.md` |
| Status | any time | `/status` | HQ | a report to the owner |

## Research to concepts

1. HQ gives ads-research (the Research tab in the Ads workspace) a bounded research objective and a stop condition ("find 10 hooks from reviews that mention titanium; stop at 10").
2. Ads research writes findings to `ads/research/` with sources.
3. HQ reads them and picks what is useful.
4. HQ hands the pick to ads and asks for concepts.
5. HQ returns the concepts to the owner with the file path, and asks before anything is built further, published or launched.

## Weekly ad batch

See `ads/docs/weekly-batch.md`. Plan from the numbers, one testing focus, build stills with zero credits, critic gate, diversity rating, approval file. The kill switch for a losing ad is a proposal, never an action.

## Social week

One post per pillar, written to `social/queue/`, calendar updated, approval file written. The owner posts.

## Inbox triage

Sort, draft, summarize. Drafts only. Wholesale and press go to the owner untouched.

## Friday report

Numbers, what worked, what did not, decisions needed. A file, not an email.

## Making a loop run on a schedule

Start by hand until the steps are stable. Then the owner can schedule the prompt with cron on the WSL machine, for example every Friday at 3pm:

```
0 15 * * 5 cd ~/emma-hq && scripts/hq prompt hq "/friday-report"
```

Only schedule loops that end at an approval file. Never schedule anything that sends, posts or spends.

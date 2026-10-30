# The layout: workspaces and folders

Every area of the business has one herdr workspace, and that workspace is rooted at the area's own folder. The workspace name matches the folder, so what you see in herdr is what you see on disk. `scripts/hq start` builds this layout, and `./setup.sh` creates every folder below on day one.

| herdr workspace / tab | Folder | Agent | What it writes |
| --- | --- | --- | --- |
| HQ | `./` (repository root) | `hq` | `work/briefs/`, the ledger in `work/`, `approvals/`, `reports/`, `memory/` |
| Ads | `ads/` | `ads` | `ads/batches/` (weekly stills and contact sheets), `approvals/` |
| Ads / Research | `ads/research/` | `ads-research` | `ads/research/` (angles, customer words, competitor notes, with sources) |
| Social | `social/` | `social` | `social/queue/`, `social/posted/`, `social/calendar.md` |
| Shopify | `shopify/` | `shopify` | `shopify/snapshots/`, `data/shopify.json` |
| Email | `email/` | `email` | `email/triage/`, `email/drafts/` |

Shared folders every agent may read: `memory/` (facts and rules), `data/` (numbers for the dashboard), `ads/assets/photos/`, `ads/assets/logo/` and `ads/assets/fonts/` (the real product photos, logo and brand fonts the ad stills are built from).

On tmux there are no workspaces, so each agent gets one window with the agent's name: `hq`, `ads`, `ads-research`, `social`, `shopify`, `email`, each started in the folder above.

## The tree

```
emma-hq/                  HQ workspace, agent hq
├── CLAUDE.md             HQ's job description and the rules for everyone
├── memory/               long term facts and rules (private)
├── work/
│   └── briefs/           one brief per job, plus the ledger (private)
├── approvals/            decisions waiting on the owner
├── data/                 numbers the dashboard reads (private)
├── reports/              the Friday report and others (private)
├── ads/                  Ads workspace, agent ads
│   ├── research/         Ads workspace, Research tab, agent ads-research
│   ├── batches/          one folder per weekly batch
│   └── assets/
│       ├── photos/       real product photos
│       ├── logo/
│       └── fonts/
├── social/               Social workspace, agent social
│   ├── queue/            posts waiting for approval or their date
│   └── posted/           what went out, and when
├── shopify/              Shopify workspace, agent shopify
│   └── snapshots/        store checkups
└── email/                Email workspace, agent email
    ├── triage/           inbox sorting notes
    └── drafts/           reply and campaign drafts, never sent
```

## Why Research is a tab, not a workspace

Research and production are one area with two jobs. The `ads` agent turns angles into ad stills; the `ads-research` agent finds those angles in reviews, comments and competitors and writes them to `ads/research/`. Keeping both in the Ads workspace means the person reading Ads sees the whole pipeline in one place, and the research agent cannot wander into production files by accident.

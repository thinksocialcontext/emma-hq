# Critic gate, batch 2026-11-04 (SAMPLE)

Checked by a fresh session against `ads/docs/critic-gate.md`. This is a sample result to show the format.

| Ad | Result | Reason |
| --- | --- | --- |
| b1 | pass | Text readable at phone size, no dashes, claim matches the site wording. |
| b2 | pass | Note readable, layout differs from b1. |
| b3 | pass | Tried list matches the skeptic angle, nothing cut off. |
| b4 | pass | Review card is marked as a sample name. A real batch must quote a real review. |
| b5 | pass | Trial wording is general and points to the store's own terms. |
| b6 | fail | Note text is too long and runs small at phone size. Shorten to one line and rebuild. |

Overall: 5 of 6 pass. b6 goes back for a fix.

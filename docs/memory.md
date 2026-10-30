# How Emma HQ remembers

Agents forget everything when a session ends. The `memory/` folder is how they remember facts and rules between sessions, and how every agent shares them.

## The shape

* `memory/MEMORY.md` is the **index**. One line per memory: a link and a short summary. Every agent reads it at the start of every session.
* Every other file holds **one fact or one rule**. Small files are easy to find, update and trust.

```
---
name: offers
description: One sentence that says what this memory is, specific enough to decide whether to open it.
type: project
---

The fact or the rule, in plain words. Dates for anything that changes.

**Why:** the reason it matters, or the event that taught it.

**How to apply:** when and how an agent should use it.

Related: [[no-medical-claims]] [[hero-products]]
```

### The four types

| type | holds | example |
| --- | --- | --- |
| `user` | who the owner is and how they like to work | prefers a short morning summary, no jargon |
| `feedback` | a rule the owner gave or a lesson from a mistake | never make medical claims |
| `project` | facts about the business that change over time | current offers, best sellers |
| `reference` | where things are and how tools are set up | brand colors, which email tool |

`[[name]]` links point to other memories by their `name`. Follow them when the task touches that subject.

## When to save

Save a memory when:

* the owner states a preference or a rule ("never post on Sundays")
* the owner corrects an agent (save the correction so it never happens twice)
* a fact about the business is learned or changes (a new offer, a new best seller, a new tool)
* a mistake costs time and has a clear lesson

Do not save: one off task details (those go in the ledger), anything secret, customers' personal details, or guesses.

## How to save

Use `/remember <the fact>`, or by hand:

1. Search `memory/` first. **Update** the existing memory if one covers the subject; do not make a second one.
2. Write the file with frontmatter, the fact, **Why**, **How to apply**, and links.
3. Add or fix its line in `MEMORY.md`.
4. If a memory turns out wrong, fix it or delete it and its index line. A wrong memory is worse than none.

## Where it lives

`./setup.sh` copies the starter memories from `memory-seed/` into `memory/`. After that, `memory/` belongs to the business and is **not committed to git** (see `.gitignore`), so private facts never end up in a shared repository. Back it up with the rest of the computer, or commit it to a private repository if the owner wants history.

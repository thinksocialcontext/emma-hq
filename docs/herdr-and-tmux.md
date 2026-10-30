# Running the agents side by side: herdr or tmux

Emma HQ runs five Claude Code agents at once: HQ, ads, social, shopify and email. Something has to hold five terminals and let HQ read and type into the others. The kit supports two options and one script, `scripts/hq`, that works the same on both.

## herdr (recommended)

[herdr](https://herdr.dev) is a terminal workspace manager built for coding agents. It knows when an agent is working, idle, or waiting on a question, and it has commands for reading and prompting agents. It is open source under the Apache 2.0 licence (https://github.com/herdrdev/herdr). `./setup.sh` offers to install it from the official installer:

```
curl -fsSL https://herdr.dev/install.sh | sh
herdr integration install claude     # lets herdr see Claude Code's state
```

Then open a terminal, run `herdr`, and inside it run `scripts/hq start`. HQ gets a workspace called "Emma HQ" with a tab per agent.

## tmux (fallback, always works)

tmux comes with Ubuntu. If herdr is not installed, `scripts/hq` uses tmux automatically:

```
scripts/hq start      # creates the tmux session "emma-hq", one window per agent
scripts/hq attach     # look at it; Ctrl+b then 0 to 4 switches agents, Ctrl+b then d leaves it running
```

On tmux, agent state is a best guess: `working` if the screen is changing, `blocked` if a question or permission dialog is showing, `idle` otherwise.

To force one or the other: `HQ_BACKEND=tmux scripts/hq start`.

## The verbs

| Command | Does |
| --- | --- |
| `scripts/hq start` | open all five agents (safe to run twice) |
| `scripts/hq list` | each agent and its state |
| `scripts/hq read ads 80` | the last 80 lines of the ads agent's screen |
| `scripts/hq prompt ads "..."` | type a task and press Enter (refuses if a dialog or unsent text is showing) |
| `scripts/hq wait ads 600` | wait up to 600 seconds for ads to finish or ask something |
| `scripts/hq attach` / `stop` | tmux only |

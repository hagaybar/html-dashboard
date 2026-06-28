---
name: html-dashboard
description: Generate visually compelling HTML — interactive dashboards with a live browser↔Claude link, or static reports/diagrams — from a pattern library. Use when the user wants to track a multi-step or long-running workflow, monitor live progress, understand a flow or architecture ("how does X work?"), compare options or review a decision, or present complex/tabular data clearly. Triggers: dashboard, diagram, flowchart, visualize, "show me", "lay this out", track progress, compare options.
---

# HTML Dashboard

Turn an idea into a styled HTML artifact from a library of patterns. Two modes:

- **Static** — pick a pattern, fill it, write the file into the current repo,
  open it. No server. For reports, diagrams, comparisons, one-shot data views.
- **Interactive** — same, plus a localhost server giving a live two-way
  browser↔Claude link (the operator pings; you reply inline).

## When to suggest it

Offer a dashboard/diagram (don't wait to be asked) when the user wants to:
track a multi-step or long workflow, monitor live progress, understand a flow
or architecture, compare options, or present complex/tabular data. **Suggest,
then let the user accept.** Never start a server unprompted.

## Choosing a pattern

Read `patterns/INDEX.md` and match intent → pattern. The catalog covers
diagrams (flowchart/sequence/architecture/state, via Mermaid), dashboards
(status-cards/progress), data (table/metrics/chart), comparison
(side-by-side/decision-matrix), and narrative (stepper).

## Workflow — static

1. Copy the chosen pattern to the repo as `<topic>.html` (default location:
   `docs/dashboards/`, or the dir that fits — see `references/building-html.md`).
2. Fill every `<!-- SLOT: ... -->`. Remove the comms `<script>` if present.
3. Open it (`python3 -m http.server` in that dir, or a `file://` path).
4. Offer to commit it (it's a per-repo, committable artifact).

## Workflow — interactive

1. Copy the chosen interactive pattern to the repo as `<topic>-dash.html`
   (the `-dash.html` suffix is what the server auto-discovers).
2. Fill slots; keep the `/assets/comms.js` + `/assets/base.css` links.
3. Start the server (it auto-picks a free port if 8765 is taken):
   ```bash
   DASH_DIR=docs/dashboards DASH_PORT=8765 python3 ~/.claude/skills/html-dashboard/engine/server.py
   ```
   Tell the user the URL printed on stderr.
4. Run the watcher to receive the operator's pings:
   ```bash
   DASH_SERVER=http://localhost:<port> bash ~/.claude/skills/html-dashboard/engine/watch.sh
   ```
5. On a ping, act, then reply inline:
   ```bash
   DASH_SERVER=http://localhost:<port> bash ~/.claude/skills/html-dashboard/engine/reply.sh <elementId|-> <info|success|warn|error|question> "text"
   ```
   Relaunch the watcher for the next ping.

## Safety

- The server redacts JWTs and API keys from every POST before persisting.
- Never write real operator-supplied identifiers into committed HTML. The
  redactor is a safety net, not a license.
- Localhost-bind only.

## Adding a pattern

Drop a new `<name>.html` in `patterns/` (follow an existing exemplar) and add a
row to `patterns/INDEX.md`. No code changes needed.

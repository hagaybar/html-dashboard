# html-dashboard

A [Claude Code](https://claude.com/claude-code) skill that turns an idea into a
styled HTML artifact from a library of patterns — interactive dashboards with a
live browser↔Claude link, or static reports and diagrams.

Two modes:

- **Static** — pick a pattern, fill it, write the file, open it. No server. For
  reports, diagrams, comparisons, one-shot data views.
- **Interactive** — same, plus a localhost server giving a live two-way
  browser↔Claude link (the operator pings an element in the page; Claude replies
  inline).

## Install

```bash
git clone https://github.com/hagaybar/html-dashboard.git
cd html-dashboard
./install.sh
```

This symlinks the skill into `~/.claude/skills/html-dashboard` and the
`/dashboard` command into `~/.claude/commands/`. Re-run after a `git pull` to
update (symlinks track the repo). Use `COPY=1 ./install.sh` to copy instead of
symlink. Restart Claude Code afterward.

Prefer not to run a script? Symlink (or copy) this directory to
`~/.claude/skills/html-dashboard` and `commands/dashboard.md` to
`~/.claude/commands/dashboard.md` yourself.

## Use

Once installed, invoke it in Claude Code with the `/dashboard` command:

```
/dashboard how does the auth flow work?
/dashboard track the migration progress
```

…or just ask in natural language ("show me…", "lay this out", "compare these
options") — the skill triggers on those intents.

## Requirements

- **[Claude Code](https://claude.com/claude-code)** — this is a Claude Code
  skill. It's loaded from `~/.claude/skills/` and invoked with the `/dashboard`
  command or natural language; it does nothing on its own without Claude Code.
- **Static** mode: a browser. Diagrams use vendored [Mermaid](https://mermaid.js.org/)
  (with a CDN fallback for standalone files).
- **Interactive** mode: **Python 3** (standard library only) for the engine
  server, plus `curl` and `jq` for the watcher/reply helper scripts.

## Layout

```
SKILL.md              # skill entry point (workflow + when to suggest)
commands/dashboard.md # the /dashboard slash command
engine/               # localhost server, watch/reply scripts, vendored assets
patterns/             # HTML pattern library + INDEX.md
references/            # build guidance
tests/                # pytest smoke tests for the engine
```

Run the tests with `pytest tests/`.

## Safety

The interactive server binds to localhost only and redacts JWTs and
`*_API_KEY` / `apikey …` values from posted state before persisting them as a
safety net. Don't put real identifiers into committed HTML — use synthetic
placeholders.

## License

MIT — see [LICENSE](LICENSE). Vendors Mermaid (MIT).

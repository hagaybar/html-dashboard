# Building HTML for this skill

## Style

- Default to the dark theme in `engine/assets/base.css`. Interactive pages
  `<link>` it from `/assets/base.css`; standalone static pages inline the rules
  they use (keeps the file portable).
- Keep it clean and information-dense. Use the `frontend-design` skill when a
  page needs more than the base patterns give.

## File naming & location

- Interactive dashboards: `<topic>-dash.html` (the `-dash.html` suffix is what
  the engine auto-discovers via `DASH_DIR`).
- Static pages: `<topic>.html`.
- Default repo location `docs/dashboards/`; use the dir that fits the repo's
  conventions.

## The comms wiring (interactive only)

Include exactly these two lines and the `window.Dash` API from
`/assets/comms.js`:
```html
<link rel="stylesheet" href="/assets/base.css" />
<script src="/assets/comms.js"></script>
```
`Dash.loadState()`, `Dash.saveState(obj)`, `Dash.ping(id, payload)`,
`Dash.onReplies(cb, intervalMs)`. State falls back to `localStorage` when no
server is running, so the page degrades gracefully.

## Diagrams

Diagram patterns load `/assets/mermaid.min.js` (vendored) and fall back to the
Mermaid CDN for standalone files. Write the diagram source in the `MERMAID`
slot; Mermaid supports flowchart, sequenceDiagram, stateDiagram-v2, classDiagram,
erDiagram, gantt.

## Security

Never put real identifiers (user IDs, record IDs, vendor codes, emails) in a
committed HTML file. Use synthetic placeholders. The server redacts JWTs and
`*_API_KEY` / `apikey …` values from posted state as a safety net.

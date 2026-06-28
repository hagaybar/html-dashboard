# Pattern library index

Each pattern is a self-contained HTML scaffold with `<!-- SLOT: ... -->`
markers and a header comment. To use one: copy it to the target repo as
`<topic>-dash.html` (interactive) or `<topic>.html` (static), fill the slots,
and follow `references/building-html.md`.

| Pattern file | Category | Mode | When to use |
|--------------|----------|------|-------------|
| `diagram-flowchart.html` | Diagram | static | Processes, request lifecycles ("how does X work?") |
| `diagram-sequence.html` | Diagram | static | Ordered calls between actors (client↔server↔API) |
| `diagram-architecture.html` | Diagram | static | Module/component relationships |
| `diagram-state.html` | Diagram | static | Lifecycle / state machines |
| `dashboard-status-cards.html` | Dashboard | interactive | Track a multi-step workflow; two-way Claude link |
| `dashboard-progress.html` | Dashboard | static/interactive | Progress + timeline of a rollout |
| `data-table.html` | Data | static | Sortable/filterable tabular results |
| `data-metrics.html` | Data | static | Headline KPI tiles |
| `data-chart.html` | Data | static | Simple bar/line trend |
| `compare-side-by-side.html` | Comparison | static | Option A vs B, before/after |
| `compare-decision-matrix.html` | Comparison | static | Weighted option scoring |
| `narrative-stepper.html` | Narrative | static | Guided multi-step explanation |

Diagram patterns load vendored Mermaid from `/assets/mermaid.min.js` when
served by the engine, with a CDN `<script>` fallback for standalone files.

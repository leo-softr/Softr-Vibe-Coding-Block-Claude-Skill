# Softr Vibe Coding Block — Claude Skill

> Turn Claude into a Softr Vibe Coding expert — generate production-ready React blocks (TSX/JSX) with polished UI, correct data fetching, and all 14 Softr data sources supported out of the box.

![Claude Code Skill](https://img.shields.io/badge/Claude_Code-Skill-blue)
![Version](https://img.shields.io/npm/v/softr-vibe-coding?label=version&color=green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

> **UNOFFICIAL** — This is a community-maintained Claude skill. It is not affiliated with, endorsed by, or officially supported by Softr. Use as-is.

---

## TL;DR

This Claude skill teaches Claude Code how to generate complete, polished Softr Vibe Coding blocks as `.tsx` / `.jsx` files (the current platform compiles TypeScript with modern syntax — verified live August 2026). It includes:

- **Complete Vibe Coding API reference** — `useRecords`, `q.select()`, mutations, uploads, metrics, charts, editable settings, `useProxyFetch` for REST APIs
- **Editable settings deep-dive** — full hook catalog including verified-undocumented capabilities (`useLongTextSetting`, the `navigation` array-schema type), settings-first design doctrine so clients edit copy/images/links in Content → Settings without re-prompting
- **Static marketing blocks** — heroes, landing headers, pricing tables, footers: editorial baseline, full-bleed layouts, full-viewport sizing, block-owned fixed headers with scroll-condensing treatment
- **All 14 Softr data sources** — Airtable, Softr Database, Google Sheets, HubSpot, Notion, Coda, monday.com, SmartSuite, ClickUp, Xano, Supabase, BigQuery, SQL Database, and REST API — each with field mapping, rate limits, and gotchas
- **Helper blocks & cross-block patterns** — Invisible helper blocks for multi-table access via `window` globals + `CustomEvent`, `useWindowData` hook, breadcrumb navigation, saved views architecture
- **Advanced integrations** — Shadow DOM CSS isolation for third-party libraries (Leaflet, Mapbox, TinyMCE, Quill, FullCalendar)
- **Native shell styling** — re-skin Softr's native top bar, **footer**, nav, dropdowns, and **page background** via global Custom Code CSS (stable selectors vs. hashed classes, floating "island" header/footer, the dropdown grid fix, the multi-layer page-background stacking, restyle-vs-replace) — distinct from blocks
- **UI/UX design guidelines** — 26 sections covering visual hierarchy, color, typography, spacing, motion design, accessibility, responsive patterns, and an AI slop anti-pattern checklist
- **Self-validation** — Claude checks Softr platform compatibility and house conventions (inline hook options, correct payload shapes, correct imports, container wrappers or a deliberate full-bleed layout, `getFieldValue()` wrapping, hooks ordering) before delivering code
- **Premium visual baseline** — every app-UI block (dashboards, lists, forms, detail pages) ships polished from v1: gradient backgrounds, card elevation, loading skeletons, empty states, error states; static marketing blocks use the editorial baseline instead
- **Debug utilities** — Field Inspector, API Response Inspector, and User Inspector blocks for diagnosing data source and permissions issues
- **Softr MCP integration** — when the [official Softr MCP server](https://docs.softr.io/mcp/overview) is installed (`claude mcp add --transport http softr https://mcp.softr.io/mcp`), Claude reads Softr DB schema, field IDs, and dropdown option UUIDs directly, browses connected Airtable / Google Sheets / Notion / Supabase integrations down to field level, and can even create and deploy Vibe Coding blocks straight into your app — no more pasting `tablespace-with-tables` JSON or copy-pasting code into Studio. See `references/softr-mcp.md`.

---

## Installation

### Recommended: One-line install with auto-updates

```bash
npx softr-vibe-coding@latest init
```

This installs the skill into `~/.claude/skills/softr-vibe-coding/` and adds a `SessionStart` hook to `~/.claude/settings.json` so the skill auto-updates to the latest published version on every Claude Code session. No manual `git pull` needed.

Requires Node.js 18+.

### Manual alternatives

<details>
<summary>Clone the repo directly into your Claude skills directory</summary>

```bash
git clone https://github.com/leo-softr/Softr-Vibe-Coding-Block-Claude-Skill.git ~/.claude/skills/softr-vibe-coding
```

</details>

<details>
<summary>Download the latest tarball</summary>

```bash
mkdir -p ~/.claude/skills/softr-vibe-coding
curl -L https://github.com/leo-softr/Softr-Vibe-Coding-Block-Claude-Skill/archive/refs/heads/main.tar.gz | \
  tar -xz --strip-components=1 -C ~/.claude/skills/softr-vibe-coding
```

</details>

<details>
<summary>Manual download (ZIP)</summary>

1. Download this repository as a ZIP from the green **Code** button above
2. Extract the ZIP
3. Rename the extracted folder to `softr-vibe-coding` and place it in `~/.claude/skills/`

</details>

### Verify installation

Start a new Claude Code session and ask:

```
What skills are available?
```

You should see `softr-vibe-coding` in the list. Or invoke it directly:

```
Build me a Softr Vibe Coding block that shows a team directory with cards
```

---

## Companion skill — `building-design-md`

This skill is **Step 2** of a two-skill brand-to-blocks pipeline:

```
New client → building-design-md (brand → DESIGN.md) → softr-vibe-coding (DESIGN.md → blocks) → shipped Softr app
```

The upstream skill is [`building-design-md`](https://github.com/leo-softr/design-md-extractor-skill), which extracts a brand foundation (colors, typography, voice) from a website URL or brand guide into a portable `DESIGN.md` file. When that file exists in your project folder, this skill picks it up automatically and applies the brand tokens throughout every block it generates — no re-asking about colors or fonts.

**Install both for the full workflow:**

```bash
npx building-design-md@latest init
npx softr-vibe-coding@latest init
```

Both auto-update on every Claude Code session. Skip the first one if you only want default Softr styling.

---

## Updating

**If you used the recommended `npx ... init` install**, updates are automatic — the SessionStart hook pulls the latest published version on every Claude Code session, so you're always at most one session behind the latest release.

**Manual installs** (git clone / tarball / ZIP):

```bash
cd ~/.claude/skills/softr-vibe-coding
git pull origin main
```

Or re-run the tarball install — the extraction overwrites the existing files.

---

## Usage

The skill activates automatically when you mention Softr, Vibe Coding, or ask to build a custom UI component for a Softr app. You can also invoke it directly with `/softr-vibe-coding`.

### Example prompts

**Simple card grid:**
```
Build a team directory with cards showing name, role, and photo from Airtable
```

**REST API integration:**
```
Create a block that fetches events from the Luma API and lets me select one to send a webhook
```

**Dashboard with metrics:**
```
Build a KPI dashboard showing revenue, active users, and churn rate from our Softr Database
```

**Form with mutations:**
```
Create a contact form that creates records in our Airtable Contacts table
```

### What the skill does

1. **Asks only what it needs** — data source type and field IDs. Everything else (folder, colors, filename) uses smart defaults.
2. **Loads the relevant guides** — reads the specific data source guide (Airtable, REST API, etc.) and reference files (helper blocks, Shadow DOM) as needed.
3. **Generates a complete block file** (`.tsx` preferred) — production-ready, visually polished, with loading/error/empty states. Never delivers code inline (prevents JSX character corruption).
4. **Self-validates** — runs a platform-compatibility checklist (`getFieldValue()` wrapping, hooks ordering, payload shapes, inline hook options) before delivering code.

---

## What's Included

```
softr-vibe-coding/
├── SKILL.md                          # Main skill
│                                     # Workflow, code structure, visual baseline,
│                                     # components, settings, 21 hard constraints
│
├── ui-ux-guidelines.md               # Design reference
│                                     # 26 sections: hierarchy, color, typography,
│                                     # spacing, motion, accessibility, AI slop checklist
│
├── references/                       # Advanced patterns (loaded on demand)
│   ├── helper-blocks.md              # Cross-block communication
│   │                                 # Invisible helper blocks, window globals,
│   │                                 # CustomEvent, useWindowData hook, breadcrumbs,
│   │                                 # saved views, companion field helpers
│   ├── airtable-automations.md       # Airtable automation scripting
│   │                                 # "Run a script" automation action vs.
│   │                                 # Scripting Extension, cross-table cascades,
│   │                                 # batch update gotchas, field-ID discipline,
│   │                                 # Airtable formulas
│   ├── softr-mcp.md                  # Official Softr MCP server — vibe coding block
│   │                                 # tools (create/edit/version/deploy), integrations
│   │                                 # browsing (Airtable/Sheets/Notion/Supabase),
│   │                                 # Softr DB schema + record tools, auth, permissions
│   ├── advanced-integrations.md      # Shadow DOM CSS isolation
│   │                                 # Leaflet, Mapbox, TinyMCE, Quill, FullCalendar
│   ├── native-chrome-styling.md      # Restyle Softr's native shell (header, footer,
│   │                                 # nav, dropdowns, page background) via global
│   │                                 # Custom Code CSS — stable selectors, floating
│   │                                 # islands, dropdown grid fix, multi-layer page-bg
│   ├── native-block-filters.md       # Dynamic date / URL-param filters + custom filter
│   │                                 # controls on native List/Grid blocks — wide-range
│   │                                 # sentinel, inject into filter row, survive re-renders
│   ├── anti-patterns.md              # Categorized violation catalog
│   │                                 # Data access, mutations, hooks, layout,
│   │                                 # permissions, editable settings, helper blocks
│   ├── common-patterns.md            # Small reusable patterns
│   │                                 # localStorage cross-page state, clipboard copy,
│   │                                 # navigation blocker, scroll-condensing header,
│   │                                 # auth-aware CTA, image masks, blobs, dot lists
│   ├── editable-settings.md          # Settings deep-dive: full hook catalog incl.
│   │                                 # verified-undocumented useLongTextSetting +
│   │                                 # "navigation" array-schema type, granularity
│   │                                 # doctrine, naming, rename-resets gotcha
│   ├── static-blocks.md              # Static marketing archetype: heroes, landing
│   │                                 # headers, pricing, footers — workflow deltas,
│   │                                 # editorial baseline, full-bleed + full-viewport,
│   │                                 # block-owned header, section anchors
│   └── quick-reference.md            # Syntax cheat sheet
│                                     # Imports, hook signatures, mutation shapes,
│                                     # field mapping, component skeleton
│
├── tools/                            # Bundled CLI scripts (run, not read)
│   ├── get-airtable-base             # Full Airtable base schema export (bash + jq)
│   └── get-softr-database.py         # Full Softr DB schema export (Python stdlib)
│
└── datasources/                      # Data source guides (loaded on demand)
    ├── overview.md                   # Comparison matrix, selection guide
    ├── shared-patterns.md            # Index → multi-datasource, reading, writing, fields
    ├── multi-datasource.md           # Several data sources in ONE block: datasource.define(),
    │                                 #   the from: parameter, getting the datasource UUIDs
    ├── reading.md                    # useRecords, filtering, sorting, pagination,
    │                                 # metrics, charts, current user
    ├── writing.md                    # Mutations, sequential write queues, uploads,
    │                                 # linked record format, cross-table writes
    ├── fields.md                     # getFieldValue(), field type shapes, record
    │                                 # structure, debug utilities
    ├── rest-api.md                   # useProxyFetch + useQuery (full docs)
    ├── softr-database.md             # Native DB — field IDs, no rate limits
    ├── airtable.md                   # Column names, PAT vs OAuth, rate limits
    ├── google-sheets.md              # Text formatting, 50-100 user cap
    ├── hubspot.md                    # CRM objects, Sensitive Data Scopes
    ├── notion.md                     # Database pages only, Relation workarounds
    ├── coda.md                       # API token auth, limitations
    ├── monday.md                     # API token, Connected Boards
    ├── smartsuite.md                 # OAuth, linked records
    ├── clickup.md                    # Extensive fields, rate limit tiers
    ├── xano.md                       # Database Connector, IP whitelisting
    ├── supabase.md                   # Session Pooler, pool size, RLS
    ├── bigquery.md                   # Read-only, custom SQL
    └── sql-database.md              # 4 SQL engines, ports, IP whitelisting
```

### How context loading works

Only `SKILL.md` loads into Claude's context when the skill triggers. The data source guides, reference files, and UI/UX guidelines load **on demand** — Claude reads only the files relevant to your specific block. This keeps context lean even with 26 files totaling 6,500+ lines.

---

## Supported Data Sources

| Data Source | Approach | Plan |
|---|---|---|
| Softr Databases | `useRecords` + `q.select()` | All plans |
| Airtable | `useRecords` + `q.select()` | Basic+ |
| Google Sheets | `useRecords` + `q.select()` | Basic+ |
| HubSpot | `useRecords` + `q.select()` | Business+ |
| Notion | `useRecords` + `q.select()` | Basic+ |
| Coda | `useRecords` + `q.select()` | Basic+ |
| monday.com | `useRecords` + `q.select()` | Professional+ |
| SmartSuite | `useRecords` + `q.select()` | Professional+ |
| ClickUp | `useRecords` + `q.select()` | Professional+ |
| Xano | `useRecords` + `q.select()` | Professional+ |
| Supabase | `useRecords` + `q.select()` | Professional+ |
| BigQuery | `useRecords` + `q.select()` | Business+ |
| SQL Database | `useRecords` + `q.select()` | Business+ |
| REST API | `useProxyFetch` + `useQuery` | Business+ |

---

## Key Softr Platform Constraints

The skill enforces these automatically, but good to know (verified live against the platform, August 2026):

- Modern TypeScript compiles — optional chaining, nullish coalescing, arrows, `const`, generics are all fine (the old `var`-only / no-`?.` rules are retired)
- Data hook options must be **inline object literals** — `useRecords(opts)` with a variable or wrapper fails to compile
- Create payloads are **flat**; update payloads are `{ recordId, fields: {...} }` — asymmetric by design
- `mutateAsync` is fully supported — it's the tool for sequential multi-row saves
- SELECT fields write by option **label string**; linked records write as arrays of record-id strings
- Every code recompile resets the block's auto-registered Actions to default permissions — tighten permissions after the last redeploy
- No `import React from 'react'` — use named imports (`import { useState } from "react"`)
- Must use `export default function Block()`
- Wrap layout in `<div className="container py-0"><div className="content">` for app/content blocks (house convention for width alignment with native blocks) — the platform default is actually full width, so full-bleed marketing blocks (heroes, banners, footers) legitimately omit the wrappers and own their gutters
- Only ONE `useRecords` call per **datasource** — but a block can connect to several sources; declare them with `datasource.define()` and pass `from:` on every hook
- `fetchNextPage` never in the render body (infinite loop) — call it from an event handler (Load More `onClick`) or a guarded `useEffect`
- All hooks declared before any conditional `return` — React error #310
- Every field value rendered in JSX must pass through `getFieldValue()`
- Mutations use `recordId` (not `id`) and always call `refetch()` in `onSuccess`
- REST API data sources use `useProxyFetch`, NOT `useRecords`
- Use relative paths in navigation, never hardcoded domains

---

## Disclaimer

This is an **UNOFFICIAL**, community-maintained Claude skill. It is provided **as-is** with no warranty.

- Not affiliated with, endorsed by, or officially supported by [Softr](https://www.softr.io)
- Not affiliated with or endorsed by [Anthropic](https://www.anthropic.com)
- The Softr Vibe Coding API may change — if something breaks, check the [official Softr docs](https://docs.softr.io/vibe-coding-developer-guide)
- This skill is based on publicly available documentation and community testing

---

## Contributing

Pull requests are what make open source great, and we appreciate the spirit behind them. That said, this skill is maintained for a specific personal workflow, so PRs won't be merged here. We highly recommend forking this repo and making it your own — customize it for your team, your data sources, your design system. That's the beauty of open source.

---

## References

- [Softr Vibe Coding Developer Guide](https://docs.softr.io/vibe-coding-developer-guide) — Official Softr Vibe Coding documentation
- [Softr Data Sources](https://docs.softr.io/data-sources) — Official Softr data source documentation
- [Impeccable](https://github.com/pbakaus/impeccable) — Design patterns and UI/UX anti-pattern principles by Paul Bakaus (referenced in the UI/UX guidelines)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills) — How Claude Code skills work

---

## License

[MIT](LICENSE)

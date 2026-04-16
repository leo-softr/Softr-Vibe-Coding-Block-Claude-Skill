# Softr Vibe Coding Block — Claude Skill

> Turn Claude into a Softr Vibe Coding expert — generate production-ready JSX blocks with polished UI, correct data fetching, and all 14 Softr data sources supported out of the box.

![Claude Code Skill](https://img.shields.io/badge/Claude_Code-Skill-blue)
![Version](https://img.shields.io/badge/version-1.1.0-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

> **UNOFFICIAL** — This is a community-maintained Claude skill. It is not affiliated with, endorsed by, or officially supported by Softr. Use as-is.

---

## TL;DR

This Claude skill teaches Claude Code how to generate complete, polished Softr Vibe Coding blocks as `.jsx` files. It includes:

- **Complete Vibe Coding API reference** — `useRecords`, `q.select()`, mutations, uploads, metrics, charts, editable settings, `useProxyFetch` for REST APIs
- **All 14 Softr data sources** — Airtable, Softr Database, Google Sheets, HubSpot, Notion, Coda, monday.com, SmartSuite, ClickUp, Xano, Supabase, BigQuery, SQL Database, and REST API — each with field mapping, rate limits, and gotchas
- **Helper blocks & cross-block patterns** — Invisible helper blocks for multi-table access via `window` globals + `CustomEvent`, `useWindowData` hook, breadcrumb navigation, saved views architecture
- **Advanced integrations** — Shadow DOM CSS isolation for third-party libraries (Leaflet, Mapbox, TinyMCE, Quill, FullCalendar)
- **UI/UX design guidelines** — 26 sections covering visual hierarchy, color, typography, spacing, motion design, accessibility, responsive patterns, and an AI slop anti-pattern checklist
- **Self-validation** — Claude checks for Softr bundler compatibility (no optional chaining, correct imports, container wrappers, `getFieldValue()` wrapping, hooks ordering) before delivering code
- **Premium visual baseline** — Every block ships polished from v1: gradient backgrounds, card elevation, loading skeletons, empty states, error states
- **Debug utilities** — Field Inspector, API Response Inspector, and User Inspector blocks for diagnosing data source and permissions issues

---

## Installation

### Option 1: Clone and copy (recommended)

```bash
# Clone the repo
git clone https://github.com/leo-softr/Softr-Vibe-Coding-Block-Claude-Skill.git

# Copy the skill to your Claude skills directory
cp -r Softr-Vibe-Coding-Block-Claude-Skill/softr-vibe-coding ~/.claude/skills/softr-vibe-coding
```

### Option 2: Download just the skill folder

```bash
# Create the skill directory
mkdir -p ~/.claude/skills/softr-vibe-coding

# Download the skill files
curl -L https://github.com/leo-softr/Softr-Vibe-Coding-Block-Claude-Skill/archive/refs/heads/main.tar.gz | \
  tar -xz --strip-components=1 -C /tmp/softr-skill && \
  cp -r /tmp/softr-skill/softr-vibe-coding/* ~/.claude/skills/softr-vibe-coding/ && \
  rm -rf /tmp/softr-skill
```

### Option 3: Manual download

1. Download this repository as a ZIP from the green **Code** button above
2. Extract the ZIP
3. Copy the `softr-vibe-coding/` folder to `~/.claude/skills/`

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

## Updating

To update the skill to the latest version:

```bash
# If you cloned the repo
cd Softr-Vibe-Coding-Block-Claude-Skill
git pull origin main
cp -r softr-vibe-coding/* ~/.claude/skills/softr-vibe-coding/
```

Or re-run any of the installation options above — they overwrite the existing files.

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
3. **Generates a complete `.jsx` file** — production-ready, visually polished, with loading/error/empty states. Never delivers code inline (prevents JSX character corruption).
4. **Self-validates** — checks 13 items including Softr bundler compatibility, `getFieldValue()` wrapping, hooks ordering, and mutation patterns before delivering code.

---

## What's Included

```
softr-vibe-coding/
├── SKILL.md                          # Main skill (330 lines)
│                                     # Workflow, code structure, visual baseline,
│                                     # components, settings, 20 hard constraints
│
├── ui-ux-guidelines.md               # Design reference (746 lines)
│                                     # 26 sections: hierarchy, color, typography,
│                                     # spacing, motion, accessibility, AI slop checklist
│
├── references/                       # Advanced patterns (loaded on demand)
│   ├── helper-blocks.md              # Cross-block communication (327 lines)
│   │                                 # Invisible helper blocks, window globals,
│   │                                 # CustomEvent, useWindowData hook, breadcrumbs,
│   │                                 # saved views, companion field helpers
│   ├── advanced-integrations.md      # Shadow DOM CSS isolation (69 lines)
│   │                                 # Leaflet, Mapbox, TinyMCE, Quill, FullCalendar
│   ├── anti-patterns.md              # Categorized violation catalog (69 lines)
│   │                                 # Data access, mutations, hooks, layout,
│   │                                 # permissions, helper blocks
│   └── quick-reference.md            # Syntax cheat sheet (156 lines)
│                                     # Imports, hook signatures, mutation shapes,
│                                     # field mapping, component skeleton
│
└── datasources/                      # Data source guides (loaded on demand)
    ├── overview.md                   # Comparison matrix, selection guide
    ├── shared-patterns.md            # Index → reading, writing, fields
    ├── reading.md                    # useRecords, filtering, sorting, pagination,
    │                                 # metrics, charts, current user (198 lines)
    ├── writing.md                    # Mutations, uploads, linked record format,
    │                                 # cross-table REST API writes (146 lines)
    ├── fields.md                     # getFieldValue(), field type shapes, record
    │                                 # structure, debug utilities (160 lines)
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

Only `SKILL.md` loads into Claude's context when the skill triggers (~330 lines). The data source guides, reference files, and UI/UX guidelines load **on demand** — Claude reads only the files relevant to your specific block. This keeps context lean even with 24 files totaling 3,100+ lines.

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

## Key Softr Bundler Constraints

The skill enforces these automatically, but good to know:

- No optional chaining (`?.`) or nullish coalescing (`??`) — Softr's bundler fails on these
- No `import React from 'react'` — use named imports (`import { useState } from "react"`)
- No arrow functions in JSX callback props — use `function() {}`
- Must use `export default function Block()`
- Must wrap layout in `<div className="container py-6"><div className="content">`
- Only ONE `useRecords` call per block (use helper blocks for multi-table)
- `fetchNextPage` only inside `useEffect` — in render body causes infinite loops
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

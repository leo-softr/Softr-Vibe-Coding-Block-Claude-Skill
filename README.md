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
- **Brand pipeline via dembrandt** — no DESIGN.md in the project? The skill generates one on the spot with [dembrandt](https://github.com/dembrandt/dembrandt) (real-browser design-token extraction over MCP: colors, typography, spacing, components from any site you have permission to analyze), writes it to the project root, and builds every block on those tokens — or keeps the default Softr style if you skip it
- **All 14 Softr data sources** — Airtable, Softr Database, Google Sheets, HubSpot, Notion, Coda, monday.com, SmartSuite, ClickUp, Xano, Supabase, BigQuery, SQL Database, and REST API — each with field mapping, rate limits, and gotchas
- **Helper blocks & cross-block patterns** — Invisible helper blocks for multi-table access via `window` globals + `CustomEvent`, `useWindowData` hook, breadcrumb navigation, saved views architecture
- **Advanced integrations** — Shadow DOM CSS isolation for third-party libraries (Leaflet, Mapbox, TinyMCE, Quill, FullCalendar)
- **Native shell styling** — re-skin Softr's native top bar, **footer**, nav, dropdowns, and **page background** via global Custom Code CSS (stable selectors vs. hashed classes, floating "island" header/footer, the dropdown grid fix, the multi-layer page-background stacking, restyle-vs-replace), plus the **app frame** for apps with Softr's sidebar navigation: the bars' colour as one frame around a paper content sheet, with blocks full-bleed, transparent and laid out by their own width — distinct from blocks
- **UI/UX design guidelines** — 26 sections covering visual hierarchy, color, typography, spacing, motion design, accessibility, responsive patterns, and an AI slop anti-pattern checklist
- **Self-validation** — Claude checks Softr platform compatibility and house conventions (inline hook options, correct payload shapes, correct imports, container wrappers or a deliberate full-bleed layout, `getFieldValue()` wrapping, hooks ordering) before delivering code
- **Premium visual baseline** — every app-UI block (dashboards, lists, forms, detail pages) ships polished from v1: gradient backgrounds, card elevation, loading skeletons, empty states, error states; static marketing blocks use the editorial baseline instead
- **Debug utilities** — Field Inspector, API Response Inspector, and User Inspector blocks for diagnosing data source and permissions issues
- **Softr MCP integration** — when the [official Softr MCP server](https://docs.softr.io/mcp/overview) is installed (`claude mcp add --transport http softr https://mcp.softr.io/mcp`), Claude reads Softr DB schema, field IDs, and dropdown option UUIDs directly, browses connected Airtable / Google Sheets / Notion / Supabase integrations down to field level, creates and deploys Vibe Coding blocks straight into your app, manages full record/table/field/database CRUD (deletes included), and can scaffold applications and build **Softr Workflows** against a 418-node trigger/action catalog. Also covers Softr's **per-application MCP servers** (one per published app, scoped to the app's own permissions). See `references/softr-mcp.md`.

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

## Brand pipeline — dembrandt

This skill is the second half of a brand-to-blocks pipeline:

```
New client → dembrandt (website → DESIGN.md) → softr-vibe-coding (DESIGN.md → blocks) → shipped Softr app
```

The DESIGN.md generator is [dembrandt](https://github.com/dembrandt/dembrandt) (MIT, npm) — a real-browser design-token extractor: point it at a website and it extracts colors, typography, spacing, radii, shadows, and component styles, rendered as a portable `DESIGN.md` in Google's DESIGN.md draft format. When that file exists in your project folder, this skill picks it up automatically and applies the brand tokens throughout every block it generates — no re-asking about colors or fonts. When it doesn't, the skill offers to generate one on the spot through the dembrandt MCP server (writing it to the project root), or proceeds with the default Softr style if you skip branding.

**Install for the full workflow:**

```bash
npx softr-vibe-coding@latest init
claude mcp add --transport stdio dembrandt -- npx -y --package dembrandt@latest dembrandt-mcp
npx -y dembrandt@latest install-browser   # one-time: fetches the Chromium dembrandt drives
```

The skill auto-updates on every Claude Code session (SessionStart hook), and the dembrandt server checks the registry for the newest release on every launch (`@latest`), so both stay current. Skip the two dembrandt lines if you only want default Softr styling. Full operating guide (MCP flow, multi-page crawls, DESIGN.md anatomy, drift QA): `references/dembrandt.md`.

The [`building-design-md`](https://github.com/leo-softr/design-md-extractor-skill) companion skill moved to the same engine: since its v2.0.0 it drives dembrandt too, and layers on what raw extraction can't provide — voice & copy register, resolved font names, logo assets, Softr app-pattern scaffolds, and the `custom-code-header.html` snippet. Run it when a project deserves the full brand foundation; this skill's Step 1 covers the quick raw DESIGN.md. Files from its v1.x (pre-dembrandt) remain fully supported.

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
│                                     # components, settings, 29 hard constraints
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
│   ├── softr-mcp.md                  # Official Softr MCP server — vibe coding block (+ push verification protocol)
│   │                                 # tools (create/edit/version/deploy), integrations
│   │                                 # browsing (Airtable/Sheets/Notion/Supabase),
│   │                                 # Softr DB schema + record tools incl. deletes,
│   │                                 # app management/scaffolding, Workflows suite
│   │                                 # (28 tools, 418-node catalog), per-application
│   │                                 # MCP servers, auth, permissions; what the server
│   │                                 # enforces on block data endpoints, "Preview as"
│   │                                 # role testing, search-replace on 100KB+ blocks
│   │                                 # (Sep 18 2026); Oct 1 2026: tool rename map,
│   │                                 # push verification by sourceSha256, stub tools
│   │                                 # after a resume, update_field/update_table fixes;
│   │                                 # Oct 6 2026: MCP-written FILTER conditions are
│   │                                 # inert (set them in Studio), Workflows tools as
│   │                                 # workflow_*, denied by-id fetch per backend;
│   │                                 # Workflows engine facts (CUSTOM_CODE contract,
│   │                                 # string-array loops, sample-based validation,
│   │                                 # replace_node new ids, re-firing triggers,
│   │                                 # write modes, serialExecution, continueOnError),
│   │                                 # Softr DB row-gating recipe, what a push leaves
│   │                                 # alone, DATETIME create shape, offset paging;
│   │                                 # OAuth grant per ticked workspace, email
│   │                                 # senders, formulas fixed at creation, loop
│   │                                 # counter, workflow time zone and publish state
│   ├── browser-checks.md             # Checking a pushed block in a browser with
│   │                                 # the agent-browser CLI (ask before installing):
│   │                                 # preview cookie, shadow-DOM refs grepped in the
│   │                                 # shell, eval measurements, the records-trigger
│   │                                 # write guard proven before any click, what a
│   │                                 # click sent, screenshots to disk (Oct 1 2026);
│   │                                 # testing Custom Code header CSS (Oct 5 2026)
│   ├── advanced-integrations.md      # Shadow DOM CSS isolation
│   │                                 # Leaflet, Mapbox, TinyMCE, Quill, FullCalendar
│   ├── native-chrome-styling.md      # Restyle Softr's native shell (header, footer,
│   │                                 # nav, dropdowns, page background) via global
│   │                                 # Custom Code CSS — stable selectors, floating
│   │                                 # islands, dropdown grid fix, multi-layer page-bg,
│   │                                 # app frame for sidebar apps (Oct 5 2026)
│   ├── native-block-filters.md       # Dynamic date / URL-param filters + custom filter
│   │                                 # controls on native List/Grid blocks — wide-range
│   │                                 # sentinel, inject into filter row, survive re-renders
│   ├── anti-patterns.md              # Categorized violation catalog
│   │                                 # Data access, mutations, hooks, layout,
│   │                                 # permissions, editable settings, helper blocks
│   ├── common-patterns.md            # Small reusable patterns (localStorage state, clipboard, nav blocker, drag-to-reorder, create → open, clickable row + inner link, keyboard picker, measure the block not the window, clear Softr's sticky bars, a modal above Softr's bars)
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
│   ├── dembrandt.md                  # DESIGN.md generation with dembrandt
│   │                                 # MCP/CLI install (@latest npx + browser step),
│   │                                 # extract → poll → findings → generate → write
│   │                                 # flow, DESIGN.md anatomy, drift QA
│   ├── printing.md                   # Printing from a block: ALWAYS a new window
│   │                                 # with its own document (never window.print()
│   │                                 # on the page, never an in-page print view) —
│   │                                 # escaped HTML builder, pop-up-safe open from
│   │                                 # the click, print once stylesheets, fonts and
│   │                                 # images load, ?print=1 deep link, paper layout
│   │                                 # (Sep 30 2026)
│   ├── quick-reference.md            # Syntax cheat sheet
│   │                                 # Imports, hook signatures, mutation shapes,
│   │                                 # field mapping, component skeleton,
│   │                                 # Softr navigation variables, container queries
│   └── searchable-dropdown.md        # THE dropdown pattern for blocks
│                                     # why native <select> and shadcn <Select> both
│                                     # break in the shadow DOM, composedPath()
│                                     # click-outside, A-Z inside the component,
│                                     # multi-token filter, searchable BY DEFAULT
│                                     # (bare = click-only; searchable={false} only
│                                     # for a fixed enum being set — Sep 10 2026),
│                                     # overflow-clipping ancestors: never clip a cell
│                                     # holding a Combo, clip-aware drop-up + list
│                                     # height, list-only scrolling (Sep 30 2026)
│
├── tools/                            # Bundled CLI scripts (run, not read)
│   ├── get-airtable-base             # Full Airtable base schema export (bash + jq)
│   └── get-softr-database.py         # Full Softr DB schema export (Python stdlib)
│
└── datasources/                      # Data source guides (loaded on demand)
    ├── overview.md                   # Comparison matrix, selection guide
    ├── shared-patterns.md            # Index → multi-datasource, reading, writing, fields
    ├── multi-datasource.md           # Several data sources in ONE block: datasource.define(),
    │                                 #   the from: parameter, getting the datasource UUIDs,
    │                                 #   select: as a module-scope identifier, the union-of-
    │                                 #   selects read payload (a conditional select is not
    │                                 #   privacy), Actions per table (Sep 18 2026);
    │                                 #   block Visibility gates its endpoints (Oct 5 2026);
    │                                 #   every row carries its record id (Oct 6 2026)
    ├── reading.md                    # useRecords, filtering, sorting, pagination,
    │                                 # metrics, charts, current user; no detail-page
    │                                 # auto-scoping, useRecords ignores enabled:false,
    │                                 # server-side linked-record filters (Sep 18 2026);
    │                                 # where/orderBy aliases resolve per hook, operator
    │                                 # semantics, filters fail open, userGroups poll,
    │                                 # excluded useRecord = no record (Oct 6 2026)
    ├── writing.md                    # Mutations, sequential write queues, uploads,
    │                                 # linked record format, cross-table writes;
    │                                 # Actions register per table (Sep 18 2026)
    ├── fields.md                     # getFieldValue(), field type shapes, record
    │                                 # structure, debug utilities; date-only fields
    │                                 # parsed as local dates, multi-value lookup shape
    │                                 # (Oct 6 2026)
    ├── rest-api.md                   # useProxyFetch + useQuery (full docs)
    ├── softr-database.md             # Native DB — field IDs, no rate limits; checkbox,
    │                                 # formula float, EMAIL lists, link label = display
    │                                 # field, Zapier replaces multi-links (Oct 6 2026)
    ├── airtable.md                   # Column names, PAT vs OAuth, rate limits
    ├── google-sheets.md              # Text formatting, 50-100 user cap
    ├── hubspot.md                    # 15 objects (listed ≠ usable), field model,
    │                                 # association writes, write behaviour, row scoping (Oct 5 2026)
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

Only `SKILL.md` loads into Claude's context when the skill triggers. The data source guides, reference files, and UI/UX guidelines load **on demand** — Claude reads only the files relevant to your specific block. This keeps context lean even with 30+ files totaling 6,000+ lines.

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
- SELECT fields write by option **label string**; linked records write as arrays of record-id strings. HubSpot differs (verified Oct 2026): SELECTs take the choice id, and an association update needs `[{ id }]` objects; in the one test it replaced the ticket's whole company list (see `datasources/hubspot.md`)
- Every code recompile resets the block's auto-registered Actions to default permissions — tighten permissions after the last redeploy, and note there is **no cosmetic-edit exemption**: an edit that changes only a comment resets them too. **Always read the permissions back to confirm** — a create action defaults to the block's own visibility, so on a block everyone can see it comes back publicly writable, and the MCP call that re-tightens it can fail with no fallback
- **Blocks cannot import each other**, so two blocks that must look alike will drift — each one looks correct in isolation while the set does not. Repeated page chrome (back button, title, primary action) must sit at the same offset on every page, and a loading skeleton must track the REST state of whatever it stands in for
- No `import React from 'react'` — use named imports (`import { useState } from "react"`)
- Must use `export default function Block()`
- Wrap layout in `<div className="container py-0"><div className="content">` for app/content blocks (house convention for width alignment with native blocks) — the platform default is actually full width, so full-bleed marketing blocks (heroes, banners, footers) legitimately omit the wrappers and own their gutters
- One `useRecords` per **connection** (house rule) — a block can connect to several sources, including the same table twice; declare them with `datasource.define()` and pass `from:` on every hook
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

If you fork it: the publish workflow first runs `python3 .github/scripts/check-links.py`, which fails the run when any relative Markdown link points at a missing file or a missing `#anchor`. Run the same command before pushing.

---

## References

- [Softr Vibe Coding Developer Guide](https://docs.softr.io/vibe-coding-developer-guide) — Official Softr Vibe Coding documentation
- [Softr Data Sources](https://docs.softr.io/data-sources) — Official Softr data source documentation
- [dembrandt](https://github.com/dembrandt/dembrandt) — Real-browser design-token extractor used for DESIGN.md generation (see `references/dembrandt.md`)
- [Impeccable](https://github.com/pbakaus/impeccable) — Design patterns and UI/UX anti-pattern principles by Paul Bakaus (referenced in the UI/UX guidelines)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills) — How Claude Code skills work

---

## License

[MIT](LICENSE)

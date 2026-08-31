---
name: softr-vibe-coding
description: >
  Generate custom Softr Vibe Coding blocks as complete React components (TSX/JSX). Use this skill whenever the user
  mentions Softr, Vibe Coding, Softr blocks, or wants to build a custom UI component for a Softr app.
  Also trigger when the user asks to create cards, lists, forms, dashboards, charts, detail pages,
  or any interactive block intended for Softr — even if they don't say "Vibe Coding" explicitly.
  If the user mentions Softr in the context of building a custom UI component, creating a JSX block,
  or vibe coding, use this skill. Do NOT use for extracting brand tokens or producing a DESIGN.md
  (that is the building-design-md skill), or for charts/dashboards with no Softr app involved.
when_to_use: >
  Triggers on "build me a Softr block", "create a card component", "make a dashboard",
  "vibe code this", "custom block for Softr", "JSX component for Softr app",
  "create a form block", "build a list view", "make a portal page",
  "Softr custom component", "vibe coding block".
effort: max
allowed-tools: Read Write Glob Grep Bash
---

# Softr Vibe Coding Block Generator

You generate complete, production-ready Softr Vibe Coding blocks as TypeScript React files. A Vibe Coding block is a single file with a default-exported React component, compiled by Softr's server and run in the browser inside a Softr app. The current platform compiles TypeScript with modern syntax — optional chaining (`?.`), nullish coalescing (`??`), arrow functions, `const`, generics — plus shadcn/ui from `@/components/ui/*`, lucide-react, sonner, and date-fns (verified live against the builder MCP's `get_vibe_coding_docs` and a 15-block production deployment, 2026-08-25).

> **Scope note — blocks vs. native chrome.** A block is page *content*, rendered inside a shadow DOM. Softr's global **header / top bar / nav / dropdown menus** are native chrome (configured in Studio, rendered in the main document) — you **cannot** build or replace them as a block. To restyle them, add CSS to Settings → Custom Code → Code inside header. See [references/native-chrome-styling.md](references/native-chrome-styling.md). One nuance: on a landing page where the native header is **hidden**, a hero block CAN render its own fixed in-block header (`position: fixed` inside the shadow root anchors to the viewport — verified 2026-08-31 from Softr's own Studio-AI output); pattern + caveats in [references/static-blocks.md](references/static-blocks.md#block-owned-landing-page-header).

## Your Workflow

1. **Detect the brand source (always run first, before any block work).** Check if a `./DESIGN.md` file exists in the project folder you're about to work in.

   - **If `./DESIGN.md` is found:** Read its frontmatter and confirm with the user:

     > "I found a DESIGN.md in this project (brand: `<name>`, source: `<source>`, extracted: `<date>`). Use its brand tokens for this block?
     > 1. Yes — use this DESIGN.md
     > 2. No — use the default Softr style instead
     > 3. No — I'll paste a different brand override"

     If (1), load every relevant section: `colors`, `typography`, `rounded`, `elevation`, `components`, and especially the `Application Patterns` scaffold. Apply those tokens throughout the block. Honour the `tech_stack` block — it may pin specific shadcn variants or note bundler quirks.

     If (2), proceed with the default Softr style (see Step 3).

     If (3), accept the override and apply it.

   - **If `./DESIGN.md` is NOT found:** Tell the user:

     > "No DESIGN.md found in this project. Three options:
     > A. **Set up a brand foundation first** — use the `building-design-md` skill to extract brand tokens from the client's website or a brand guide, then come back here. (Recommended for client work. Not installed? Run `npx building-design-md@latest init` in your terminal.)
     > B. **Quick brand override** — paste the brand's primary color, accent color, and font name now. I'll apply just those.
     > C. **Use the default Softr style** — primary `#386AF5`, accent `#FCB500`, Inter font."

     Wait for their pick. If (A), end the skill — the user will run `building-design-md` and then re-invoke this skill. If (B) or (C), record their choice for Step 3 and continue.

   Do not silently default to Softr's brand. The user must opt in to defaults explicitly.

2. **Understand what the user wants to build — and fork on archetype.** They will describe it in plain language. First decide: is this a **data-connected block** (list, dashboard, form, detail page — reads or writes records) or a **static marketing block** (hero, page header, pricing table, testimonial band, footer, content section — zero datasources, all content from editable settings)? For static blocks, read [references/static-blocks.md](references/static-blocks.md) and **skip the data-source questions and datasource guides entirely** (Step 1 brand detection still runs); settings-first design becomes the default — see [references/editable-settings.md](references/editable-settings.md#granularity-doctrine-settings-first-static-blocks). For data blocks, only ask about things you genuinely cannot infer: **data source type** and **field IDs**. For everything else, make sensible defaults and flag your assumptions.

3. **Apply defaults for the rest, don't ask.** Infer these from context instead of asking:
   - **Project folder**: Derive from the block description (e.g., "partner-portal", "client-dashboard"). If the user has already specified a folder in this session, reuse it.
   - **Brand colors**: Use whatever was chosen in Step 1 — DESIGN.md tokens, the user's override, or the default Softr palette (primary `#386AF5`, accent `#FCB500`). Never silently fall back to defaults.
   - **Filename**: Derive from the block purpose (e.g., `partner-invite.tsx`, `team-directory.tsx`). The user can rename later.

4. **Load the relevant data source guide** from [datasources/](datasources/) before writing code. Read the specific guide for the user's data source type. (Static marketing blocks: skip this step — read [references/static-blocks.md](references/static-blocks.md) instead.)

5. **Write the complete block file** (`.tsx` preferred; `.jsx` also compiles) to the project sub-folder and tell the user the full path. Create the sub-folder if it doesn't exist yet. The file must be fully self-contained, **visually polished from the first version**, and ready to paste into Softr's Vibe Coding editor. Styling is not an afterthought -- it ships in v1. **Never deliver code inline in chat.** Copy-pasting JSX from chat corrupts characters (`>`, `>=`, `=>`, quotes), causing compilation errors that are hard to debug. Always write to a file.

   **Delivery path:** if the official Softr MCP server is connected with Applications & Forms full access, offer to deploy the block directly after writing the file — `create_vibe_coding_block` (or `update_vibe_coding_block_code` for edits) plus `connect_vibe_coding_block_data_source` to wire the data. The local `.tsx` file stays the source of truth. Remember: every code push resets the block's Action permissions to defaults (Hard Constraint 21), and a block whose data source isn't connected saves fine but errors at page load. Details in [references/softr-mcp.md](references/softr-mcp.md).

6. **Self-validate before delivering.** Before presenting the code as complete, verify. (Data-hook items apply only to data-connected blocks; static marketing blocks swap in the checklist deltas from [references/static-blocks.md](references/static-blocks.md#workflow-deltas).)
   - Every data hook is called with an **inline options object literal** — `useRecords({ ... })` written through a variable or wrapper function fails to compile (verified live 2026-08-25). Share `q.select` mappings between hooks, never whole options objects
   - All imports use named imports (no `import React from 'react'`)
   - `export default function Block()` is present
   - Container + content wrappers present (`<div className="container py-0"><div className="content">`) — OR a deliberate full-bleed layout recorded in the `// BLOCK PLACEMENT:` comment (see "Block Placement & Page Spacing")
   - `// BLOCK PLACEMENT:` comment present at top of file with wrapper classes matching the placement (see "Block Placement & Page Spacing")
   - Loading, error, and empty states all handled
   - Mutation calls gated behind `enabled` check (if using mutations)
   - Field access uses `record.fields.alias` (not `record.alias`)
   - Every field rendered in JSX wrapped in `getFieldValue()` -- prevents React error #31
   - All hooks declared before any conditional `return` -- prevents React error #310
   - Sub-components (FieldLabel, TextInput, ChipButton, SectionCard, etc.) defined at **module scope**, NOT inside `Block()` -- prevents inputs losing focus after one keystroke (each render creates a new component identity, React unmounts/remounts the `<input>`)
   - When a custom DESIGN.md is in use, brand `fontFamily` (and any non-inherited brand defaults) set as an **inline style on the block's outermost wrapper** `<div>`, not relied on from `custom-code-header.html` -- Vibe Coding blocks render inside a shadow DOM and `html, body` rules don't cross that boundary. Per-element overrides (e.g. Fraunces serif on h1) still set inline at the element.
   - `fetchNextPage` never called in the render body — only from an event handler (Load More `onClick` with `disabled={isFetching}`, the official pattern) or a guarded `useEffect` (auto-load-all)
   - Mutations use `recordId` (not `id`) and call `refetch()` in `onSuccess`
   - `useRecordUpdate` payload is `{ recordId, fields: { ... } }` — nested. `useRecordCreate` payload is **flat** (no `fields` wrapper). The two shapes are asymmetric by design (verified live 2026-08-25)
   - Sequential multi-row saves use `await hook.mutateAsync(...)` per row, in order, with stop-on-failure + retry state — `mutateAsync` is fully supported on the current platform (verified 2026-08-25; the old ".mutate() only" Action-parser rule is gone — see [datasources/writing.md](datasources/writing.md))
   - No hardcoded domains in links -- use relative paths (`/page?recordId=...`); same-page anchors written relative too (`/#section`)
   - Static block: no hardcoded user-visible copy — every string/image/link is an editable setting (see [references/editable-settings.md](references/editable-settings.md#granularity-doctrine-settings-first-static-blocks))
   - Array-setting rows keyed by **index**, never by a builder-editable field value
   - Media settings that may start empty (`src: ""`) gated with a conditional render or placeholder — never an unconditional `<img src={setting.src}>`

## What to Clarify

When the user describes their block, figure out which of these areas apply and ask about anything you're missing:

- **Data source type**: Is it Airtable, Softr Database, REST API, or another source? This determines the data fetching approach. **Load the relevant data source guide** from the [datasources/](datasources/) directory before writing code.
- **Data source fields**: For Airtable/Softr Database, you need actual field IDs. For REST APIs, you access the raw API response directly. If the user doesn't know field IDs:
  - For **Softr Database**, the cleanest path is the official **Softr MCP server** — ask whether they have it installed (`claude mcp list` shows it as `softr` or similar). If yes, query schema directly with the MCP tools instead of asking for paste-ins. The same server also browses connected **Airtable, Google Sheets, Notion, and Supabase** integrations down to field level (`list_data_sources` → ... → `list_data_source_table_fields`), so prefer it for those sources too when available — see [references/softr-mcp.md](references/softr-mcp.md). If no MCP, the next-best option for Softr DB is the bundled **`get-softr-database` CLI script** — tell the user to run `python3 ~/.claude/skills/softr-vibe-coding/tools/get-softr-database.py <database_id>` (it prompts for their Softr API key and exports the full schema to `~/Desktop/softr-database-<id>-<timestamp>.json` — Python stdlib only, nothing to install) and paste the resulting JSON into chat. As a final fallback, ask them to paste the `tablespace-with-tables` network response (DevTools -> Network -> filter that string while on Studio's Data tab) — same JSON content, different acquisition path. Optionally tell them they can install the MCP once with `claude mcp add --transport http softr https://mcp.softr.io/mcp` for future sessions. Full MCP details in [references/softr-mcp.md](references/softr-mcp.md); CLI script details in [datasources/softr-database.md](datasources/softr-database.md#bundled-cli-script-get-softr-database); fallback paste-in workflows in [datasources/fields.md](datasources/fields.md#field-inspector-block).
  - For **Airtable**, the most thorough path is the bundled **`get-airtable-base` shell script** — `bash ~/.claude/skills/softr-vibe-coding/tools/get-airtable-base` (requires `jq` — `brew install jq` on macOS). It prompts for Base ID + PAT, then exports the full schema (every table, every field with both `fld...` IDs and column names, relationships, webhooks, interfaces) to a timestamped Desktop folder. The user pastes `02-schema.json` or the combined `00-bundle.json` into chat. For lighter inspection (just a few fields, runtime-only), suggest the Field Inspector block — empty `q.select({})` works for Airtable. CLI script details in [datasources/airtable.md](datasources/airtable.md#bundled-cli-script-get-airtable-base).
  - For other non-Softr-DB sources where empty `q.select({})` works, suggest the Field Inspector block.
- **Brand colors**: Already resolved in Step 1 (Detect the brand source). Don't re-ask. The brand source is one of:
  - **Project's `./DESIGN.md`** (recommended for client work — produced by the `building-design-md` skill)
  - **User's quick override** (paste of primary + accent + font)
  - **Default Softr palette** (only when the user explicitly opted in — never as a silent fallback):

    | Color | Hex | Name | Use |
    |---|---|---|---|
    | Primary | `#386AF5` | Mariner (blue) | CTAs, links, active states |
    | Accent | `#FCB500` | Yellow Sea | Highlights, badges, sparkle accents |
    | Destructive | `#F53878` | Cabaret (pink) | Errors, destructive actions, required markers |
    | Text | `#030712` | Revolver (near-black) | Body text, headings |
    | Background | `#FFFFFF` | White | Page and card backgrounds |

  Softr logo assets (for blocks that need Softr branding):
  - Icon + wordmark (SVG): `https://cdn.brandfetch.io/idytCFzVcY/theme/dark/logo.svg`
  - Icon only (PNG): `https://cdn.brandfetch.io/idytCFzVcY/w/1024/h/1024/theme/dark/icon.png`
- **Layout and style**: Cards vs. table vs. list? How many columns? Apply the Premium Visual Baseline for app-UI blocks; static marketing blocks use the editorial baseline in [references/static-blocks.md](references/static-blocks.md#editorial-baseline-replaces-the-premium-visual-baseline) instead.
- **Interactivity**: Create/edit/delete? Filtering? Sorting? Pagination?
- **User context**: Does it need to know who's logged in?
- **Settings**: Should anything be editable by the Softr builder (titles, images, toggle sections)?

Don't over-ask. If the user gives a clear description, fill in sensible defaults and note your assumptions.

## Examples (Decision Traces)

**User:** "Build a team directory with cards showing name, role, and photo from Airtable"
**Claude:** Reads `datasources/airtable.md` -> uses `q.select()` with Airtable column names (e.g., `"Full Name"`, `"Role"`, `"Headshot"`) -> card grid layout with `repeat(auto-fit, minmax(280px, 1fr))` -> avatar with brand-color fallback initials -> loading skeleton matching card shape -> empty state with "No team members yet"

**User:** "I need a form that pulls events from the Luma API and sends a webhook"
**Claude:** Reads `datasources/rest-api.md` -> uses `useProxyFetch` + `useQuery` (NOT `useRecords`) -> accesses raw API response directly (`event.name`, not `record.fields.name`) -> Select dropdown with event name + formatted date -> webhook via regular `fetch()` (not proxied) -> loading/error/empty states

## Data Sources

Softr supports 14 data sources. **Before writing any data-fetching code, read the relevant guide:**

| Data Source | Guide | Approach |
|---|---|---|
| Softr Databases | [datasources/softr-database.md](datasources/softr-database.md) | `useRecords` + `q.select()` |
| Airtable | [datasources/airtable.md](datasources/airtable.md) | `useRecords` + `q.select()` |
| Google Sheets | [datasources/google-sheets.md](datasources/google-sheets.md) | `useRecords` + `q.select()` |
| HubSpot | [datasources/hubspot.md](datasources/hubspot.md) | `useRecords` + `q.select()` |
| Notion | [datasources/notion.md](datasources/notion.md) | `useRecords` + `q.select()` |
| Coda | [datasources/coda.md](datasources/coda.md) | `useRecords` + `q.select()` |
| monday.com | [datasources/monday.md](datasources/monday.md) | `useRecords` + `q.select()` |
| SmartSuite | [datasources/smartsuite.md](datasources/smartsuite.md) | `useRecords` + `q.select()` |
| ClickUp | [datasources/clickup.md](datasources/clickup.md) | `useRecords` + `q.select()` |
| Xano | [datasources/xano.md](datasources/xano.md) | `useRecords` + `q.select()` |
| Supabase | [datasources/supabase.md](datasources/supabase.md) | `useRecords` + `q.select()` |
| BigQuery | [datasources/bigquery.md](datasources/bigquery.md) | `useRecords` + `q.select()` |
| SQL Database | [datasources/sql-database.md](datasources/sql-database.md) | `useRecords` + `q.select()` |
| REST API | [datasources/rest-api.md](datasources/rest-api.md) | `useProxyFetch` + `useQuery` |

**A block can connect to MORE THAN ONE of these at a time.** Declare them with `datasource.define({ alias: "uuid" })` and pass `from: ds.alias` on every data hook — read two tables and write to a third from a single block. Required reading before building anything multi-table: [datasources/multi-datasource.md](datasources/multi-datasource.md). (This replaces the old one-table-per-block limit and the invisible-helper-block workaround.)

Shared data patterns, linked directly (read the one the task needs): **reading** records, filtering, sorting, pagination, metrics, charts, current user — [datasources/reading.md](datasources/reading.md); **writing** — mutations, sequential write queues, uploads, field-type write shapes — [datasources/writing.md](datasources/writing.md); **field values** — `getFieldValue()`, field shapes, debug blocks — [datasources/fields.md](datasources/fields.md). ([datasources/shared-patterns.md](datasources/shared-patterns.md) is the thin index of the same set.)

For data source comparison and selection guidance, see [datasources/overview.md](datasources/overview.md).

## Reference Guides

For advanced patterns beyond data fetching, load the relevant reference when the task needs it:

| If the task involves... | Load reference |
|---|---|
| Reading/writing **several tables from one block** — `datasource.define()`, the `from:` parameter, obtaining the datasource UUIDs (and why Studio's chat invents them) | [datasources/multi-datasource.md](datasources/multi-datasource.md) |
| Cross-*block* communication, window globals, breadcrumbs, publishing shared computed state. *(Multi-table reads no longer need a helper — use a second datasource.)* | [references/helper-blocks.md](references/helper-blocks.md) |
| Embedding third-party libraries with their own CSS (Leaflet, Mapbox, TinyMCE, Quill, FullCalendar) | [references/advanced-integrations.md](references/advanced-integrations.md) |
| Debugging a broken block, checking patterns before delivery, full violation catalog | [references/anti-patterns.md](references/anti-patterns.md) |
| Quick syntax check — import paths, hook signatures, mutation call shapes, field mapping | [references/quick-reference.md](references/quick-reference.md) |
| Small reusable patterns — `localStorage` cross-page state, clipboard copy button | [references/common-patterns.md](references/common-patterns.md) |
| Writing Airtable Automation Scripts / Scripting Extension scripts / Airtable formulas — companion to Softr blocks for cross-table cascades and computed values | [references/airtable-automations.md](references/airtable-automations.md) |
| The official **Softr MCP server** — schema discovery and record reads for Softr DB, field-level browsing of connected Airtable / Google Sheets / Notion / Supabase integrations, and **creating, editing, versioning, and deploying Vibe Coding blocks directly** (`get_vibe_coding_docs`, `create_vibe_coding_block`, `connect_vibe_coding_block_data_source`, ...) | [references/softr-mcp.md](references/softr-mcp.md) |
| Restyling Softr's **native shell — header / footer / nav / dropdowns / page background** (not a block; it's Softr chrome, done with global Custom Code CSS): stable selectors vs. hashed classes, floating "island" header+footer, the dropdown blank-space grid fix, the multi-layer page-background stacking, restyle-vs-replace | [references/native-chrome-styling.md](references/native-chrome-styling.md) |
| Adding a **dynamic date filter or custom filter control to a native List/Grid block** (via a Custom Code Static block, not a Vibe block): drive the block's conditional filter with `{URL_PARAM:…}`, the empty-param "match nothing" wide-range sentinel, inject the control into the filter row and keep it alive across Softr's re-renders | [references/native-block-filters.md](references/native-block-filters.md) |
| **Editable settings deep-dive** — full hook catalog (incl. verified-undocumented `useLongTextSetting` and the `navigation` array-schema type), settings-first granularity doctrine, heading-line-split and `-text`/`-link` pairing patterns, naming conventions, rename-resets-value gotcha, empty-media gating, key-by-index rule | [references/editable-settings.md](references/editable-settings.md) |
| **Static marketing blocks** — heroes, landing headers, pricing tables, footers: workflow deltas (skip datasources), editorial baseline, full-bleed license, full-viewport sizing, block-owned fixed header + caveats, section anchors | [references/static-blocks.md](references/static-blocks.md) |

## Code Structure

Every block follows this shape:

```jsx
// imports at the top
import { ... } from "@/lib/datasource";
// ...other imports

export default function Block() {
  // hooks, state, logic
  return (
    <div className="container py-0">
      <div className="content">
        <div className="py-3 px-8">
          {/* block content — wrapper padding depends on placement; see "Block Placement & Page Spacing" */}
        </div>
      </div>
    </div>
  );
}
```

Wrap the outermost layout in `container` and `content` divs by default — these constrain width to match the Softr app's max width settings so the block aligns with neighboring native blocks. Note this is a **house convention, not platform-enforced**: per the official developer guide the platform default is full width, and the classes are merely "available" to constrain it (verified 2026-08-31 against `get_vibe_coding_docs` and a rendering wrapper-free Studio-AI hero).

**Exceptions (omit the wrappers deliberately):**
- Blocks inside Softr column containers — Softr controls layout.
- Full-bleed marketing blocks (heroes, banner bands, footers) — backgrounds and decorative shapes run edge-to-edge; the block then owns its own gutters (`px-6 md:px-12 lg:px-16`) and inner max-widths, and records the choice in the `// BLOCK PLACEMENT:` comment. See [references/static-blocks.md](references/static-blocks.md#full-bleed-layout-license).

## Block Placement & Page Spacing

Blocks rarely live alone — most Softr pages stack 2–4 blocks vertically, often between a header and a footer. Spacing must be set per-block based on **where the block sits on the page**, so adjacent blocks don't double up padding or leave inconsistent gaps.

**General rule:** the inner wrapper (the `<div>` directly inside `<div className="content">`) owns all vertical spacing. The outer `container` is always `py-0`. Top and bottom padding on the wrapper change based on what's above and below the block (another block, a header, a footer, or nothing).

**When generating a new block, if the placement is not clear from the user's description, ASK before writing code:**
- Where will this block sit on the page? (top / middle / bottom / standalone)
- Is there a Softr header immediately above this block?
- Is there a Softr footer immediately below this block?
- Is there a Back button at the top of this block?

**Detail pages — always ask about the back button AND its fallback URL.** A "detail page" is any block that reads a single record by URL recordId (i.e. it calls `useCurrentRecordId()` / `useRecord()`, or the user describes it as the target of a `/page?recordId=...` link). Users almost always want a back button there but rarely think to mention it, and shipping the page without one is the most common UX gap on these screens. So even if every other placement detail is clear, ask both:

1. **"Should the detail page have a back button?"** — if yes, always wire one. Use the back-navigation pattern in [references/helper-blocks.md](references/helper-blocks.md#breadcrumb--back-navigation): `window.history.back()` for users with history, plus a fallback URL for users who arrived via shared link.
2. **"What page should the back button fall back to when there's no history?"** — this is a separate question, easy to skip but important. Don't default silently; ask. If the user doesn't have a listing page yet, default to `/` and leave a `// TODO: update fallback when /jobs (or similar) exists` comment so it can be updated later.

**Persist the answer as a grep-able comment at the top of the generated file** so future edits know the spacing assumptions and can be updated consistently:

```jsx
// BLOCK PLACEMENT: <position on page>, <header/footer adjacency>, <back button y/n>
// Spacing: <wrapper classes; back-button container if present>
```

Example:

```jsx
// BLOCK PLACEMENT: first block on page, header-adjacent, has Back button
// Spacing: wrapper py-3 px-8; back-button container mt-6 mb-4
```

The `// BLOCK PLACEMENT:` marker is intentionally stable so it can be grepped and updated when the block's surroundings change.

### Spacing values (defaults)

**Container** (default — omitted by full-bleed blocks and blocks inside column containers; see table below): `<div className="container py-0">`

**Inner wrapper** classes by block position:

| Position on page | Wrapper classes | Rationale |
|---|---|---|
| First block (header-adjacent) | `py-3 px-8` | 12px top + 12px bottom; lets the Softr header own its own spacing |
| Middle block | `py-3 px-8` | 12px + Softr separator + 12px ≈ 24px between blocks |
| Last block (footer-adjacent) | `pt-3 pb-12 px-8` | 12px top + 48px bottom for footer breathing room |
| Standalone (only block on page) | `pt-3 pb-12 px-8` | Treat like a last block |
| Full-bleed (hero / banner / footer) | none — no container/content; block owns gutters `px-6 md:px-12 lg:px-16` | Edge-to-edge backgrounds; see [references/static-blocks.md](references/static-blocks.md#full-bleed-layout-license) |

**Back button** (when present at the top of a block — typically on detail pages): wrap in `<div className="mt-6 mb-4">`. The `mt-6` (24px) adds breathing room above the button independent of wrapper padding; `mb-4` (16px) sits between the button and the first card. Apply this regardless of whether the block is first or mid-page.

**Within-block stacked cards**: each card uses `mb-6` (24px). **Do NOT add `mb-6` to the last card** in a block — the wrapper's bottom padding already handles that buffer. Doubling them produces 32–40px gaps that look bigger than the within-block rhythm.

**Net page rhythm**: between-block gaps (12 + 12 = 24px) match within-block card gaps (`mb-6` = 24px), so the page reads as one consistent vertical rhythm.

### Full-viewport hero blocks

A hero may size itself to the viewport — vh units inside a block resolve against the real window (blocks are shadow DOM in the main document, not iframes). The Studio-verified responsive shape is `min-h-screen lg:min-h-0 lg:h-screen` (natural height on mobile, locked viewport height on desktop). Three rules: (1) `h-screen` fills the window only when the native header is hidden on that page — with a native header above, a 100vh block overflows by the header height; use `min-h-[calc(100vh-<px>)]` when native chrome stays; (2) hard `h-screen` + `overflow-hidden` + centered flex **clips settings-grown content unrecoverably** — prefer `lg:min-h-screen` unless the locked look is explicitly wanted; (3) the standard spacing table above does not apply — the hero owns all its spacing. Extend the placement comment: `// BLOCK PLACEMENT: full-viewport hero, native header hidden, owns all spacing`. Full detail in [references/static-blocks.md](references/static-blocks.md#full-viewport-hero-sizing).

## Premium Visual Baseline

**Every block must look polished in its first version.** Styling is not a follow-up task — it is a core requirement of every code generation. Apply ALL of the following by default unless the user explicitly requests a minimal/plain style.

**Scope: this is the app-UI baseline** — dashboards, lists, forms, detail pages. Static marketing blocks (heroes, landing sections, footers) use the **editorial baseline** in [references/static-blocks.md](references/static-blocks.md#editorial-baseline-replaces-the-premium-visual-baseline) instead — typographic hierarchy and brand-exact values, no gradient wrapper/cards/skeletons/empty states (nothing loads).

Refer to [ui-ux-guidelines.md](ui-ux-guidelines.md) for full design principles.

### 1. Gradient background wrapper
```jsx
<div className="rounded-2xl p-8" style={{ background: "linear-gradient(180deg, #EEF2FF 0%, #FFFFFF 100%)" }}>
  {/* header + content cards go inside here */}
</div>
```
Adjust the top gradient color to complement the user's brand.

### 2. Header section
- Icon in a colored rounded square (`h-10 w-10 rounded-xl` with brand primary, white icon)
- Title at `text-2xl font-bold`
- Optional subtitle in `text-muted-foreground`
- Primary CTA button with `shadow-md hover:shadow-lg transition-shadow`

### 3. Card-based content
- `bg-white rounded-xl shadow-sm border border-gray-100`
- Items with `hover:shadow-md hover:border-gray-200 transition-all duration-200`
- Use `space-y-3` or `gap-3`, never flat separators

### 4. Avatar and identity elements
- Brand primary color as avatar fallback with white initials
- `h-12 w-12` for list items, `h-28 w-28` for profiles
- `border-2 border-white shadow-lg` on profile avatars

### 5. Interactive feedback
- Buttons: `shadow-md hover:shadow-lg transition-shadow`
- Cards: `hover:shadow-md hover:border-gray-200 transition-all duration-200`
- Active states: blue left border accent (`border-l-4`)

### 6. Status and metadata
- Counts in pill badges: `text-xs font-medium px-2 py-0.5 rounded-full`
- Dates with icons (Calendar, Mail, Users)

### 7. Empty states
- Large icon in gradient square (`h-20 w-20 rounded-2xl`)
- Clear heading + explanation + CTA button

### 8. Loading states
- Skeleton shapes matching the final layout, `rounded-xl`

### 9. Error states
- Icon in tinted background, clear message, retry button

### 10. Modals and dialogs
- Icon in dialog title, required field markers, example placeholders

## Styling & Components

**Tailwind CSS** is pre-configured. **Semantic color tokens** preferred:
`bg-background`, `bg-card`, `bg-primary`, `bg-secondary`, `bg-muted`, `bg-accent`, `bg-destructive`, `border`, `border-input`

**Arbitrary values compile in full** — the platform's Tailwind build is JIT, so the whole arbitrary-value syntax works, including opacity modifiers on arbitrary hex (`bg-[#FAF5EC]/85`), variant + arbitrary + opacity combined (`hover:bg-[#6E7A5C]/10`), negative arbitrary values (`-top-[22%]`, `hover:-translate-y-[1px]`), arbitrary object-position (`object-[62%_25%]`), arbitrary z (`z-[1]`), and vw sizing (verified 2026-08-31 from rendering Studio-AI output). Classes must be **static source strings** — never template-interpolate (`` bg-[${x}] ``); JIT extracts classes by static scan (standard-Tailwind inference, not Softr-verified). When to reach for them vs. the scale: see the editorial lane in [ui-ux-guidelines.md](ui-ux-guidelines.md) §7. (This covers arbitrary *values* and standard variants; arbitrary *selector* variants like `[&_svg]:` have at least one known bundler failure — see the SelectTrigger row in [references/anti-patterns.md](references/anti-patterns.md#layout--styling).)

**Font classes:** `font-heading`, `font-sans`, `font-mono`

**Conditional classNames:** `import { cn } from "@/lib/utils";` — template-literal conditionals (`` className={`base ${cond ? "a" : "b"}`} ``) are equally valid (Studio AI emits them); prefer `cn()` when merging many groups or de-duplicating conflicting classes.

**DO NOT USE:** CSS modules, styled-components, or CSS file imports.

**shadcn/ui components** at `@/components/ui/[name]`:
accordion, alert, alert-dialog, aspect-ratio, avatar, badge, button, calendar, card, carousel, chart, checkbox, collapsible, command, context-menu, dialog, drawer, dropdown-menu, empty, hover-card, input, input-group, input-otp, item, kbd, label, menubar, native-select, navigation-menu, pagination, popover, progress, radio-group, resizable, scroll-area, select, separator, sheet, skeleton, slider, sonner, spinner, switch, table, tabs, textarea, toggle, toggle-group, tooltip

**Common import patterns:**

```jsx
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
```

**Lucide Icons:** `import { TrendingUp, User, Settings } from "lucide-react";`

**Dynamic icons by name string:** `<DynamicIcon>` from `@/components/dynamic-icon` renders a Lucide icon when you only know its name at runtime (e.g. from an editable setting, a window global, or a `useRecords` row). Pass the kebab-case Lucide name as `name`. Use this — not a manual lookup table — whenever the icon is data-driven.

```jsx
import { DynamicIcon } from "@/components/dynamic-icon";
<DynamicIcon name="trending-up" className="h-5 w-5" />
```

**Softr's `<NavigationAction>`** is a built-in component for triggering Softr-native navigation actions from inside a Vibe Coding block. Accepts a `recordId` prop for dynamic record-specific URLs and supports action types `OPEN_URL`, `OPEN_PAGE`, `OPEN_CHAT`, `TRIGGER_CUSTOM_WORKFLOW`. Prefer this over bare `<a href>` when you want Softr's user-group visibility checks and slide-out / modal navigation styles to apply. Bare `<a href>` is still fine for simple in-app links where you don't need that behavior.

The canonical pattern pairs a shadcn `<Button asChild>` with `<NavigationAction navigation={...}>` so the button's styling stays on-brand while the navigation behavior is handled by Softr's component:

```jsx
import { Button } from "@/components/ui/button";
import { NavigationAction } from "@/components/navigation-action";
import { useNavigationSetting } from "@/lib/editable-settings";
import { MessageSquare } from "lucide-react";

var askAi = useNavigationSetting({
  name: "ask-ai-action",
  label: "Ask AI Action",
  initialValue: { action: "OPEN_CHAT" },   // OPEN_CHAT needs no destination
});

<Button asChild size="lg" className="gap-2">
  <NavigationAction navigation={askAi}>
    <MessageSquare className="h-5 w-5" />
    Ask AI about this
  </NavigationAction>
</Button>
```

**Action types — what each one needs in `initialValue`:**

- `OPEN_CHAT` — opens Softr's AI chat. **No `destination` or `openIn` needed** — it's the cheapest "Ask AI" button to wire up. **GOTCHA:** Softr's AI pulls context from the block that triggered the chat, NOT from the page. If the block has no data source connected, `chat/prepare` returns HTTP 500 ("Failed to prepare AI assistant") even though the chat panel opens. Fix: in Softr Studio, connect the block to whatever data source the AI should read from — even if the block doesn't read or write any records itself, the connection is what gives the AI context. Verified by direct experiment, May 2026: a button-only helper block with no data source caused this exact failure; connecting it to the same table as the main block fixed it without any code change.
- `OPEN_URL` — opens an external URL. Needs `destination` (the URL) + `openIn` (`"SELF"` | `"TAB"`).
- `OPEN_PAGE` — navigates to a Softr page in-app. Needs `destination` (page path) + `openIn` (`"SELF"` | `"TAB"` | `"MODAL"`).
- `TRIGGER_CUSTOM_WORKFLOW` — runs a Softr workflow. The documented setting shape is `{ action: "TRIGGER_CUSTOM_WORKFLOW" }` with no `destination` (same shape as `OPEN_CHAT`); the builder picks the workflow in the block's settings panel. Not verified live whether a `destination` is also accepted — don't rely on one.

When the action navigates to a record-specific page, pass the runtime record id via the `recordId` prop on `<NavigationAction>` (not on the setting) so Softr can resolve dynamic URLs:

```jsx
<NavigationAction navigation={openWigDetails} recordId={wig.id}>
  View wig
</NavigationAction>
```

For on-brand custom styling (matching DESIGN.md inline-style conventions instead of shadcn Button), wrap the same pattern with a styled `<button>` — `<NavigationAction>` will render its children into the button's slot. The `asChild` attribute on Button is what enables this slot composition; without it shadcn renders its own native button and ignores `<NavigationAction>`.

**Third shape — standalone `<NavigationAction>` with `className`** (text-style links, nav items — no Button wrapper). NavigationAction renders its own clickable element and forwards `className` onto it; include UA-style resets since that element ships default chrome. Observed in Studio-AI output 2026-08-31, not in the official developer guide — don't treat className forwarding as officially guaranteed:

```jsx
<NavigationAction
  navigation={item.link}
  className="text-[15px] text-[#2A2520] hover:text-[#AE5E3D] transition-colors bg-transparent border-none cursor-pointer no-underline"
>
  {item.label}
</NavigationAction>
```

**Brand hex on a shadcn `<Button>` — the middle path.** To keep `<Button asChild>` (slot composition, focus ring, disabled handling) while guaranteeing an exact brand color, set the color as an inline style: `<Button asChild className="... shadow-none" style={{ backgroundColor: "#B4603D" }}>`. The precedence consequence: with an inline `backgroundColor`, **no `hover:bg-*` class can ever repaint it** (inline style outranks all classes, and ui-ux-guidelines' "hover handled by shadcn Button" no longer holds) — do hover feedback with `hover:opacity-90` / `hover:-translate-y-[1px]` instead. Alternative: a static `bg-[#HEX]` class also works (arbitrary values compile, and shadcn's `cn()`/tailwind-merge resolves it against the variant's `bg-primary`), in which case `hover:bg-*` stays available.

**Any public npm package** auto-installs on import: `import { format } from "date-fns";`

### React Hooks — Critical Import Rule

```jsx
// CORRECT
import { useState, useEffect } from "react";

// WRONG — All of these fail:
const { useState } = React;
import React from 'react';
React.useState(null);
useState(null);  // without import = ReferenceError
```

## Editable Settings

Hooks from `@/lib/editable-settings` let Softr builders customize blocks via **Content → Settings**. Each `name` must be unique — and `name` is the **persistence key**: renaming it in a later edit silently resets the builder's saved value to `initialValue`. Compact signatures below; the deep-dive (granularity doctrine, naming conventions, undocumented hooks/types, empty-media gating) is [references/editable-settings.md](references/editable-settings.md).

```jsx
import { useTextSetting } from "@/lib/editable-settings";
var title = useTextSetting({ name: "title", label: "Title", initialValue: "Welcome", required: false });
// Returns: string

import { useLongTextSetting } from "@/lib/editable-settings";
var description = useLongTextSetting({ name: "description", label: "Description", initialValue: "..." });
// Returns: string — multi-line textarea in the Settings pane. UNDOCUMENTED officially but verified
// working 2026-08-31 (Studio-AI output). Render with `whitespace-pre-line` or builder line breaks collapse.

import { useImageSetting } from "@/lib/editable-settings";
var image = useImageSetting({ name: "hero", label: "Hero Image", initialValue: { src: "https://...", alt: "Hero" } });
// Returns: { src: string, alt: string }

import { useVideoSetting } from "@/lib/editable-settings";
var video = useVideoSetting({ name: "intro", label: "Intro Video", initialValue: { src: "https://..." } });
// Returns: { src: string }

import { useVibeCodingBlockIconSetting } from "@/lib/editable-settings";
import { DynamicIcon } from "@/components/dynamic-icon";
var iconSetting = useVibeCodingBlockIconSetting({ name: "icon", label: "Icon", initialValue: { icon: "trending-up" } });
// Render: <DynamicIcon name={iconSetting.icon} className="w-6 h-6" />

import { useNavigationSetting } from "@/lib/editable-settings";
var nav = useNavigationSetting({ name: "cta", label: "CTA", initialValue: { action: "OPEN_PAGE", destination: "/pricing", openIn: "SELF" } });
// Returns: { action, destination, openIn }
// `openIn` MUST be one of: "SELF" (same tab), "TAB" (new tab), or "MODAL". Any other value (e.g. "SAME_TAB", "NEW_TAB") fails Softr's setting validator with: "useNavigationSetting(): The 'initialValue.openIn' property in the 'navigation' setting must be \"SELF\", \"TAB\", or \"MODAL\" if provided".
// The validator ACCEPTS an initialValue with no `action` key (Studio AI emits { destination, openIn } alone — verified 2026-08-31). Keep emitting an explicit `action` when generating, but don't flag its absence as a defect when reviewing existing blocks.

import { useBooleanSetting } from "@/lib/editable-settings";
var show = useBooleanSetting({ name: "toggle", label: "Show header", initialValue: false });
// Returns: boolean

import { useArraySetting } from "@/lib/editable-settings";
var features = useArraySetting({
  name: "features", label: "Features",
  schema: {
    title: { type: "text", label: "Title", initialValue: "Feature" },
    description: { type: "text", label: "Description" },
    icon: { type: "vibeCodingBlockIcon", label: "Icon" },
  },
  initialValue: [{ title: "Fast", description: "Blazing fast.", icon: { icon: "zap" } }],
});
// Schema types: "text", "image", "video", "vibeCodingBlockIcon" — plus UNDOCUMENTED-but-working
// "navigation" (verified 2026-08-31 via Studio-AI output; renders per-item link pickers, item values
// carry the useNavigationSetting shape → pass to <NavigationAction navigation={item.link}>).
// Give navigation-typed schema entries a per-field initialValue, or guard the render — builder-added
// rows otherwise start with that field undefined.
// No nested arrays. Don't put vibeCodingBlockIcon as first field.
// Key rendered rows by INDEX (key={index}), never by an editable field — builder-added rows all start
// at the schema default, so value keys duplicate immediately. See references/editable-settings.md.
```

## Hard Constraints

Non-negotiable rules. Most are enforced by the Softr platform (compiler, validator, or runtime); the ones marked **[house]** are conventions this skill enforces on itself — the platform accepts violations, but the rule exists for consistency or safety:

1. **Browser-only** — No server-side code, no Node.js APIs.
2. **Static field mappings** — `q.select()` keys and values must be string literals.
3. **Filter nesting limit** — Maximum 2 levels deep with `q.and()` / `q.or()`.
4. **Check mutation `enabled`** — Gate mutation UI and calls behind the `enabled` boolean.
5. **Unique setting names** — No two setting hooks can share the same `name`.
6. **Array setting icon placement** — Never put `vibeCodingBlockIcon` as first field.
7. **No nested arrays in settings** — Use text with separator, split in code.
8. **Default export required** — `export default function Block()`.
9. **Container wrapping [house]** — Wrap in `<div className="container py-0"><div className="content">` by default so the block's width matches native blocks. NOT platform-enforced: the platform default is full width and the wrappers are officially optional (verified 2026-08-31). Deliberate full-bleed blocks (heroes, banner bands, footers) and blocks inside column containers omit them — see "Block Placement & Page Spacing" and [references/static-blocks.md](references/static-blocks.md#full-bleed-layout-license). Vertical padding lives on the inner wrapper and depends on block placement.
10. **Inline options literals for data hooks** — `useRecords` fails to compile when its options
    object is passed through a variable or wrapper function. Build the options object inline at the
    call site; share `q.select` mappings between hooks, not whole options objects. (Same
    static-analysis family as the `q.select()` / `datasource.define()` literal rules. Verified live
    2026-08-25 — hit in a production block whose options came from a wrapper function; the fix was
    changing the wrapper to take the hook's *result* instead.)
11. **Airtable, Notion, Google Sheets: use field NAMES, not IDs** — `q.select()` values are field names for these three sources; Softr Database and Supabase use field IDs (Supabase = SQL column name). Getting this wrong fails silently: the block compiles and saves, then renders empty. See [datasources/airtable.md](datasources/airtable.md).
12. **Record fields nested under `fields`** — Access via `record.fields.alias`, not `record.alias`.
13. **ONE `useRecords` per datasource** — filter client-side rather than issuing several queries against
    the same table. A block CAN connect to multiple data sources and call `useRecords` once per source;
    declare them with `datasource.define()` and pass `from:` on every hook. See
    [datasources/multi-datasource.md](datasources/multi-datasource.md). Multiple `useMetric` calls OK.
14. **React functional components only** — No class components.
15. **Do NOT `import React from 'react'`** — Use named imports for hooks.
16. **No CSS modules or styled-components** — Tailwind only.
17. **setTimeout for scroll [house]** -- Wrap **programmatic** scroll commands (`scrollIntoView`, `scrollTo`) in `setTimeout(fn, 0)`. This is about ISSUING scrolls only — LISTENING to window scroll (`window.addEventListener("scroll", ...)`) needs no wrapper and works normally from block code; see [references/common-patterns.md](references/common-patterns.md#scroll-condensing-fixed-header-landing-page-hero).
18. **Never call `fetchNextPage` in the render body** -- render calls `fetchNextPage`, which updates data, which triggers re-render, which calls it again: infinite loop. Call it from an event handler (the official Load More pattern: `<button onClick={() => fetchNextPage()} disabled={isFetching}>`) or from a guarded `useEffect` when intentionally auto-loading all pages.
19. **All hooks before any conditional `return`** -- Hooks must be called in the same order every render. A hook declared after a conditional `return` causes React error #310.
20. **Relative paths in navigation [house]** -- Use `/page-name?recordId=...`, never hardcoded domains like `app.client.com/page`. The platform accepts absolute self-domain URLs as navigation setting values (a Studio-generated hero shipped its CTA configured as `https://<app>.softr.app/#section` — observed in the Settings pane, 2026-08-31), but they break on custom-domain publish — rewrite them relative, including hash anchors (`/#section`).
21. **Recompiles reset Action permissions** -- Every code recompile/redeploy resets the block's
    auto-registered Actions to **default permissions**. Do the Actions-tab permission tightening pass
    only after the LAST redeploy, and re-check it after any future one. Verified live 2026-08-25
    across a 15-block deployment. See [datasources/writing.md](datasources/writing.md#how-actions-work-studios-actions-tab).

## Style Conventions

**The current platform compiles TypeScript with modern syntax** — optional chaining (`?.`), nullish coalescing (`??`), arrow functions, `const`/`let`, generics — verified live against `get_vibe_coding_docs` and a 15-block production deployment on 2026-08-25. Write new blocks in modern TS (`.tsx`); it matches what Softr's own Studio AI emits.

History, kept so old guidance elsewhere is recognizable as superseded: until mid-2026 this skill mandated `var` + `function(){}` and banned `?.` / `??` because the then-current bundler failed on them (verified April 2026; a Studio-scaffolded block already contradicted it by July 2026). That platform behavior is gone. Existing var-style blocks remain valid — the compiler accepts both styles — so don't churn a working block just to modernize its syntax, and don't "fix" modern syntax back to var-style when editing.

Still house conventions: the field-value helper is named `getFieldValue()`, with property priority `label` -> `name` -> `title`.

**Platform truth sources.** Blocks emitted by Softr's own Studio AI are known-good evidence of what the current platform accepts — they compile and render live, and they surface undocumented hooks and setting types before the official docs catch up (this is how `useLongTextSetting` and the `navigation` array-schema type were discovered, 2026-08-31). Mine them for capabilities, but **never copy them verbatim**: fix React keys on settings-array loops (index, never a builder-editable label), consolidate near-duplicate hardcoded hexes into brand/DESIGN.md tokens, add the missing mobile nav / media-setting guards, and normalize formatting. Functional patterns in Studio output are platform-support evidence; its formatting and code hygiene are not patterns to imitate. (This is distinct from the no-churn rule above — cleaning up a block you're ADOPTING into the repo as source of truth is required; modernizing a deployed working block's syntax is still churn.) Adoption checklist: [references/softr-mcp.md](references/softr-mcp.md#adopting-studio-ai-generated-code). Note the inverse rule stays too: Studio's chat **prose** fabricates facts (datasource UUIDs) — trust its code, not its answers.

## Anti-Patterns Checklist

Before delivering any block, run through [references/anti-patterns.md](references/anti-patterns.md) — a categorized catalog of every violation observed in production (data access, mutations, hooks, layout, helper blocks).

## Code Quality Guidelines

- Use `sonner`'s `toast` for notifications. Also: `toast.info()`, `toast.message("Note", { description: "..." })`.
- Show loading states with `spinner` or `skeleton` when `status === "pending"`.
- Show error states gracefully when `status === "error"`.
- After mutations, call `refetch()` before success toast.
- Use Tailwind for all styling.
- Prefer shadcn/ui components over raw HTML.
- Use `date-fns` for date formatting.

## UI/UX Guidelines

For design best practices, spacing, responsive patterns, and component guidance, see [ui-ux-guidelines.md](ui-ux-guidelines.md).

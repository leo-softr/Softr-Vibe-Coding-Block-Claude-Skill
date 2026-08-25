# Softr MCP Server

The official Softr MCP server (`https://mcp.softr.io/mcp`) gives an AI assistant (Claude Code, Claude Desktop, claude.ai, Cursor, ChatGPT, Mistral) direct access to a Softr **workspace**: databases, applications, vibe coding blocks, integrations (external data sources), and workflows. Everything the assistant does happens as the connected user, with their permissions, and shows up in Studio like any other change.

**This file is a sibling concern to the [../datasources/](../datasources/) guides, which cover in-block data fetching (`useRecords` + `q.select()`).** The MCP runs at chat-build time, not inside the block. For Vibe Coding work it matters twice: it answers "what fields does this table have?" without any paste-ins, and it can create and deploy the block itself — no copy-paste into Studio.

> Historical note: this file was previously named `softr-database-mcp.md` and described a databases-only server with granular scopes. That server has since grown into the workspace-wide MCP documented here; the old "does NOT cover external sources" limitation is gone (see [Integrations](#browsing-integrations-external-data-sources)).

## Contents

- [What it covers](#what-it-covers)
- [Connection and auth](#connection-and-auth)
- [Permissions model](#permissions-model)
- [Vibe coding block tools](#vibe-coding-block-tools)
- [Vibe coding gotchas (official)](#vibe-coding-gotchas-official)
- [Browsing integrations (external data sources)](#browsing-integrations-external-data-sources)
- [Softr Database tools](#softr-database-tools)
- [Two delivery paths for this skill](#two-delivery-paths-for-this-skill)
- [When the MCP is not installed](#when-the-mcp-is-not-installed)

## What it covers

| Area | What the assistant can do | Official docs |
|---|---|---|
| Databases | Query, filter, aggregate; create/update records; build tables and fields | https://docs.softr.io/mcp/databases |
| Applications | Read apps, pages, blocks, permissions; preview; publish | https://docs.softr.io/mcp/apps |
| Vibe coding blocks | Create and edit blocks, manage settings, visibility, versions, data source connections | https://docs.softr.io/mcp/vibe-coding |
| Integrations | Browse external data sources connected to the workspace, down to field level | https://docs.softr.io/mcp/integrations |
| Workflows | Build, test, and publish workflows | https://docs.softr.io/mcp/workflows |

`list_workspaces` is often the first call — it turns "my Sales workspace" into the workspace ID every other tool needs.

## Connection and auth

- **Server URL:** `https://mcp.softr.io/mcp` (streamable HTTP)
- **Official docs:** https://docs.softr.io/mcp/overview

Install in Claude Code:

```bash
claude mcp add --transport http softr https://mcp.softr.io/mcp
```

Then start a new session and run `/mcp` to complete OAuth in the browser.

Two auth methods:

1. **OAuth (recommended)** — pre-built clients exist for Claude (claude.ai), Cursor, ChatGPT, and Mistral. If a Client ID is requested, use the value from the [overview docs](https://docs.softr.io/mcp/overview); leave Client Secret blank (Softr's OAuth clients are public). The assistant cannot request permissions — the user always picks them on Softr's authorization screen.
2. **Personal access token** — for custom clients. Created in Softr under **Settings → API tokens** (name, expiry, workspace + permission scoping), then used as a Bearer token.

Revoke or edit access anytime in **Settings → API tokens** (Authorized apps section for OAuth, token list for PATs).

## Permissions model

Permissions are chosen per workspace across **three areas with bundled levels** — not granular per-tool scopes. Each level includes everything below it (no "write without read").

| Area | Levels | Highest level adds |
|---|---|---|
| Applications & Forms | Full access · Read only · None | Creating/editing vibe coding blocks, previewing, publishing |
| Databases | Full access · Edit data · View only · None | Schema changes (tables/fields); Edit data adds record writes |
| Workflows | Full access · Read only · None | Building, testing, publishing workflows |

For block-building work you need **Applications & Forms: Full access** (to create/edit blocks) plus at least **Databases: View only** (schema discovery). Integrations browsing rides on Applications & Forms read access.

## Vibe coding block tools

Before writing any block code through the MCP, call `get_vibe_coding_docs` — it returns the current version of the [Vibe Coding Developer Guide](https://docs.softr.io/vibe-coding-developer-guide), which is the authority on hook signatures if it and this skill ever disagree.

| Group | Tools |
|---|---|
| Create / read | `get_vibe_coding_docs`, `create_vibe_coding_block`, `get_vibe_coding_block_code`, `get_vibe_coding_block_settings` |
| Edit code | `update_vibe_coding_block_code` (full replace), `update_vibe_coding_block_code_search_replace` (targeted edit) |
| Settings / visibility | `update_vibe_coding_block_settings`, `set_vibe_coding_block_visibility`, `set_vibe_coding_block_action_visibility` |
| Versions | `list_vibe_coding_block_versions`, `restore_vibe_coding_block_version`, `duplicate_vibe_coding_block_from_version` |
| Data sources | `connect_vibe_coding_block_data_source`, `disconnect_vibe_coding_block_data_source`, `set_vibe_coding_block_data_source_sort`, `set_vibe_coding_block_data_source_record_filters` |

Editable settings via MCP are the same fields as the block's **Content → Settings** panel; sort and record filters are the same as the **Source** tab. Duplicating from a version is the safe way to try an alternative — the original keeps working while you experiment on the copy.

## Vibe coding gotchas (official)

From the official MCP docs — these hold for MCP-driven and Studio-driven edits alike:

- **A broken block can't be saved.** Code is validated before storage; on failure the block keeps its last working state and nothing is lost.
- **A version is a snapshot of the whole block** — code, settings, visibility, AND data source connections. Setting-only changes don't create a version.
- **Rolling back reverts more than the code.** Restoring a version also restores settings, visibility, and data source connections as they were at that point.
- **Changing the code resets action permissions.** Any code change rebuilds the block's record actions at default visibility — restrictions to user groups must be re-applied. (This is Hard Constraint 21 in SKILL.md, now officially documented: tighten Action permissions only after the LAST redeploy.)
- **A block with an unconnected data source saves without complaint**, then errors when the page loads. If a freshly created block looks broken but the code seems right, check its data source connection first.

## Browsing integrations (external data sources)

An integration is an external data source connected once per workspace (the builder says "integrations", the tools say "data sources" — same thing). Five read-only tools drill down from workspace to fields; each level needs an ID from the level above:

```
list_data_sources                          workspace's integrations
└── list_data_source_databases             a base, spreadsheet, or database
    └── list_data_source_schemas           SQL schemas — Supabase only (usually just `postgres`)
        └── list_data_source_tables        tables or sheets
            └── list_data_source_table_fields   fields, types, options, primary field
```

**Only five integration types are browsable/connectable through MCP today:** Softr Databases, Airtable, Google Sheets, Notion, and Supabase. Anything else still appears in `list_data_sources` but must be connected through the block's **Source** tab in Studio, with schema discovery via the manual workflows in [../datasources/fields.md](../datasources/fields.md#field-inspector-block).

`list_data_source_table_fields` also tells you **how fields must be referenced in `q.select()`**:

| Integration | Reference fields by |
|---|---|
| Airtable, Google Sheets, Notion | Name |
| Softr Databases, Supabase | ID (for Supabase, the SQL column name) |

Getting this wrong **fails silently** — the code compiles, saves, and looks right in the builder, then returns nothing at page load. If a block renders but its data is empty, check this first.

## Softr Database tools

For Softr's native databases the MCP goes far beyond browsing: `get_schema` (authoritative field-type + filter-operator reference — call it before building tables or filters), database/table/field CRUD, `list_views`, record reads (`list_records`, `search_records`, `get_record`), record writes (`create_record`, `create_records` batch, `update_record`), and `aggregate_data` for grouped summaries.

Known limits and behaviors (per official docs):

- Record field keys are **field IDs**, not labels — `list_fields` maps between them.
- Computed fields (formula, lookup, rollup, count) and system fields (created/updated time and by, autonumber, record ID) are read-only; a field's type cannot be changed after creation.
- **Nothing can be deleted through the MCP yet** — no record/table/field/database delete tools (docs say deletion is coming). Deletions happen in the builder.
- Limits: 100 records per `create_records` call, 200 records per read (silently capped, not an error), 2 group-by fields in `aggregate_data`. For big tables prefer a filter or aggregate over paging.

Typical Vibe Coding uses: "list every field on `Wigs` with id, name, type, and dropdown options", "what's the option id for `Payment status` = 'Partially paid'?", "show 3 sample records so we know value shapes", "verify the field id in my `q.select()` exists". This eliminates the field-id-typo / wrong-option-uuid class of bugs entirely.

## Two delivery paths for this skill

When generating a block, pick the delivery path by what's connected:

1. **MCP connected with Applications & Forms full access** — write the `.tsx` file locally first (it remains the source of truth and the reviewable artifact), then offer to deploy it directly: `create_vibe_coding_block` (or `update_vibe_coding_block_code` for edits), then `connect_vibe_coding_block_data_source` to wire up the data. Remember the action-permissions reset gotcha after every code push.
2. **No MCP (or read-only access)** — classic path: write the `.tsx` file and have the user paste it into Studio's Vibe Coding editor, then connect the data source in the **Source** tab themselves.

Either way, never deliver code inline in chat (JSX character corruption — see SKILL.md workflow step 5).

## When the MCP is not installed

If the user hasn't installed the MCP (and doesn't want to right now), fall back to the schema-discovery methods documented per source:

- **Softr Database:** bundled CLI script — see [../datasources/softr-database.md](../datasources/softr-database.md#bundled-cli-script-get-softr-database); or the `tablespace-with-tables` network paste — see [../datasources/fields.md](../datasources/fields.md#field-inspector-block).
- **Airtable:** bundled `get-airtable-base` script — see [../datasources/airtable.md](../datasources/airtable.md#bundled-cli-script-get-airtable-base).
- **Other sources:** Field Inspector block and vendor workflows in [../datasources/fields.md](../datasources/fields.md#field-inspector-block).

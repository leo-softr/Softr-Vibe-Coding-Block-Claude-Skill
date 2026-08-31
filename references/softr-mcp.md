# Softr MCP Server

The official Softr MCP server (`https://mcp.softr.io/mcp`) gives an AI assistant (Claude Code, Claude Desktop, claude.ai, Cursor, ChatGPT, Mistral) direct access to a Softr **workspace**: databases, applications, vibe coding blocks, integrations (external data sources), and workflows. On this workspace server, everything the assistant does happens as the connected user, with their permissions, and shows up in Studio like any other change.

**There are now TWO server classes.** Besides the workspace server above, Softr ships **per-application MCP servers** — one server per published app, exposing that app's data (and only what the app's pages actually use) through the app's own permission model. Different tools, different schema doc, and (apparently) a different identity model. See [Per-application MCP servers](#per-application-mcp-servers). (Live-enumerated 2026-08-31; roster facts below marked "roster-verified" mean the tool exists — its behavior was not necessarily exercised.)

**This file is a sibling concern to the [../datasources/](../datasources/) guides, which cover in-block data fetching (`useRecords` + `q.select()`).** The MCP runs at chat-build time, not inside the block. For Vibe Coding work it matters twice: it answers "what fields does this table have?" without any paste-ins, and it can create and deploy the block itself — no copy-paste into Studio.

> Historical note: this file was previously named `softr-database-mcp.md` and described a databases-only server with granular scopes. That server has since grown into the workspace-wide MCP documented here; the old "does NOT cover external sources" limitation is gone (see [Integrations](#browsing-integrations-external-data-sources)).

## Contents

- [What it covers](#what-it-covers)
- [Connection and auth](#connection-and-auth)
- [Permissions model](#permissions-model)
- [Vibe coding block tools](#vibe-coding-block-tools)
- [Adopting Studio-AI-generated code](#adopting-studio-ai-generated-code)
- [Vibe coding gotchas (official)](#vibe-coding-gotchas-official)
- [Application management tools](#application-management-tools)
- [Browsing integrations (external data sources)](#browsing-integrations-external-data-sources)
- [Softr Database tools](#softr-database-tools)
- [Workflows](#workflows)
- [Per-application MCP servers](#per-application-mcp-servers)
- [Two delivery paths for this skill](#two-delivery-paths-for-this-skill)
- [When the MCP is not installed](#when-the-mcp-is-not-installed)

## What it covers

| Area | What the assistant can do | Official docs |
|---|---|---|
| Databases | Query, filter, aggregate; create/update **and delete** records; build **and delete** tables, fields, databases | https://docs.softr.io/mcp/databases |
| Applications | **Create whole apps**; manage app users and login settings; swap an app's data source; read apps, pages, blocks, permissions, user groups; preview; publish — see [Application management tools](#application-management-tools) | https://docs.softr.io/mcp/apps |
| Vibe coding blocks | Create and edit blocks, manage settings, visibility, versions, data source connections | https://docs.softr.io/mcp/vibe-coding |
| Integrations | Browse external data sources connected to the workspace, down to field level | https://docs.softr.io/mcp/integrations |
| Workflows | Build, wire, test, and publish workflows — 26 tools and a 418-node trigger/action catalog; see [Workflows](#workflows) | https://docs.softr.io/mcp/workflows |

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
| Any block | `get_block` (roster-verified 2026-08-31; presumed to read any block type, not just vibe blocks — unconfirmed by a live call on a native block) |

Editable settings via MCP are the same fields as the block's **Content → Settings** panel; sort and record filters are the same as the **Source** tab. Duplicating from a version is the safe way to try an alternative — the original keeps working while you experiment on the copy.

## Adopting Studio-AI-generated code

When you pull a Studio-AI-generated block via `get_vibe_coding_block_code` to adopt into a project repo as source of truth: its output renders fine but ships with predictable defects. **Functional patterns in Studio output are platform-support evidence** (it surfaces undocumented capabilities before the docs do — see SKILL.md's "Platform truth sources"); **its code hygiene is not a pattern to imitate.** Cleanup pass before committing:

- **Run a formatter** — Studio output ships inconsistent indentation (observed: statements at column 0 inside a 4-space-indented component).
- **Hoist and consolidate brand hexes** into module-scope constants; flag near-duplicate hexes as probable unintended drift (observed: `#AE5E3D` vs `#B4603D` for one terracotta in a single block).
- **Fix React keys on settings-array loops** — Studio emits `key={item.label}`; use `key={index}` (see [anti-patterns.md](anti-patterns.md#editable-settings)).
- **Add the guards Studio omits** — conditional render for empty media settings, `whitespace-pre-line` on long-text settings, mobile nav for block-owned headers, `aria-hidden` on decorative glyphs.
- **Rewrite absolute self-domain URLs relative** (`https://<app>.softr.app/#x` → `/#x`) — observed as a configured setting value on a Studio-generated hero, 2026-08-31.

This is distinct from SKILL.md's no-churn rule: cleaning up a block you're ADOPTING into the repo is required; modernizing a deployed working block's syntax is still churn — don't do that.

## Vibe coding gotchas (official)

From the official MCP docs — these hold for MCP-driven and Studio-driven edits alike:

- **A broken block can't be saved.** Code is validated before storage; on failure the block keeps its last working state and nothing is lost.
- **A version is a snapshot of the whole block** — code, settings, visibility, AND data source connections. Setting-only changes don't create a version.
- **Rolling back reverts more than the code.** Restoring a version also restores settings, visibility, and data source connections as they were at that point.
- **Changing the code resets action permissions.** Any code change rebuilds the block's record actions at default visibility — restrictions to user groups must be re-applied. (This is Hard Constraint 21 in SKILL.md, now officially documented: tighten Action permissions only after the LAST redeploy.)
- **A block with an unconnected data source saves without complaint**, then errors when the page loads. If a freshly created block looks broken but the code seems right, check its data source connection first.

## Application management tools

The Applications area goes well beyond reads (all roster-verified 2026-08-31; behavior not individually exercised):

| Group | Tools |
|---|---|
| Apps | `list_applications`, `get_application`, `create_application` (create a whole app via MCP), `update_application_data_source` (point/swap the app's data source), `set_application_login` |
| App users | `add_application_user`, `remove_application_user`, `list_user_groups` |
| Pages / blocks / permissions | `list_pages`, `get_page`, `get_page_permissions`, `get_access_control`, `get_block` |
| Publish / preview | `preview_app`, `publish_app` |
| Workspace | `list_workspaces`, `get_workspace_integrations` (distinct from the [integrations drill-down](#browsing-integrations-external-data-sources) below) |

Combined with the database tools (`create_database` / `create_table` / `create_field`) and `create_vibe_coding_block` + `publish_app`, the tool set for scaffolding a full app end to end now exists. (Existence-verified only — that pipeline hasn't been run live; treat the first full scaffold as an experiment, not a routine.)

**Etiquette from the server's own instructions:** after changing a block, link the page as `https://studio.softr.io/applications/{applicationId}/pages/{pageId}`; offer `preview_app` or `publish_app`, but **only publish when the user asks**.

> **preview_app links are auth tokens.** Per the server's own instructions, a preview link **signs its opener in as the user who requested it** and lasts about a day. Give it only to that user, and mint a fresh one with another `preview_app` call rather than re-sending an old link. Never paste a preview link into a shared channel.

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

For Softr's native databases the MCP goes far beyond browsing: `get_schema` (authoritative field-type + filter-operator reference — call it before creating/updating tables, fields, or filters; the server's own instructions say "do not guess field types, options, or operators"), database/table/field CRUD **including deletes** (`delete_database`, `delete_table`, `delete_field`), `list_views`, record reads (`list_records`, `search_records`, `get_record`), record writes (`create_record`, `create_records` batch, `update_record`, `delete_record`, `delete_records` batch), and `aggregate_data` for grouped summaries.

**Call economy (from the server's own instructions):** `get_table` returns a table's metadata AND all its field definitions in one call; `list_fields` returns the fields alone. Call ONE of them once per table and reuse the result — never both. (Sensible extension: re-fetch only after you changed the table's fields yourself.)

**get_schema, live-confirmed 2026-08-31:** `readOnlyFieldTypes` = AUTONUMBER, COUNT, CREATED_AT, CREATED_BY, FORMULA, LOOKUP, RECORD_ID, ROLLUP, UPDATED_AT, UPDATED_BY (matches this file's long-standing claim verbatim). The `LINKED_RECORD` value example is `["record-id-1", "record-id-2"]` — independently corroborating the verified string-array write shape in [../datasources/softr-database.md](../datasources/softr-database.md). Operator families include relative-date `IS_WITHIN` / `IS_NOT_WITHIN` ("last 7 days"), ternary `IS_BETWEEN` / `IS_NOT_BETWEEN`, and `AND`/`OR` composites. **Schema-drift caution:** the workspace server's `get_schema` and the [per-application servers'](#per-application-mcp-servers) `get_schema` have drifted — the per-app catalog lists creatable types the workspace one omits (ADDRESS, PROGRESS, TIME, DATE_RANGE, BUTTON), and even the operator NAMES differ between server kinds (workspace `GREATER_THAN` / `DOES_NOT_CONTAIN` vs per-app `GT` / `DOES_NOT_CONTAINS`) — so filter payloads are not portable between them. Always call `get_schema` on the server you are actually using.

Known limits and behaviors (per official docs):

- Record field keys are **field IDs**, not labels — `list_fields` maps between them.
- Computed fields (formula, lookup, rollup, count) and system fields (created/updated time and by, autonumber, record ID) are read-only; a field's type cannot be changed after creation.
- **Deletion now exists** (supersedes the earlier "nothing can be deleted through the MCP yet" finding): `delete_record`, `delete_records` (batch), `delete_field`, `delete_table`, and `delete_database` are all in the roster (verified 2026-08-31), and per-app servers add `delete_record` + `batch_delete_records`. Roster-verified only — no destructive call was made, so which Databases permission level gates them and how cascades behave (e.g. deleting a table with linked records) are untested. Treat every delete as irreversible; no soft-delete is documented.
- **Attachment writes take a URL and copy the file.** `create_record` / `update_record` accept
  `{ filename, url }` on an ATTACHMENT field with any publicly reachable URL; Softr fetches it, stores its
  own copy and generates thumbnails, so backfilling images from another system is one write per record
  with no upload step. Verified 2026-08-26 — see [../datasources/writing.md](../datasources/writing.md#attachment).
- **`update_field` silently ignores `allowMultipleEntries` nested inside `options`** — it is a TOP-LEVEL
  field property; the call succeeds and changes nothing (verified 2026-08-26; the server has grown
  substantially since — deletes added by 2026-08-31 — so this write surface is worth a re-test when
  next touched live). To flip a LINKED_RECORD
  field between single and multi, `PUT` it via the Tables API with `allowMultipleEntries` at top level —
  and always echo `options.inverseLinkFieldId` in that PUT, because omitting it severs the inverse
  pairing. Full write-up, including the silent on-write clobbering of single-valued link pairs and the
  truthy-`[]` empty-link read shape:
  [../datasources/writing.md](../datasources/writing.md#linked-record-write-traps-verified-live-2026-08-26).
- Limits: 100 records per `create_records` call, 200 records per read (silently capped, not an error), 2 group-by fields in `aggregate_data`. For big tables prefer a filter or aggregate over paging.

Typical Vibe Coding uses: "list every field on `Wigs` with id, name, type, and dropdown options", "what's the option id for `Payment status` = 'Partially paid'?", "show 3 sample records so we know value shapes", "verify the field id in my `q.select()` exists". This eliminates the field-id-typo / wrong-option-uuid class of bugs entirely.

## Workflows

Softr Workflows are automations built from trigger + action nodes, and the MCP can build, wire, test, and publish them — a **26-tool suite** (roster-verified 2026-08-31; `list_node_types` called live, the build/publish loop itself not yet exercised end to end):

| Group | Tools |
|---|---|
| Workflow lifecycle | `create_workflow`, `get_workflow`, `get_workflow_url`, `list_workflows`, `rename_workflow`, `update_workflow_configuration`, `publish_workflow`, `unpublish_workflow` |
| Node management | `add_node`, `add_branch_node`, `create_branch`, `delete_node`, `duplicate_node`, `rename_node`, `reorder_node`, `reorder_multiple_nodes`, `replace_node`, `replace_trigger_node`, `update_node_inputs`, `update_node_note`, `update_node_continue_on_error` |
| Discovery / testing | `list_node_types`, `get_node_specifications`, `get_dynamic_input_options`, `test_node`, `get_node_output` |

**The node catalog is huge** — live-enumerated 2026-08-31: **418 node types (58 triggers + 360 actions) across 56 applications.** The parts that matter most for this skill:

- **Softr-native triggers:** one-time + recurring schedules, `WEBHOOK` (inbound webhook), `SOFTR_EMAIL_RECEIVED` (inbound email! — delivery mechanism not captured), Softr Databases record events (added / updated / deleted / meets-conditions / enters-view / "run custom workflow on selected records"), Softr Apps events (Add Record form submitted, Edit Record form submitted, form submitted, user added, comment added) — and **"Run Custom Workflow action triggered"**, which by its name is the receiving end of the vibe block's `TRIGGER_CUSTOM_WORKFLOW` NavigationAction (name-based inference; the pairing has not been wired live). See SKILL.md's NavigationAction action-types list.
- **Softr-native actions:** `BRANCH`, `FILTER`, `WAIT`, `LOOP_ACTION_GROUP` (run each list item through the same steps), `SOFTR_SEND_EMAIL`, `CALL_API` (REST), `WEBPAGE_SCRAPPER`, `PDF_TO_TEXT`, `COMPRESS_FILES` (zip + download link), `TRANSFORM_DATA`, `RESPONDED_TO_WEBHOOK` (custom HTTP response to the webhook caller); Softr DB record CRUD incl. bulk update/delete and find; Softr Apps user management (find / create / delete / deactivate / activate / invite user, send push notification).
- **`CUSTOM_CODE`:** runs custom **JavaScript or Python** inside a workflow.
- **AI actions:** Softr AI, OpenAI, Anthropic, Gemini, and Mistral each ship Write / Summarize / Categorize / Custom-prompt nodes; OpenAI adds gpt-image-2 image generation. Pinecone, Firecrawl, Replicate, and Linkup nodes exist too.
- **Integration apps (top of 56):** Stripe (36 nodes), QuickBooks (24), ActiveCampaign (23), SharePoint (22), Asana (18), Gmail/Attio/Brevo/Resend (12 each), ClickUp/Zendesk (10), Airtable/Notion/Cal.com/HubSpot/Xero/DocuSign/Apollo (9 each), Sheets/Excel (8), monday/SQL/Jira (7), Slack/Telegram (6), plus Salesforce, Coda, Calendly, Twilio, Zoom, Linear, Trello, form tools (Typeform/Tally/Jotform/Fillout), and more.

**Mechanics from the server's own instructions:**

- Node inputs can embed **references to another node's runtime output**, a loop's current item, or named date/time tokens.
- **Test-first is mandated:** every testable node needs a test run before its outputs become referenceable by downstream nodes. Each node carries a `testRunMode` — `REAL_ONLY`, `MOCK_ONLY`, or `MOCK_AND_REAL` — so some nodes can only be tested against real side effects while others mock.
- **Workflows are workspace-level, not part of an app**: `preview_app` / `publish_app` do not apply. Link a workflow as `https://studio.softr.io/workflow/{workflowId}`.

**Why this matters to block work:** Softr Workflows are now the Softr-native answer to the "block writes to its own table, backend cascades the rest" pattern — for **Softr Database backends** what [airtable-automations.md](airtable-automations.md) is for Airtable backends. See the cross-table alternatives in [../datasources/writing.md](../datasources/writing.md#cross-table-operations).

## Per-application MCP servers

A separate product class from the workspace server (live-observed 2026-08-31 on two connected app servers): **one MCP server per published Softr app**, exposing that app's data to MCP clients. How these servers are provisioned/connected was not captured — check the app's settings in Studio or the official docs when setting one up.

**Tools (12):** `list_tables`, `describe_table`, `get_schema`, `get_records`, `get_record`, `get_linked_records`, `get_current_user`, `create_record`, `update_record`, `delete_record`, `batch_update_records`, `batch_delete_records`.

**Live-observed semantics:**

- **The table catalog is derived from the app itself.** `list_tables` returns only tables the app's pages actually use, each with an `operations` array (`read` / `create` / `update` / `delete`) mirroring the app's configured actions — read-only tables genuinely appear read-only. Each table also carries `context.pages` (which app pages use it) and `operationLabels` (the app's actual button labels: "Add record", "Edit", "Delete").
- An app may connect **multiple distinct data sources**; always call `list_tables` first for the full catalog before concluding data doesn't exist.
- `get_current_user` exists, and combined with the action-scoped catalog this implies the server operates in an **app-user context** rather than the builder identity the workspace server uses (inferred — not confirmed by a live `get_current_user` call).
- **Field keys in records are field IDs, not labels** — same rule as everywhere in Softr DB land; on these servers the mapping tool is `describe_table` (not `list_fields`).
- Its `get_schema` returns a **richer field-type catalog than the workspace server's**: creatable types add ADDRESS, PROGRESS, TIME, DATE_RANGE, BUTTON; SELECT documents `choices: array<{id, label, color}>` + `allowToAddNewChoice`; LONG_TEXT documents TEXT|HTML|MARKDOWN formats; ATTACHMENT documents `fileType` + `showAs PREVIEW|BADGE`; PERCENT documents `showAs NUMBER|PROGRESS_BAR|PROGRESS_RING`. Read-only list matches the workspace server.
- **Documented conventions** (unlike the workspace server's silent caps): pagination is `page` (1-based) + `pageSize` (max 100) with `total` and `hasMore` in the response; timestamps are UTC `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'` for reads AND writes; errors return `{code, error, suggestion}` with machine-readable codes (NOT_FOUND, VALIDATION_ERROR, PERMISSION_DENIED, INVALID_REQUEST, INTERNAL_ERROR). Do not assume the workspace server's limits (200-record silent read cap, etc.) transfer here, or vice versa.
- Filter operators use the per-app naming (`GT`/`LT`/`GTE`/`LTE`, `DOES_NOT_CONTAINS`, `IS_WITHIN` relative dates, `IS_ONE_OF`/`IS_NONE_OF`, `HAS_ALL_OF`/`HAS_NONE_OF` (the latter flagged legacy in the schema), `INLINE_CONTAINS`) with per-operator supported-type lists — see the schema-drift caution in [Softr Database tools](#softr-database-tools).

**What they are NOT:** a delivery path for blocks. Per-app servers serve a published app's **data** at runtime; they cannot create, edit, or deploy vibe coding blocks — that stays on the workspace server.

## Two delivery paths for this skill

When generating a block, pick the delivery path by what's connected:

1. **WORKSPACE MCP server connected with Applications & Forms full access** (a per-application server does not count — it cannot create or deploy blocks; see the section above) — write the `.tsx` file locally first (it remains the source of truth and the reviewable artifact), then offer to deploy it directly: `create_vibe_coding_block` (or `update_vibe_coding_block_code` for edits), then `connect_vibe_coding_block_data_source` to wire up the data. Remember the action-permissions reset gotcha after every code push. After deploying, link the Studio page (`https://studio.softr.io/applications/{applicationId}/pages/{pageId}`) and offer `preview_app` / `publish_app` — publish only when asked, and mind the [preview-link auth warning](#application-management-tools).
2. **No workspace MCP (or read-only access)** — classic path: write the `.tsx` file and have the user paste it into Studio's Vibe Coding editor, then connect the data source in the **Source** tab themselves.

Either way, never deliver code inline in chat (JSX character corruption — see SKILL.md workflow step 5).

## When the MCP is not installed

If the user hasn't installed the MCP (and doesn't want to right now), fall back to the schema-discovery methods documented per source:

- **Softr Database:** bundled CLI script — see [../datasources/softr-database.md](../datasources/softr-database.md#bundled-cli-script-get-softr-database); or the `tablespace-with-tables` network paste — see [../datasources/fields.md](../datasources/fields.md#field-inspector-block).
- **Airtable:** bundled `get-airtable-base` script — see [../datasources/airtable.md](../datasources/airtable.md#bundled-cli-script-get-airtable-base).
- **Other sources:** Field Inspector block and vendor workflows in [../datasources/fields.md](../datasources/fields.md#field-inspector-block).

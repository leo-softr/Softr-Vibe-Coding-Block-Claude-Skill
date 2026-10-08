# Softr Database

## Overview
Softr's native built-in database. No external account or integration required. Available on all plans with support for 1M+ records.

## Connection Setup
No setup needed. Softr Database is available by default in every Softr app. Create tables directly from the Softr admin dashboard under the "Data" section. Import data via CSV, one-click migration from Airtable, or AI-assisted table generation.

## AI-Assisted Workflows

Softr publishes an official MCP server (`https://mcp.softr.io/mcp`) that lets the AI read Softr DB schema and field IDs directly — eliminating the manual "paste `tablespace-with-tables` JSON" step. The same server can also browse connected Airtable / Google Sheets / Notion / Supabase integrations, and can create and deploy Vibe Coding blocks. For setup, permissions, and the full tool catalog, see [../references/softr-mcp.md](../references/softr-mcp.md).

## Vibe Coding Field IDs
Field IDs are short alphanumeric codes (e.g., `"xgETy"`, `"TLhWF"`). These codes are NOT human-readable names.

```jsx
// CORRECT - use the alphanumeric field ID
q.select({ name: "xgETy" })

// WRONG - human-readable names do not work
q.select({ name: "First Name" })
```

Find field IDs in this order of preference:

1. **Softr MCP server** (recommended when working with an AI assistant) — the AI calls schema/list-fields tools directly. See [../references/softr-mcp.md](../references/softr-mcp.md).
2. **`get-softr-database` CLI script (bundled)** — a Python CLI bundled with this skill at `~/.claude/skills/softr-vibe-coding/tools/get-softr-database.py`. Exports the full schema (every table, field, dropdown option UUID) to `~/Desktop/softr-database-<id>-<timestamp>.json`. Stdlib only, no `pip install`. See [Bundled CLI script](#bundled-cli-script-get-softr-database) below.
3. **Network inspector** — DevTools -> Network -> filter `tablespace-with-tables` for the full schema including dropdown option UUIDs. Paste the JSON into chat to share with an AI when the MCP isn't installed.
4. **Inline in Studio** — click a field's name in the Data tab; the ID appears in the field-edit drawer.

The generic Field Inspector pattern with empty `q.select({})` does NOT work for Softr Database — see [fields.md](fields.md#field-inspector-block).

**Field ids are per database.** Rebuilding a database (for example, to move an app into another workspace) gives every table and field a new id, so every block's field and table references have to change. Do the remap with a script: a one-to-one old-to-new map keyed on table and field names rewrote 775 references in 15 blocks (LCDB rebuild, 2026-10-05). Prove a remap by reversing it back to the original, byte for byte, and by each push's `sourceSha256` ([protocol](../references/softr-mcp.md#verifying-a-push--the-deployed-source-is-the-only-proof)). Match only real field references (`q.select` values, `where` / `orderBy` aliases). Counting every quoted five-character literal overcounted by 191 ordinary words such as `error`.

## Bundled CLI script: `get-softr-database`

A Python CLI bundled with this skill that exports a complete Softr Tables database schema (every table, every field, all dropdown option UUIDs) to a timestamped JSON file on your Desktop. Stdlib only — no `pip install` required.

**Script location after `npx softr-vibe-coding@latest init`:**

```
~/.claude/skills/softr-vibe-coding/tools/get-softr-database.py
```

**Run it directly:**

```bash
python3 ~/.claude/skills/softr-vibe-coding/tools/get-softr-database.py <database_id>
```

It prompts for your Softr API key (input hidden via `getpass`). To skip the prompt entirely, pass via env var:

```bash
SOFTR_API_KEY=xxx python3 ~/.claude/skills/softr-vibe-coding/tools/get-softr-database.py <database_id>
```

Run with no args to be prompted for both the database ID and API key.

**Output:** `~/Desktop/softr-database-<databaseId>-<YYYYMMDD-HHMMSS>.json` containing:

```json
{
  "exportedAt": "...",
  "source": "https://tables-api.softr.io/api/v1",
  "databaseId": "...",
  "database": { /* full database metadata */ },
  "tableCount": N,
  "fieldCount": M,
  "tables": [ /* every table with its full fields[] array */ ]
}
```

**Optional alias** for a shorter command. Add to your `~/.zshrc` or `~/.bashrc`:

```bash
alias get-softr-database='python3 ~/.claude/skills/softr-vibe-coding/tools/get-softr-database.py'
```

After `source ~/.zshrc`, just run `get-softr-database <database_id>` from anywhere.

**Get your Softr API key:** Softr workspace settings → API keys → create a new key with read access to the target database.

**When to use vs the MCP:** the MCP server is better for AI-assisted workflows (the assistant calls schema tools directly without any user action). This CLI script is better when you want a portable JSON file — for sharing in chat, archiving alongside your project, diffing across schema versions, or pasting a single big blob into Claude. The two approaches don't conflict; many projects use both.

## Supported Fields

| Field Type     | Writable | Notes |
|----------------|----------|-------|
| Text           | Yes      | |
| Number         | Yes      | |
| Date           | Yes      | Date-semantics fields take `"yyyy-MM-dd"`; timestamp fields take `new Date().toISOString()` (verified 2026-08-25) |
| File / Image   | Yes      | |
| Checkbox       | Yes      | |
| Dropdown       | Yes      | Write the option **LABEL string**, exactly matching a defined choice (verified 2026-08-25; supersedes the old option-UUID rule). See [writing.md](writing.md#dropdown--single-select-softr-database) |
| Relationship   | Yes      | Linked records to other Softr Database tables. Write as an **array of record-id strings**, e.g. `[recordId]` (verified 2026-08-25) |
| Formula        | Read-only | Booleans return as strings: use `=== "1"` for true, `=== "0"` for false |

This table is the coarse block-side view. The full current catalog is larger — Rating, Duration, Currency, Percent, plus computed Lookup/Rollup/Count and system fields — and is best fetched live from the MCP, authoritative **for the server you're calling** (`database_get_field_reference` on the workspace server, `get_schema` on a per-app server): the per-app servers document a fuller catalog than the workspace server (adding Address, Progress, Time, Date range, Button, and display options like Percent's progress-bar/ring — still missing from the workspace reference on 2026-10-01), and the two have also differed on operator names — see [../references/softr-mcp.md](../references/softr-mcp.md#softr-database-tools).

## Rate Limits
No API rate limits. Softr Database queries run internally without external API calls, making it the best choice for high-traffic applications.

## Gotchas
- **Formula boolean values are strings.** A formula that evaluates to true returns `"1"`, not `true`. Always compare with `=== "1"` or `=== "0"`.
- **Field IDs are opaque codes.** You cannot guess them from column names. Look them up via the ranked list above (MCP `database_list_fields` / bundled CLI / network inspector / Studio field drawer) — the generic Field Inspector block does NOT work for Softr Database.
- **Relationships** work similarly to linked records in Airtable but use Softr's internal record IDs.
- **A checkbox reads back as a real boolean** (`true` / `false`), not a string like a formula's boolean above (verified live 2026-09-18).
- **Formula arithmetic is floating-point.** `1.15 * 400` rendered as `459.99999999999994` (seen 2026-09-18; the stored 1.15 was exact, the product was not). Wrap money and any other displayed product in `ROUND(…, 2)`.
- **An EMAIL field does not enforce one address.** A full read of a production table on 2026-09-01 found EMAIL-typed fields holding comma-separated lists. Split and trim before treating the value as one address. Passed whole into an email's To field, the addresses all see each other.
- **A link's `label` is the linked table's display field** (verified 2026-09-19). Change that table's display field in Studio and every label changes with it, so anything that matches on a label (block code, a Source condition, a workflow reference such as `[*].label`) silently stops matching. Match on the record id, or read the value from its own field.
- **A NUMBER field's precision rounds only Softr's own display.** At precision 0 the database stored 1.5 while Softr's views showed it rounded. Changing precision changes no stored value, and the MCP and blocks read the stored decimals: quarter hours and cents read back unchanged before and after a precision change (LCDB, 2026-10-07 to 08). A block cannot rely on precision to reject decimals.
- **A CREATED_AT field added to an existing table is filled in for the existing records with their own creation time**, so a creation-order tie-breaker can be added later (LCDB, 2026-10-07: 101 existing records). Like any read-only field, it stays out of every write select ([anti-patterns.md](../references/anti-patterns.md#mutations)).
- **Users-table sync from a Softr Database table (set in Studio) turns every row with a value in the mapped email field into an app user** (and invites it, when the sync is set to invite; whether an invite fires for a row a block creates was not checked), whatever its other fields say: inactive rows and rows that stand for a team rather than a person included. Synced users land in no custom group unless a condition puts them in one. The sync also runs the other way: an existing app user with no matching row got a new row holding only the email (blank name and status), and blocks then showed it as a nameless active record. Map the sync to a field filled only for people who should sign in, and give blocks a rule for rows with no name or status (LCDB, 2026-10-05 to 08; the HubSpot equivalent is in [hubspot.md](hubspot.md#user-sync)).
- **An "entered by" or "updated by" value a block writes is self-reported.** The browser puts it in the save body, so anyone who can reach the write endpoint can write any email there. Treat it as a convenience, not an audit trail. Softr Database's CREATED_BY and UPDATED_BY system fields may be the tamper-evident alternative; whether they record the app user (not the builder) when a vibe block writes is unverified, so check on one test record first.
- **Softr's Zapier "Update Record" action replaces a multi-link field's whole set** (confirmed by a Studio test, 2026-09-01). A zap that writes one record id into a link that allows several wipes the earlier links. Write the existing ids plus the new one.

## Best For
- New projects starting from scratch
- High-traffic applications (no rate limit concerns)
- Teams that do not already have data in an external platform
- Apps requiring the simplest possible setup

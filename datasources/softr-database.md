# Softr Database

## Overview
Softr's native built-in database. No external account or integration required. Available on all plans with support for 1M+ records.

## Connection Setup
No setup needed. Softr Database is available by default in every Softr app. Create tables directly from the Softr admin dashboard under the "Data" section. Import data via CSV, one-click migration from Airtable, or AI-assisted table generation.

## AI-Assisted Workflows

Softr publishes an official MCP server (`https://mcp.softr.io/mcp`) that lets the AI read Softr DB schema and field IDs directly — eliminating the manual "paste `tablespace-with-tables` JSON" step. For setup, scopes, the 20 tools, and the limitation that this only covers Softr DB (not external sources), see [../references/softr-database-mcp.md](../references/softr-database-mcp.md).

## Vibe Coding Field IDs
Field IDs are short alphanumeric codes (e.g., `"xgETy"`, `"TLhWF"`). These codes are NOT human-readable names.

```jsx
// CORRECT - use the alphanumeric field ID
q.select({ name: "xgETy" })

// WRONG - human-readable names do not work
q.select({ name: "First Name" })
```

Find field IDs in this order of preference:

1. **Softr Database MCP** (recommended when working with an AI assistant) — the AI calls schema/list-fields tools directly. See [../references/softr-database-mcp.md](../references/softr-database-mcp.md).
2. **`get-softr-database` CLI script (bundled)** — a Python CLI bundled with this skill at `~/.claude/skills/softr-vibe-coding/tools/get-softr-database.py`. Exports the full schema (every table, field, dropdown option UUID) to `~/Desktop/softr-database-<id>-<timestamp>.json`. Stdlib only, no `pip install`. See [Bundled CLI script](#bundled-cli-script-get-softr-database) below.
3. **Network inspector** — DevTools -> Network -> filter `tablespace-with-tables` for the full schema including dropdown option UUIDs. Paste the JSON into chat to share with an AI when the MCP isn't installed.
4. **Inline in Studio** — click a field's name in the Data tab; the ID appears in the field-edit drawer.

The generic Field Inspector pattern with empty `q.select({})` does NOT work for Softr Database — see [fields.md](fields.md#field-inspector-block).

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
| Date           | Yes      | |
| File / Image   | Yes      | |
| Checkbox       | Yes      | |
| Dropdown       | Yes      | |
| Relationship   | Yes      | Linked records to other Softr Database tables |
| Formula        | Read-only | Booleans return as strings: use `=== "1"` for true, `=== "0"` for false |

## Rate Limits
No API rate limits. Softr Database queries run internally without external API calls, making it the best choice for high-traffic applications.

## Gotchas
- **Formula boolean values are strings.** A formula that evaluates to true returns `"1"`, not `true`. Always compare with `=== "1"` or `=== "0"`.
- **Field IDs are opaque codes.** You cannot guess them from column names. Use the Field Inspector block to find them.
- **Relationships** work similarly to linked records in Airtable but use Softr's internal record IDs.

## Best For
- New projects starting from scratch
- High-traffic applications (no rate limit concerns)
- Teams that do not already have data in an external platform
- Apps requiring the simplest possible setup

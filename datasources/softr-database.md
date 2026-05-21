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
2. **Network inspector** — DevTools -> Network -> filter `tablespace-with-tables` for the full schema including dropdown option UUIDs. Paste the JSON into chat to share with an AI when the MCP isn't installed.
3. **Inline in Studio** — click a field's name in the Data tab; the ID appears in the field-edit drawer.

The generic Field Inspector pattern with empty `q.select({})` does NOT work for Softr Database — see [fields.md](fields.md#field-inspector-block).

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

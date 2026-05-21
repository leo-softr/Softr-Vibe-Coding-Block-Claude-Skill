# Softr Database MCP Server

Out-of-band integration for AI-assisted Vibe Coding workflows. The MCP server lets the AI assistant (Claude Code, Claude Desktop, Cursor, ChatGPT, Mistral) read schema, list field IDs, query records, and write data directly into Softr Databases — eliminating the manual "paste `tablespace-with-tables` JSON" step and removing transcription errors on field IDs and dropdown option UUIDs.

**This file is a sibling concern to [../datasources/softr-database.md](../datasources/softr-database.md), which covers in-block data fetching (`useRecords` + `q.select()`).** The MCP runs at chat-build time, not inside the block. Same parallel as [airtable-automations.md](airtable-automations.md) sits next to [../datasources/airtable.md](../datasources/airtable.md).

## Connection

- **Server URL:** `https://mcp.softr.io/mcp`
- **Transport:** streamable HTTP
- **Auth:** OAuth (pre-configured for Claude / Cursor / ChatGPT / Mistral) or Personal API Token (`Settings → API Tokens` in Softr)
- **Official docs:** https://docs.softr.io/mcp-server

## Install (Claude Code)

```bash
claude mcp add --transport http softr https://mcp.softr.io/mcp
```

Then start a new Claude Code session and run `/mcp` to complete the OAuth authorization in the browser. See [the Softr docs](https://docs.softr.io/mcp-server) for Cursor / ChatGPT / Mistral / custom client setup.

## Permissions (three granular scopes)

Grant only what you need:

| Scope                       | Use case for Vibe Coding                                              |
|-----------------------------|-----------------------------------------------------------------------|
| `databases.records:read`    | AI discovers field IDs, dropdown UUIDs, verifies value shapes         |
| `databases.records:write`   | AI mutates live data (e.g. seeding test records, bulk updates)        |
| `databases.schema:write`    | AI provisions databases / tables / fields for you                     |

For block-writing workflows, **read scopes are the most valuable** — they cover the AI's schema-discovery needs (the bottleneck the MCP solves) without any blast-radius into live data. Add write scopes only when you want the AI to mutate records; schema-write only when you want it to provision tables.

## Tools available (20 total)

- **Databases (4):** list / get / create / update
- **Tables (8):** list tables, list fields, list views, get table schema, create / update tables, create / update fields
- **Records (8):** list / get / create (batch ≤ 100) / update / delete + filter-based and view-filtered search

## Why this changes Vibe Coding workflows

Without the MCP, the AI needs schema shared manually — either paste `tablespace-with-tables` network JSON or describe fields by name. Both are slow, and verbal-name approaches lose dropdown option UUIDs entirely without a second copy step.

With the MCP installed, you can ask things like:

- "List every field on the `Wigs` table with id, name, type, and dropdown options."
- "What's the option id for `Wigs.Payment status` = 'Partially paid'?"
- "Show me 3 sample records from `Wig Services` so we know the value shapes."
- "Verify the field id I used for `q.select({ status: 'sel...' })` exists on this table."

The AI then writes `q.select()` keys and write payloads against the live schema, eliminating an entire class of "field id typo" / "wrong option uuid" bugs.

## Scope: Softr Database only

The MCP server exposes Softr's **native** databases only. It does NOT proxy external sources (Airtable, Google Sheets, HubSpot, Notion, Xano, etc.) — those still need the schema-discovery workflows documented in [../datasources/fields.md](../datasources/fields.md#field-inspector-block) (Field Inspector block, vendor APIs, network inspector paste, etc.). If your Softr app blends Softr DB with external sources, the MCP helps only with the Softr DB tables.

## When the MCP is not installed

If the user hasn't installed the MCP (and doesn't want to right now), fall back to the schema-sharing methods documented in [../datasources/fields.md](../datasources/fields.md#field-inspector-block) — primarily the `tablespace-with-tables` network paste, which gives the AI everything it needs in one shot.

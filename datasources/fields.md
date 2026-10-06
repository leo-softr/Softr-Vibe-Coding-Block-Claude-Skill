# Field Types & Debug Utilities

The `getFieldValue()` helper, field type shapes, record structure, and diagnostic blocks.

## Table of Contents

- [getFieldValue -- Never Render Raw Fields](#getfieldvalue----never-render-raw-fields)
- [Debugging Error #31](#debugging-error-31)
- [Common Field Type Shapes](#common-field-type-shapes)
- [Record Structure](#record-structure)
- [Debug Utilities](#debug-utilities)

## getFieldValue -- Never Render Raw Fields

**Every field value rendered in JSX must pass through `getFieldValue()`** before rendering, parsing, or comparing. Softr returns many field types as `{label, ...}` objects, not strings. Rendering them raw crashes React with error #31 ("Objects are not valid as a React child"). The cost of unnecessary `getFieldValue()` calls is zero; the cost of debugging error #31 is 30 minutes.

```jsx
var getFieldValue = function(f) {
  if (f == null) return "";
  if (Array.isArray(f)) {
    return f.map(function(x) {
      if (x && typeof x === "object") return x.label || x.name || x.title || "";
      return String(x);
    }).filter(Boolean).join(", ");
  }
  if (typeof f === "object") return f.label || f.name || f.title || "";
  return String(f);
};
```

Property priority: `label` first (most common in Softr formatted fields), then `name`, then `title`.

Apply `getFieldValue()` everywhere you read fields:
- Table cells, badges, tooltips: `<td>{getFieldValue(f.subject)}</td>`
- Date parsing: `toLocalDate(getFieldValue(f.dueDate))` for date-only fields ([below](#date-only-fields-arrive-as-midnight-utc)), `new Date(...)` for real timestamps -- raw value might be `{label: "2025-12-01"}`
- Number parsing: `parseInt(getFieldValue(f.count), 10)` -- formula numbers come back as objects
- String methods: `getFieldValue(f.status).toLowerCase()`
- Inside `useMemo` normalizers, BEFORE storing into state -- prevents the object from propagating

For companion helpers (`getLinkedNames`, `getLinkedItems`) used in helper block consumers, see [../references/helper-blocks.md](../references/helper-blocks.md).

### Date-only fields arrive as midnight UTC

*Verified live 2026-09-18 (Softr Database).* A date field without a time arrives as midnight UTC.
`new Date()` parses it as UTC, so anywhere west of Greenwich (New York, for one) date-fns renders
the **previous day**. Parse date-only values as local dates, and keep the default parse for real
timestamps:

```jsx
var DATE_ONLY_RE = /^(\d{4})-(\d{2})-(\d{2})(?:[T ]00:00(?::00(?:\.0+)?)?(?:Z|\+00:00)?)?$/;

function toLocalDate(raw) {
  if (typeof raw === "string") {
    var m = raw.match(DATE_ONLY_RE);
    if (m) return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  }
  return new Date(raw);
}
```

A real timestamp at exactly midnight UTC matches the pattern too, so call `toLocalDate` only on
fields you know are date-only.

## Debugging Error #31

If React crashes with error #31 ("Objects are not valid as a React child"), open console on the first record that crashes and run:

```js
JSON.stringify(record.fields, null, 2).slice(0, 1000)
```

You'll see exactly which field is an object. Add `getFieldValue()` around it.

## Common Field Type Shapes

| Field type | Value shape |
|---|---|
| Text, Email, URL, Phone, Address | `string` |
| Number, Currency, Percent, Progress, Autonumber | `number or null` |
| Checkbox | `string or boolean` |
| Date, DateTime, Time, Created At, Updated At | `string` (ISO) |
| Date Range | `{ from: string, to: string }` |
| Rating, Duration | `string or number or null` |
| Select | `{ label: string, id: string }` |
| Linked Record (via useRecord/useRecords) | `{ label: string, id: string }` — usually an array of these, but a link can arrive as a **single object** (verified live 2026-09-18); normalise with `Array.isArray(v) ? v : (v ? [v] : [])` |
| Linked Record (via useLinkedRecords) | `{ id: string, title: string }` -- different! |
| User, Created By, Updated By | `{ avatarUrl, id, name, email }` |
| Attachment | `{ filename, id, type, url }` |
| Formula | `string or number` |
| Lookup (multi-value) | array of **strings**, one element per linked record: `["#1042#"]`, and `[]` when empty (verified live 2026-09-19, Softr Database). `getFieldValue()` joins it for display; a `contains` filter on it tests each element ([reading.md](reading.md#operator-semantics-on-the-server)) |

## Record Structure

Records returned by `useRecords` have: `{ id: "recXXX", fields: { alias1: value, alias2: value } }`. Keys inside `fields` are the **aliases from `q.select()`**, NOT the original field names.

```jsx
var rawRecord = items && items[0];
var f = rawRecord ? rawRecord.fields || {} : {};
var name = f.firstName || "";
```

## Debug Utilities

Two throwaway diagnostic blocks you can drop into a page to diagnose data problems. Neither is meant for production -- delete or hide them once the issue is resolved. During development, drop them on a `/debug` page whose VIEW permission is limited to admins. A page that is merely left out of the navigation is still reachable by URL, and its blocks' endpoints answer anyone the page lets in (see [softr-mcp.md](../references/softr-mcp.md#what-the-server-enforces-on-a-blocks-data-endpoints)).

### Field Inspector Block

Use when records load but fields come back empty, or when you're not sure which Field IDs exist on a table.

**Important caveat for Softr Database:** `q.select({})` returns record IDs with empty `fields: {}` -- it does NOT dump all fields. Verified by direct experiment, April 2026. Use one of the alternatives below for Softr DB. The empty-select pattern still works for Airtable and other sources where the field keys come back automatically (for Airtable / Notion / Google Sheets those keys are field NAMES — the same names `q.select()` uses; see the name-vs-ID rule in [../references/softr-mcp.md](../references/softr-mcp.md#browsing-integrations-external-data-sources)).

For Airtable and other non-Softr-DB sources:

```jsx
import { useRecords, q } from "@/lib/datasource";
var select = q.select({});
export default function Block() {
  var result = useRecords({ select: select, count: 3 });
  if (result.status === "pending") return <div className="container py-6"><div className="content"><p>Loading...</p></div></div>;
  var records = (result.data && result.data.pages) ? result.data.pages.flatMap(function(p) { return p.items; }) : [];
  return (
    <div className="container py-6">
      <div className="content">
        <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
          {JSON.stringify(records.slice(0, 2), null, 2)}
        </pre>
      </div>
    </div>
  );
}
```

**For Airtable specifically, the bundled `get-airtable-base` script is a more comprehensive alternative** — it exports the full base schema (every table, every field with `fld...` IDs and column names, relationships, webhooks, interfaces) to a Desktop folder via the Airtable Web API. Run with `bash ~/.claude/skills/softr-vibe-coding/tools/get-airtable-base` (requires `jq` — `brew install jq` on macOS). Best when you want a portable schema snapshot, are documenting field IDs alongside column names per the [airtable.md maintainability mitigation](airtable.md#maintainability-gotcha), or need to audit lookup/rollup/sync relationships. Full usage in [airtable.md](airtable.md#bundled-cli-script-get-airtable-base).

**For Softr Database, find field IDs via:**

1. **Softr MCP server (recommended for AI-assisted workflows)** -- if you're collaborating with an AI assistant (Claude Code, Claude Desktop, Cursor, ChatGPT, Mistral) to write Vibe Coding blocks, the official Softr MCP server is the cleanest path. The AI calls schema/list-fields tools directly against your workspace and reads back every field's `id`, `name`, `type`, and dropdown option UUIDs -- no copy-paste, no transcription errors. The same server also browses connected Airtable / Google Sheets / Notion / Supabase integrations down to field level. Full setup and permissions in [../references/softr-mcp.md](../references/softr-mcp.md).

2. **`get-softr-database` CLI script (bundled, no MCP needed)** -- a Python CLI bundled with this skill at `~/.claude/skills/softr-vibe-coding/tools/get-softr-database.py`. Exports the full schema (every table, every field, all dropdown option UUIDs) to `~/Desktop/softr-database-<id>-<timestamp>.json`. Run with `python3 ~/.claude/skills/softr-vibe-coding/tools/get-softr-database.py <database_id>` (prompts for API key) or set `SOFTR_API_KEY=xxx` env var to skip the prompt. Stdlib only, no `pip install`. Best when you want a portable JSON dump for sharing in chat, archiving, or diffing across schema versions. Full usage in [softr-database.md](softr-database.md#bundled-cli-script-get-softr-database).

3. **Network inspector (full schema in one shot, no MCP needed)** -- in Studio's Data tab with browser DevTools open, filter Network requests by `tablespace-with-tables`. The Response JSON contains every table's complete schema, including:
   - Each field's `id`, `name`, `type`, and `options`
   - For dropdown / SELECT fields: the full `choices` array with every option's `id` (UUID), `label`, and `color`

   Use this when scaffolding a block that needs many field IDs at once, or to see a SELECT field's full choice list. (Write payloads take the option **label**, not the UUID — verified 2026-08-25, see [writing.md](writing.md#dropdown--single-select-softr-database) — but the exported labels are exactly what you need for a correct write vocabulary.) **When working with an AI assistant without the MCP installed**, paste this JSON response into the chat -- second-best way to share accurate field IDs and choice lists in one shot.

4. **Inline in Studio (one field at a time)** -- in the Data tab, click a field's name to open its edit drawer. The field ID appears next to the "Field name" label (e.g. `ID: 37fts`). Fastest for spot-checking a single field.

5. **Softr Database REST API with `fieldNames=true`** -- runtime inspection from inside a Vibe Coding block (only on a page limited to admins, and removed afterwards: the PAT sits in the block's source, and anyone who can load the page can read it and use it against the whole database, past every page, block and Source-condition gate):

```jsx
import { useEffect, useState } from "react";
export default function Block() {
  var [data, setData] = useState(null);
  useEffect(function() {
    var url = "https://tables-api.softr.io/api/v1/databases/<DB_ID>/tables/<TABLE_ID>/records?limit=3&fieldNames=true";
    fetch(url, { headers: { "Softr-Api-Key": "<PAT>" } })
      .then(function(res) { return res.json(); })
      .then(function(json) { setData(json); });
  }, []);
  if (!data) return <div className="container py-6"><div className="content"><p>Loading...</p></div></div>;
  return (
    <div className="container py-6">
      <div className="content">
        <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  );
}
```

This calls the Softr Database REST API with `?fieldNames=true`, which returns records keyed by human-readable field names so you can map them back to IDs. See [writing.md Cross-Table Operations](writing.md#cross-table-operations) for more on this REST API.

### API Response Inspector Block

For REST API data sources, use `useProxyFetch` instead (see [rest-api.md](rest-api.md)):

```jsx
import { useProxyFetch } from "@/lib/datasource";
import { useQuery } from "@tanstack/react-query";
export default function Block() {
  var proxyFetch = useProxyFetch();
  var result = useQuery({
    queryKey: ["api-inspect"],
    queryFn: function() {
      return proxyFetch("YOUR_FULL_API_URL_HERE")
        .then(function(res) { return res.json(); });
    },
  });
  if (result.status === "pending") return <div className="container py-6"><div className="content"><p>Loading...</p></div></div>;
  if (result.status === "error") return <div className="container py-6"><div className="content"><p className="text-red-500">Error: {result.error && result.error.message}</p></div></div>;
  return (
    <div className="container py-6">
      <div className="content">
        <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", wordBreak: "break-all", background: "#f9fafb", padding: 16, borderRadius: 8 }}>
          {JSON.stringify(result.data, null, 2)}
        </pre>
      </div>
    </div>
  );
}
```

### User Inspector Block

Use when debugging permissions, user groups, or the `useCurrentUser()` vs `window.__softr_current_user` distinction. Renders both side-by-side as JSON. This catches a common surprise: `userGroups` only lives on the `window.__softr_current_user` object, not on `useCurrentUser()`. (Custom user-record fields, by contrast, ARE available through the hook — `useCurrentUser({ properties: { alias: "FIELD_ID" } })` exposes them under `user.properties`; see [reading.md](reading.md#current-user).)

```jsx
import { useCurrentUser } from "@/lib/user";
export default function Block() {
  var currentUser = useCurrentUser();
  var softrUser = window.__softr_current_user || {};
  return (
    <div className="container py-6">
      <div className="content">
        <h3>useCurrentUser():</h3>
        <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
          {JSON.stringify(currentUser, null, 2)}
        </pre>
        <h3 style={{ marginTop: 16 }}>window.__softr_current_user:</h3>
        <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
          {JSON.stringify(softrUser, null, 2)}
        </pre>
      </div>
    </div>
  );
}
```

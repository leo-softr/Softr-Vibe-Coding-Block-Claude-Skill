# Airtable

## Overview
Popular spreadsheet-database hybrid used as a data source for Softr. Requires a Basic plan or higher in Softr.

## Connection Setup
1. In Softr admin, go to Data Sources and select Airtable.
2. Authenticate via OAuth or paste a Personal Access Token (PAT).
3. Select the base and table to connect.
4. Optionally connect to a specific View to inherit that view's filters and sort order.

**Always recommend PAT over OAuth.** OAuth connections are limited to 5 requests/second. PAT connections allow up to 50 requests/second.

## Vibe Coding Field IDs
q.select() uses **human-readable Airtable column names**, NOT internal `fld...` IDs.

```jsx
// CORRECT - use the column name exactly as it appears in Airtable
q.select({ name: "First Name" })
q.select({ name: "Email Address" })

// WRONG - internal field IDs do not work
q.select({ name: "fldqSabBeD6RkpTtp" })
```

Column names are case-sensitive and must match the Airtable header exactly.

## Supported Fields

| Field Type           | Writable  | Notes |
|----------------------|-----------|-------|
| Text                 | Yes       | |
| Long Text            | Yes       | |
| Number               | Yes       | |
| Date                 | Yes       | |
| Checkbox             | Yes       | |
| Single Select        | Yes       | Returns as `{ label, id }` object. Use `getFieldValue()` helper to extract the label. |
| Multiple Select      | Yes       | Array of `{ label, id }` objects |
| Attachment           | Yes       | Array of `{ filename, id, type, url }` objects |
| URL                  | Yes       | |
| Email                | Yes       | |
| Phone                | Yes       | |
| Linked Record        | Read/Write | Returns as `{ label, id }` objects |
| Rollup               | Read-only | |
| Formula              | Read-only | |
| Lookup               | Read-only | |
| Computed             | Read-only | |
| Created Time         | Read-only | |
| Modified Time        | Read-only | |
| Created By           | Read-only | |
| Last Modified By     | Read-only | |

## Rate Limits
- **Airtable Free plan:** 1,000 API calls/month
- **Airtable Team plan:** 100,000 API calls/month
- **Airtable Business plan:** Unlimited API calls
- **OAuth connections:** 5 requests/second
- **PAT connections:** 50 requests/second

Mitigation: Use PAT authentication. Cache data where possible. Avoid unnecessary re-fetches.

## Gotchas
- **Single Select returns an object**, not a string. `record.fields["Status"]` gives `{ label: "Active", id: "sel..." }`, not `"Active"`. Use `getFieldValue()` or access `.label` directly.
- **Attachments are arrays**, even for a single file. Always index into the array: `record.fields["Photo"][0].url`.
- **Linked records are objects** with `{ label, id }` structure, not plain text.
- **View connections** apply Airtable-side filters and sorts before data reaches Softr. This is useful for pre-filtering but means the Softr block only sees the view's subset.
- **Column names are case-sensitive.** `"First name"` and `"First Name"` are different.

## Best For
- Teams already managing data in Airtable
- Apps with moderate traffic (under 200-300 concurrent users)
- Projects needing a flexible schema with rich field types

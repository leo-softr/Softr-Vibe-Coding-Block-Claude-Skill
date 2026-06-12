# Airtable

> **Looking for Airtable Automation Scripts, Scripting Extension, or Airtable formulas?** This page covers the **Softr data source** integration (read/write from a Vibe Coding block). For Airtable-side scripts and formula fields — including cross-table cascades triggered by record changes — see [../references/airtable-automations.md](../references/airtable-automations.md).

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

**Verified by direct experiment, May 2026:** aliases mapped to `fld...` IDs are silently omitted from the record's `fields` object -- only column-name aliases populate. Airtable's native API supports both formats; Softr's wrapper restricts to names.

### Maintainability gotcha

Renaming a column in Airtable breaks the block **silently**. The failure mode depends on whether the alias is used for reads or writes:

- **Read side** (`useRecords` / `useRecord` / `useLinkedRecords`): the alias stops resolving — no error, the field becomes `undefined`. Other fields in the same `q.select()` still load fine. Partial behaviour.
- **Write side** (`useRecordCreate` / `useRecordUpdate` `q.select`): the parser silently rejects the **entire** Action. Studio's Actions tab shows "No actions used in this block yet", `createRecord.enabled` / `updateRecord.enabled` stays `false`, and `.mutate()` calls fail with "not yet ready" / "create action is not yet ready". Every field in that `q.select()` is lost, even the valid ones. All-or-nothing.

The asymmetry matters because reads silently degrade while writes silently disable. A renamed column on a list view shows blank cells; the same rename on a create helper bricks the whole submit flow with no console error.

**Diagnosing a disabled write Action** (the "No actions used" symptom): bisect the `q.select()`. Strip it down to a known-good minimal set (4–6 fields that you're sure exist), confirm the Action shows up in Studio's Actions tab, then add fields back in halves until the Action drops out. The culprit is in the last half added. Once narrowed to a single field, grep that field name against the freshest schema export — almost always a rename, a trailing space, or a case mismatch.

**Three mitigations, in order of effort:**

1. **Document the field ID alongside the name** in `q.select()` comments. A grep for the field ID then finds every block affected by a rename:

   ```jsx
   var select = q.select({
     firstName: "First Name",  // fld6vaQi4ZHxxwP0y
     lastName: "Last Name",    // fldIQDfFXwBvtSCQp
   });
   ```

2. **Centralize `q.select()` mappings** in a single helper block (see [references/helper-blocks.md](../references/helper-blocks.md)). One rename then touches one file rather than every block that reads the table.

3. **Avoid renaming columns mid-project** -- use Airtable's Description field for clarification instead.

## Bundled CLI script: `get-airtable-base`

A Bash CLI bundled with this skill that exports an Airtable base's full metadata to a timestamped folder on your Desktop. Pulls schema, relationships, sync detection, webhooks, interfaces, and shares — everything the Airtable Web API exposes for a single base.

**Script location after `npx softr-vibe-coding@latest init`:**

```
~/.claude/skills/softr-vibe-coding/tools/get-airtable-base
```

**Requirements:** `jq` (`brew install jq` on macOS), `curl` (preinstalled on macOS/Linux), Bash.

**Run it:**

```bash
bash ~/.claude/skills/softr-vibe-coding/tools/get-airtable-base
```

The script prompts interactively for:

- **Base ID** (e.g. `appXXXXXXXXXXXXXX` — find it in the Airtable URL or the API docs page for the base).
- **Personal Access Token** (input hidden — needs `schema.bases:read` scope minimum, plus `webhook:manage` for webhooks, and optionally `enterpriseAccount:read` for shares).

**Output folder:** `~/Desktop/airtable-base-<BASE_ID>-<UTC-timestamp>/` containing:

| File | Contents |
|---|---|
| `00-bundle.json` | Combined bundle of all the below for easy sharing in one paste |
| `01-base-info.json` | Collaborators, interfaces, invite links |
| `02-schema.json` | Full schema: every table, every field (with both `fld...` IDs and column names), every view, `visibleFieldIds` per view |
| `03-shares.json` | Enterprise-only shares — skipped on non-Enterprise plans |
| `04-webhooks.json` | Registered webhooks |
| `05-whoami.json` | Token identity and scopes — confirms which user/PAT was used and what it can access |
| `06-relationships.json` | Derived from `02-schema.json`: sync destinations, cross-table links, lookup/rollup/count/formula field maps |

After completion, the script opens the folder in Finder (macOS).

**Optional alias** for a shorter command. Add to your `~/.zshrc` or `~/.bashrc`:

```bash
alias get-airtable-base='bash ~/.claude/skills/softr-vibe-coding/tools/get-airtable-base'
```

After `source ~/.zshrc`, run `get-airtable-base` from anywhere.

**Getting a PAT:** https://airtable.com/create/tokens → Create token → grant `schema.bases:read` (add `data.records:read` only if you want to also read records via the Web API outside Softr). Scope to the specific base(s) the script should access.

**When to use this:**

- **Documenting field IDs alongside column names** in `q.select()` — the mitigation in [Maintainability gotcha](#maintainability-gotcha) above. Grep the `02-schema.json` for an `fld...` ID to find every block affected by a column rename.
- **Bisecting a broken Action** when a column rename has silently disabled it — the freshest `02-schema.json` is the source of truth to grep against.
- **Auditing relationships** (lookups, rollups, formulas, cross-table links, sync sources) — `06-relationships.json` summarizes everything the schema reveals about derived/referenced fields.
- **Sharing schema with an AI assistant** — paste `00-bundle.json` (or just `02-schema.json` if smaller) into chat to give the assistant accurate, current schema context.

This script reads only **metadata**, never records. To inspect record contents inside a Vibe Coding block, use the Field Inspector pattern in [fields.md](fields.md#field-inspector-block).

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
| Formula              | Read-only | Reads fine for most formulas — BUT a formula that references an **autoNumber** field often comes back blank through Softr's data layer. See Gotchas → "Formulas depending on autoNumber". |
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
- **Formulas that depend on an `autoNumber` field can read back blank** (verified 2026-06-12). Softr serves most formulas fine — a `CONCATENATE` of text fields reads correctly — but a formula like `"WIG-" & RIGHT("0000" & {Autonumber}, 4)` frequently comes through as `""`, even though Airtable shows the value and a data re-sync doesn't fix it. The autoNumber dependency is the differentiator: a sibling formula on the same record (no autoNumber) reads fine.
  - **Symptom:** one computed field is empty in `record.fields` while the rest populate; re-syncing the Softr data source doesn't help.
  - **Fix:** don't read the formula — read the raw `autoNumber` field and rebuild the value in JS:
    ```jsx
    // q.select({ tag: "Wig Tag ID", auto: "Autonumber", ... })
    function buildTag(f) {
      var raw = getFieldValue(f.tag);
      if (raw) return raw;                       // formula populated — use it
      var n = f.auto;
      if (n != null && typeof n === "object") n = (n.value != null) ? n.value : "";
      var s = (n == null) ? "" : String(n).trim();
      return s ? "WIG-" + ("0000" + s).slice(-4) : "";  // mirror the Airtable formula in JS
    }
    ```
  - **Alternative (most robust):** add a plain single-line-text field and stamp the value into it with an Airtable automation on record create. Softr reads plain text 100% reliably, with no formula/autoNumber dependency.

## Best For
- Teams already managing data in Airtable
- Apps with moderate traffic (under 200-300 concurrent users)
- Projects needing a flexible schema with rich field types

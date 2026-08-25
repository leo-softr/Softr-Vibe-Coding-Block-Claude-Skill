# Writing Data

Record mutations, sequential write queues, file uploads, linked record format, and cross-table operations.

## Table of Contents

- [How Actions Work (Studio's Actions Tab)](#how-actions-work-studios-actions-tab)
- [Record Mutations](#record-mutations)
- [Sequential Multi-Row Writes (mutateAsync)](#sequential-multi-row-writes-mutateasync)
- [File Uploads](#file-uploads)
- [Linked Record Format for Mutations](#linked-record-format-for-mutations)
- [Writing to Field Types](#writing-to-field-types)
- [Cross-Table Operations](#cross-table-operations)

## How Actions Work (Studio's Actions Tab)

Every Vibe Coding block in Softr Studio has an **Actions tab** alongside Chat / Source / Content / Visibility. The Actions tab is a **read-only inspector** of the Create / Update / Delete operations the platform inferred from your code.

Each Action's "FIELDS USED" list mirrors the aliases in your `q.select()` mapping. Actions are not a separately-managed system:

- The platform parses your block's source on every save
- For each `useRecordCreate` / `useRecordUpdate` / `useRecordDelete` hook, it auto-derives a corresponding Action
- The fields list comes from your `q.select` aliases used in the mutation payload
- Cosmetic AND structural code edits both update the Action automatically -- you do NOT need to re-prompt the AI assistant after editing code
- There is no manual delete control; to remove an Action, remove the mutation hook from the code

**⚠️ Every recompile resets Action permissions (verified live 2026-08-25).** Each code
recompile/redeploy re-registers the block's auto-derived Actions with **default permissions** —
any per-Action permission tightening done in the Actions tab is wiped. Deployment-order
implication: do the Actions-tab tightening pass only AFTER the last redeploy of a block, and
re-check every tightened block after any future redeploy. Hit across a 15-block production
deployment; treat it as standing platform behavior, not a one-off.

The `enabled` boolean on a mutation hook is a combined signal — it's `true` only when BOTH conditions are met:

1. **The Action was successfully derived from the code** (parser side). Causes of failure here:
   - The hook is declared after a conditional `return`, so it doesn't run on every render
   - `q.select` is built dynamically rather than from string-literal mappings
   - The block hasn't been connected to a data source yet
   - `useRecordUpdate.mutate()` is called with a flat payload (`{ recordId, status: ... }`) instead of the nested shape (`{ recordId, fields: { status: ... } }`) -- the parser ignores flat field references, so no Action gets created

2. **The currently logged-in (or previewed-as) user has permission to perform the action on the data source** (permissions side). Per the official Softr docs, "`enabled` reflects user permissions." So even with a perfectly-derived Action, `enabled` will be `false` if the previewed user's group lacks write access to the connected table.

**Critical debugging implication:** when `enabled` stays `false` and Studio's Actions tab DOES show the action listed (parser succeeded), the cause is permissions — not code. Three places to check, in order:

- **Block's Visibility tab** (right panel) — confirm the previewed user's group is allowed to see / interact with this block.
- **Studio → Users → Data Restrictions → Global data restrictions** — an app-wide layer that limits what data users can interact with across the whole app, applied on top of block-level settings. Easy to miss because it's under Users (not on the block). If a Global restriction exists on the target table for the user's group, every mutation against that table in every block silently fails — no error, just `enabled: false`. Open this tab and either confirm there are no restrictions or that the worker / target group has the access they need.
- **Data-source connection PAT scope** — if the PAT was granted with read-only scope, every write fails regardless of UI permissions. Reconnect with write scope if needed.

Verified by direct experiment (April 2026): adding a new field to `q.select` + `mutate()` payload and saving the code propagates to the Actions tab automatically and writes successfully to the database with no manual configuration.

Because the parser only inspects your hooks and `q.select` mappings (not the JSX tree), inputs rendered conditionally inside `<Dialog>`, `<Sheet>`, or any subtree gated by state are still bound to the Action correctly. Verified by direct experiment, May 2026.

## Record Mutations

All mutation hooks expose an `enabled` boolean. You must check it before rendering any mutation UI or calling the mutate function.

### useRecordCreate

```jsx
import { useRecordCreate, q } from "@/lib/datasource";
import { toast } from "sonner";

var createRecord = useRecordCreate({
  fields: q.select({ name: "FIELD_ID1", email: "FIELD_ID2" }),
  onSuccess: function(newRecord) { toast.success("Created!"); },
  onError: function(error) { toast.error(error.message); },
});

// Usage (gate on enabled):
if (createRecord.enabled) {
  createRecord.mutate({ name: "Jane", email: "jane@example.com" });
}
```

**Create payloads are FLAT — no `{ fields }` wrapper** (verified live 2026-08-25). The payload's
keys are the aliases from the hook's `fields:` q.select, at the top level. This is deliberately
asymmetric with `useRecordUpdate`, whose payload nests them: `{ recordId, fields: { ... } }`.
Wrapping a create payload in `fields:` is a wrong shape — don't copy it from an update call.

### useRecordUpdate

```jsx
import { useRecordUpdate, q } from "@/lib/datasource";

var updateRecord = useRecordUpdate({
  fields: q.select({ status: "FIELD_ID1" }),
  onSuccess: function(updatedRecord) {
    refetch().then(function() { toast.success("Updated!"); });
  },
  onError: function(error) { toast.error(error.message); },
});

// Usage -- MUST use recordId, NOT id, AND fields MUST be nested:
updateRecord.mutate({
  recordId: "RECORD_ID",
  fields: { status: "active" },
});
```

#### CRITICAL: The `useRecordUpdate` payload shape (and the retired `.mutate()`-only rule)

**Payload must be `{ recordId, fields: {...} }` — not flat.** Field values must be nested inside a `fields: {...}` object. The flat form (`mutate({ recordId, status: "active" })`) can succeed at runtime, but Softr's Action parser doesn't see field references inside it, so no Update Action is derived — `enabled` stays `false`, the UI gated on it silently does nothing, and Studio's Actions tab shows "No actions used in this block yet":

```jsx
// CORRECT
updateRecord.mutate({ recordId: id, fields: { status: "Active" } }, { onSuccess, onError });

// WRONG — Action parser ignores this, hook stays disabled
updateRecord.mutate({ recordId: id, status: "Active" }, { onSuccess, onError });
```

Note the asymmetry: **update payloads nest under `fields:`, create payloads are flat** (no wrapper). Verified live 2026-08-25.

**`.mutateAsync()` is fully supported (verified live 2026-08-25 — supersedes the old rule).**
Until mid-2026 this skill documented that the Action parser only recognized the literal
`.mutate(` token, and that any mutation written as `.mutateAsync(...)` produced no derived
Action (verified by direct experiment, May 2026, on the then-current platform). The current
platform derives Actions for `mutateAsync` call sites too — a 15-block production deployment
built its entire multi-row write layer on `await hook.mutateAsync(...)` with Actions deriving
correctly on every block. Use `.mutate(payload, { onSuccess, onError })` for fire-and-forget
single writes; use `await .mutateAsync(payload)` when the code must sequence writes or branch
on the result (see [Sequential Multi-Row Writes](#sequential-multi-row-writes-mutateasync)).
If you're maintaining an old app where an Action refuses to derive, the legacy `.mutate(`-only
parser is worth checking before deeper debugging.

### useRecordDelete

```jsx
import { useRecordDelete } from "@/lib/datasource";

var deleteRecord = useRecordDelete({
  onSuccess: function(result) {
    refetch().then(function() { toast.success("Deleted!"); });
  },
  onError: function(error) { toast.error(error.message); },
});

// Usage -- pass just the string, NOT an object:
deleteRecord.mutate("RECORD_ID");
```

### Three q.select() Mappings Pattern

For blocks that read, create, and update, use separate mappings:

```jsx
// 1. READ -- includes everything (formulas, lookups, linked records)
var select = q.select({
  name: "FIELD_1", email: "FIELD_2",
  score: "FORMULA_FIELD",       // read-only OK here
  department: "LOOKUP_FIELD",   // read-only OK here
});

// 2. CREATE -- only writable fields
var createFields = q.select({ name: "FIELD_1", email: "FIELD_2" });

// 3. UPDATE -- only writable fields that can be edited
var updateFields = q.select({ name: "FIELD_1", email: "FIELD_2" });
```

## Sequential Multi-Row Writes (mutateAsync)

`await hook.mutateAsync(...)` is the tool for any save that writes several rows in a required
order — a header record followed by its line items, a source record followed by ledger rows, a
batch of rows that must stop cleanly on the first failure. Verified live 2026-08-25: this
pattern carried every multi-row save in a 15-block production deployment.

The battle-tested queue shape:

```tsx
// Track queue state in component state so a failure is renderable and resumable.
// { phase: "idle" | "saving" | "failed" | "done", failedIndex: number | null }

async function saveAll() {
  setQueue({ phase: "saving", failedIndex: null });

  // 1. Header first — its id links every line.
  const header = await createHeader.mutateAsync({ name, date });   // create payloads are FLAT
  if (!header?.id) throw new Error("Header created without an id");

  // 2. Lines in order. STOP on the first failure; never re-issue completed writes.
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].saved) continue;                 // resume support: skip completed rows
    try {
      await createLine.mutateAsync({ header: [header.id], product: lines[i].product, qty: lines[i].qty });
      markSaved(i);
    } catch (err) {
      setQueue({ phase: "failed", failedIndex: i });   // render the failed line + a Retry button
      return;
    }
  }
  await refetch();                                // refresh affected queries BEFORE toasting
  setQueue({ phase: "done", failedIndex: null });
  toast.success("Saved");
}
```

Rules that make this safe:

- **Header first, then lines in order.** Await each write; never fire the loop in parallel and
  never chain with nested `.then()` callbacks.
- **Stop on failure, keep the queue.** Render the failed row with its error and a Retry button;
  Retry re-runs only the failed write and resumes the remainder. Completed writes are never
  re-issued.
- **Guard against ambiguous failures.** A failed *response* doesn't prove a failed *write* (the
  server may have committed and the response been lost). Before a Retry re-writes, re-fetch the
  already-written child rows for that header and skip any the server already has — this is what
  makes the queue double-write-proof.
- **Guard the created id.** If a create resolves without an id, throw — don't write lines linked
  to `undefined`.
- **Gate the whole flow on the hooks' `enabled` booleans**, same as any mutation UI.

## File Uploads

```jsx
import { useUpload } from "@/lib/datasource";

var upload = useUpload();

// Single file:
upload.uploadAsync(file).then(function(results) {
  var result = results[0];
  if (result.status === "completed") {
    // result.url = uploaded file URL, result.file.name = original filename
  }
});

// Combine with record creation:
upload.uploadAsync(file).then(function(results) {
  var result = results[0];
  if (result.status === "completed") {
    createRecord.mutate({
      name: "Document",
      attachment: { filename: result.file.name, url: result.url },
    });
  }
});
```

### Async/await style

The official Softr Vibe Coding docs use this form; it's more ergonomic when uploading inside a larger async flow:

```jsx
var [result] = await upload.uploadAsync(file);
if (result.status === "completed") {
  createRecord.mutate(
    { attachment: { filename: result.file.name, url: result.url } },   // create payload is FLAT
    { onSuccess: function() { toast.success("Saved"); } }
  );
}
```

Inside a larger async flow, `await createRecord.mutateAsync({ attachment: ... })` works just as
well — `mutateAsync` is fully supported on the current platform (verified 2026-08-25; see the
supersession note under `useRecordUpdate` above).

## Linked Record Format for Mutations

Write linked-record fields as an **array of record-id strings** (verified live 2026-08-25 on
Softr Database — every cross-table link in a 15-block production deployment used this shape):

```jsx
// CORRECT -- array of record-id strings, even for a single link
createRecord.mutate({
  parentAccount: ["RECORD_ID_1"],
  teamMembers: ["MEMBER_1", "MEMBER_2"],
});

// WRONG -- bare string, not wrapped in an array
parentAccount: "RECORD_ID_1"
```

**Legacy / Airtable note.** This skill previously documented arrays of `{ id }` objects
(`teamMembers: [{ id: "MEMBER_1" }]`), verified May 2026 on Airtable-backed blocks. The
string-array shape is the verified current form on Softr Database; if a linked-record write
fails on an Airtable-backed block, try the `[{ id }]` object shape before deeper debugging.

## Writing to Field Types

Different Softr field types accept different value shapes in mutation payloads. The shape returned when you READ a field is often different from the shape you must SEND when you WRITE.

### Dropdown / Single Select (Softr Database)

Write the option's **LABEL string** — it must exactly match a defined choice on the field. No
option-UUID discovery step is needed:

```jsx
// CORRECT -- the option's display label, exactly as defined
createRecord.mutate({
  status: "Active",
});

// WRONG -- object form (returned on read, but rejected on write)
createRecord.mutate({
  status: { id: "822b8d69-3af4-47b4-90eb-3a80c5d1b85c", label: "Active" },
});
```

Verified live 2026-08-25 (Softr Database, `useRecordCreate` AND `useRecordUpdate`): every
controlled-vocabulary SELECT write in a 15-block production deployment wrote label strings
(`"Tier 1"`, `"Prospect"`, `"Physical count correction"`, ...) with no UUID discovery step.

The label must match a defined choice character-for-character — a typo fails the write, so
keep vocabularies as greppable constants, or fetch them live with `useFieldOptions` (see
[reading.md](reading.md#usefieldoptions----fetch-singlemulti-select-choices)) and write
`option.label`.

**Legacy note.** Until mid-2026 this skill documented the opposite — write the option UUID,
labels rejected (verified April 2026 on the then-current platform). If a label write is
rejected on an old app, the UUID form is the thing to try; on the current platform it is not
needed.

### Linked Record

Array of `{ id }` objects. See "Linked Record Format for Mutations" above.

### Multi-Select

Expected: array of option **label strings** — mirrors Single Select (which writes by label,
verified 2026-08-25) but wrapped in an array:

```jsx
// EXPECTED
createRecord.mutate({ tags: ["Urgent", "Internal"] });

// WRONG -- {id, label} objects (returned on read, rejected on write)
tags: [{ id: "uuid-1", label: "Urgent" }]
```

_Not independently verified — inferred from the verified single-select label behavior; verify by
experiment before production use. (The pre-2026-08 platform took option-UUID arrays instead.)_

### Number

Plain JS number, not string:

```jsx
createRecord.mutate({ price: 49.99, quantity: 3 });
```

To clear, `null` works on Softr Database (`""` is invalid for numeric fields). Other data sources not independently verified.

### Checkbox

Boolean `true` / `false`:

```jsx
createRecord.mutate({ isActive: true });
```

**Softr Database** also accepts the string forms `"true"` / `"false"` (mirrors the `string or boolean` read shape — see [fields.md](fields.md)). **Google Sheets** requires the string form, not native booleans — see [google-sheets.md](google-sheets.md). Other data sources expected to accept the boolean form but not independently verified.

### Date

ISO string. Date-only fields take `YYYY-MM-DD`; date-time fields take the full ISO form:

```jsx
// Date-only field
createRecord.mutate({ dueDate: "2025-03-15" });

// Date-time field — use new Date().toISOString() for current timestamp
createRecord.mutate({ lastSeenAt: "2025-03-15T14:00:00Z" });
```

Verified live 2026-08-25 (Softr Database): DATETIME fields with **date semantics** (a due date,
a distribution date) take the `"yyyy-MM-dd"` form; **timestamp** fields (`*_at` audit fields)
take `new Date().toISOString()`. Writing a full timestamp into a date-semantics field invites
timezone-shift bugs — compare and display such fields on the `yyyy-MM-dd` slice.

### Date Range

Object with `from` and `to` ISO strings — mirrors the read shape (`{ from, to }` per [fields.md](fields.md)):

```jsx
createRecord.mutate({
  bookingWindow: { from: "2025-03-15", to: "2025-03-20" },
});
```

_Inferred from the read shape (see [fields.md](fields.md)); verify by experiment before production use._

### Attachment

`{ filename, url }` for a single attachment, or an array of those objects for multi-attachment fields:

```jsx
// Single attachment
createRecord.mutate({
  document: { filename: "report.pdf", url: "https://..." },
});

// Multiple attachments
createRecord.mutate({
  gallery: [
    { filename: "photo1.jpg", url: "https://..." },
    { filename: "photo2.jpg", url: "https://..." },
  ],
});
```

To upload a file before writing it to a record, see [File Uploads](#file-uploads) above for the full `useUpload` flow.

_Shape matches the example shown in [File Uploads](#file-uploads). Not yet independently verified across all data sources._

### Text / Email / URL / Phone

Plain string. To clear a value, both `null` and `""` work for Softr Database text fields (verified by direct experiment, May 2026, for `useRecordUpdate`). Behavior on other data sources has not been independently verified.

## Cross-Table Operations

**The default path is multi-datasource (supersedes the REST-API-first guidance that used to live
here).** A block can connect to several data sources at once — declare them with
`datasource.define({ alias: "uuid", ... })` and pass `from: ds.alias` on every hook, including
the mutation hooks. Reading two tables and writing a third from one block needs no helper
block, no REST API, and no exposed key. Required reading:
[multi-datasource.md](multi-datasource.md). Verified at scale 2026-08-25: a 15-block production
deployment routed all of its cross-table writes (header + ledger + audit-log rows) through
`from:`-scoped mutation hooks.

Two remaining alternatives, for the cases multi-datasource doesn't cover:

- **For Airtable backends** — when the cascade logic is heavy, write to the block's own table and let an Airtable automation script handle the cascade. See [../references/airtable-automations.md](../references/airtable-automations.md). Keeps the block simple and lets cross-table logic live next to the data.
- **Softr Database REST API via `fetch()`** — a fallback for what the hooks can't express (e.g. writes from outside a Vibe block, or admin tooling that must bypass block bindings). Details below.

**Base URL:** `https://tables-api.softr.io/api/v1/databases/{databaseId}/tables/{tableId}/records`

**Authentication:** `Softr-Api-Key` header with a Personal Access Token.

**Create:** POST with `{ fields: { fieldId1: "value1" } }`
**Read:** GET with `?limit=200&fieldNames=true`
**Update:** PATCH `/{recordId}` with `{ fields: { fieldId1: "newValue" } }`

Notes:
- API key is exposed in client-side code -- acceptable for internal portals only
- When updating linked records or multi-selects, read existing values first, merge, then write
- Use `fieldNames=true` on GET for human-readable field names
- Rate limits: Reads 40 req/s, Writes 30 req/s

Verified by direct experiment (May 2026): POST to this endpoint with field IDs as keys writes successfully, returning HTTP 200 and the full record JSON. At that time the endpoint took plain string UUIDs for dropdown writes, and the response returned the dropdown value as a `{id, label}` object (matching the read shape). Note: that observation predates the 2026-08-25 finding that the **in-block hooks** write SELECTs by label — the REST endpoint is a separate surface and may still expect UUIDs; re-verify whichever shape you use here.

# Writing Data

Record mutations, file uploads, linked record format, and cross-table operations.

## Table of Contents

- [How Actions Work (Studio's Actions Tab)](#how-actions-work-studios-actions-tab)
- [Record Mutations](#record-mutations)
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

#### CRITICAL: Two parser requirements for `useRecordUpdate`

Softr's Action parser is strict about both the **method name** and the **payload shape**. Get either wrong and the Action is never derived, `enabled` stays `false`, and any UI gated on it silently does nothing — no error, no warning, console just shows `enabled: false, error: null, status: "idle"`.

**Requirement 1 — Call `.mutate()`, NOT `.mutateAsync()`.** The parser scans for the literal `.mutate(` token to detect mutation call sites. `.mutateAsync()` runs fine at runtime (it's just a Promise wrapper), but the parser ignores it and no Update Action gets created. Pass per-call success/error handlers as the second argument (react-query convention):

```jsx
// CORRECT — parser sees `.mutate(`, derives the Action
updateRecord.mutate(
  { recordId: id, fields: { status: optionId } },
  {
    onSuccess: function() { toast.success("Saved"); },
    onError: function(err) { toast.error(err.message); },
  }
);

// WRONG — parser ignores `.mutateAsync(`, Action never created
updateRecord.mutateAsync({ recordId: id, fields: { status: optionId } })
  .then(function() { toast.success("Saved"); });
```

**Requirement 2 — Payload must be `{ recordId, fields: {...} }` — not flat.** Field values must be nested inside a `fields: {...}` object. The flat form (`mutate({ recordId, status: "active" })`) can succeed at runtime, but the parser doesn't see field references inside it, so no Action is derived:

```jsx
// CORRECT
updateRecord.mutate({ recordId: id, fields: { status: optionId } }, { onSuccess, onError });

// WRONG — Action parser ignores this, hook stays disabled
updateRecord.mutate({ recordId: id, status: optionId }, { onSuccess, onError });
```

Verified by direct experiment (May 2026): Softr's Studio AI assistant emits both `.mutate()` AND the nested payload shape — and that combination is what produces a derived Update Action. Switching either back to its alternative form (`.mutateAsync()` or flat payload) disables the hook.

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
    { fields: { attachment: { filename: result.file.name, url: result.url } } },
    { onSuccess: function() { toast.success("Saved"); } }
  );
}
```

**Stick with `.mutate(...)` even inside async functions** — don't switch to `.mutateAsync(...)` just for the await ergonomics. Softr's Action parser only recognizes the `.mutate(` token, so any mutation written as `.mutateAsync(` produces no derived Action and `enabled` stays `false` (see "Two parser requirements for `useRecordUpdate`" below).

## Linked Record Format for Mutations

```jsx
// CORRECT -- Array of { id } objects
createRecord.mutate({
  parentAccount: [{ id: "RECORD_ID_1" }],
  teamMembers: [{ id: "MEMBER_1" }, { id: "MEMBER_2" }],
});

// WRONG -- Plain string or array of strings
parentAccount: "RECORD_ID_1"           // Won't work
teamMembers: ["MEMBER_1"]              // Won't work
```

## Writing to Field Types

Different Softr field types accept different value shapes in mutation payloads. The shape returned when you READ a field is often different from the shape you must SEND when you WRITE.

### Dropdown / Single Select (Softr Database)

Write the option's UUID as a **plain string**, not an object:

```jsx
// CORRECT -- plain string UUID
createRecord.mutate({
  status: "822b8d69-3af4-47b4-90eb-3a80c5d1b85c",
});

// WRONG -- object form (returned on read, but rejected on write)
createRecord.mutate({
  status: { id: "822b8d69-3af4-47b4-90eb-3a80c5d1b85c", label: "Active" },
});

// WRONG -- display label
createRecord.mutate({
  status: "Active",
});
```

Option UUIDs are stable. Three ways to retrieve them:

- **AI scaffolding** -- Softr's AI assistant in Studio inlines them automatically into `<SelectItem value="...">` when generating a form
- **Network inspector** -- DevTools -> Network -> filter `tablespace-with-tables` returns the full `choices` array for any SELECT field (see [fields.md](fields.md#field-inspector-block) for the full technique). Pasting this JSON into an AI assistant chat is the most reliable way to share UUIDs without transcription errors.
- **Runtime scan** -- learn them at runtime from already-loaded records (useful when the block must work in environments where UUIDs are not known at code time)

Verified by direct experiment (April 2026) for `useRecordCreate`. The same pattern is expected to apply to `useRecordUpdate` but has not been independently verified.

### Linked Record

Array of `{ id }` objects. See "Linked Record Format for Mutations" above.

### Multi-Select

Array of option UUIDs as plain strings — mirrors Single Select but wrapped in an array:

```jsx
// CORRECT
createRecord.mutate({ tags: ["uuid-1", "uuid-2"] });

// WRONG -- {id, label} objects (returned on read, rejected on write)
tags: [{ id: "uuid-1", label: "Urgent" }]

// WRONG -- display labels
tags: ["Urgent", "Internal"]
```

_Inferred from the read shape (see [fields.md](fields.md)); verify by experiment before production use._

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

_Inferred from the read shape (see [fields.md](fields.md)); verify by experiment before production use._

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

`useRecordCreate`, `useRecordUpdate`, and `useRecordDelete` only work with the block's configured datasource. Two paths to write across tables:

- **For Airtable backends** — usually cleanest to write to the block's own table and let an Airtable automation script handle the cascade. See [../references/airtable-automations.md](../references/airtable-automations.md). Keeps the block simple, avoids exposing an API key in the browser, and lets cross-table logic live next to the data.
- **Softr Database REST API via `fetch()`** — the only option for non-Airtable sources, and the right choice when an automation cycle would be too slow. Details below.

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

Verified by direct experiment (May 2026): POST to this endpoint with field IDs as keys writes successfully, returning HTTP 200 and the full record JSON. The endpoint uses the same field-ID format and the same value shapes as `useRecordCreate` -- plain string UUID for dropdown writes; the response returns the dropdown value as a `{id, label}` object (matching the read shape).

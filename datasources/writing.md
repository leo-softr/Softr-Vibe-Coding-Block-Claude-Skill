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

**Critical debugging implication:** when `enabled` stays `false` and Studio's Actions tab DOES show the action listed (parser succeeded), the cause is permissions — not code. Common triggers: previewing the page as a non-admin user, or a data-source connection that was granted with read-only PAT scope. Fix at the Studio data-source permissions level, not in the block.

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

#### CRITICAL: Payload must be `{ recordId, fields: {...} }` — not flat

The mutate payload **must** wrap the field values inside a `fields: {...}` object. The flat form (`mutate({ recordId, status: "active" })`) can succeed at runtime for some sources, but Softr's **Action parser** only recognizes the nested shape. With a flat payload:

- The Actions tab shows "No actions used in this block yet"
- `updateRecord.enabled` stays `false` forever
- The Save button / status chip / whatever-you-gated-on-`enabled` never lights up
- No error, no warning — just a silently disabled mutation

Symptoms in the field: a worker clicks Save, nothing happens, console shows `enabled: false, error: null, status: "idle"`. Every mutate call in the block must use the nested form, even when only writing a single field:

```jsx
// CORRECT
updateRecord.mutate({ recordId: id, fields: { status: optionId } });

// WRONG — Action parser ignores this, hook stays disabled
updateRecord.mutate({ recordId: id, status: optionId });
```

Verified by direct experiment (May 2026): Softr's Studio AI assistant emits the nested form, and that's the only form that produces a derived Update Action.

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

### Text / Email / URL / Phone

Plain string. To clear a value, both `null` and `""` work for Softr Database text fields (verified by direct experiment, May 2026, for `useRecordUpdate`). Behavior on other data sources has not been independently verified.

## Cross-Table Operations

`useRecordCreate`, `useRecordUpdate`, and `useRecordDelete` only work with the block's configured datasource. To write to a different table, use the **Softr Database REST API** via `fetch()`:

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

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

The `enabled` boolean on a mutation hook reflects whether the Action was successfully derived. If `enabled` is false, the most likely causes are:

- The hook is declared after a conditional `return`, so it doesn't run on every render
- `q.select` is built dynamically rather than from string-literal mappings
- The block hasn't been connected to a data source yet

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

// Usage -- MUST use recordId, NOT id:
updateRecord.mutate({
  recordId: "RECORD_ID",
  fields: { status: "active" },
});
```

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

Option UUIDs are stable. Hardcode them in `<SelectItem value="...">` (Softr's AI assistant in Studio does this automatically when scaffolding a form) or learn them at runtime from already-loaded records.

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

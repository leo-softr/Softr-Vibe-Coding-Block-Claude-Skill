# Airtable Automation Scripts & Formulas

Companion reference for Softr Vibe Coding blocks. Many Softr blocks talk to an Airtable backend, and some flows can't be done from the block side — most commonly **cross-table writes triggered by a record change** (the block can only write to its own configured data source). For those, the right tool is an Airtable Automation Script, written in JavaScript and triggered by Airtable's automation runner.

This guide covers Airtable's two scripting environments + Airtable formulas. **It is NOT about Softr Vibe Coding** — runtime, API surface, and gotchas are entirely different. Don't apply Softr block rules (no `?.`, shadow DOM, etc.) here.

## When to reach for an Airtable script vs. a Softr block

| Want to … | Use |
|---|---|
| Build UI inside a Softr page | Softr Vibe Coding block |
| React to a record-level event in Airtable (e.g. status change) and cascade to other tables | **Airtable Automation Script** |
| Run ad-hoc transformations / bulk fixes | Airtable Scripting Extension |
| Compute a derived value displayed in an Airtable cell | Airtable formula field |

If a Softr block needs to write across multiple tables in response to a user click, the **cleanest pattern** is: have the Softr block write to its own table, and let an Airtable automation handle the cascade. See [datasources/writing.md → Cross-Table Operations](../datasources/writing.md#cross-table-operations) for the alternative (Softr Database REST API), but the Airtable-side automation is usually simpler.

## Two scripting environments — pick the right one

### 1. Automation Script (the "Run a script" action inside an automation)

Background-only. No UI. Receives input from the automation trigger; can output values for downstream automation steps.

- Read trigger inputs via `input.config()` — call it WITHOUT arguments. Input variables are configured in the automation's left panel, not in code.
- Output to downstream steps via `output.set(key, value)`.
- `console.log()` appears in the automation's run log (NOT the browser console).
- No `input.buttonsAsync`, no `output.markdown`, no `output.table` — those are Scripting-Extension-only and will throw.
- Execution cap: 120 seconds (recently raised from 30s).

```js
// Inputs are wired in the automation UI's left panel:
//   recordId = (record from trigger).id
let config = input.config();
let recordId = config.recordId;

async function main() {
  try {
    let table = base.getTable('Your Table');
    let record = await table.selectRecordAsync(recordId);
    // ... do work ...
    output.set('processed', true);
  } catch (error) {
    console.log('ERROR: ' + error.message);
    output.set('error', error.message);
    throw error;  // re-throw so Airtable marks the run as failed
  }
}

await main();
```

### 2. Scripting Extension (run-in-the-UI scripts)

Foreground, interactive. Used for one-off transforms, bulk fixes, building admin dashboards. Has a richer API.

- Configure interactive inputs via `input.config({ title, items: [...] })` — note: takes an OBJECT here, unlike Automation Scripts.
- Show prompts with `await input.buttonsAsync(prompt, options)`, `input.textAsync(...)`, etc.
- Render output with `output.markdown(...)`, `output.table(...)`.
- `console.log()` shows in the browser devtools console.

```js
let settings = input.config({
  title: 'Bulk update tool',
  items: [
    input.config.table('mainTable', { label: 'Primary Table' }),
    input.config.field('targetField', { parentTable: 'mainTable' }),
  ],
});

async function main() {
  let confirm = await input.buttonsAsync('Confirm?', [
    { label: 'Run', variant: 'danger' },
    { label: 'Cancel' },
  ]);
  if (confirm === 'Cancel') return;
  // ... do work ...
  output.markdown('# Done');
}

await main();
```

### Pick by question

- Does the script run because Airtable's automation runner fires it? → **Automation Script**
- Does the script run because a user clicks "Run script" in the Scripting Extension? → **Scripting Extension**

The two are NOT interchangeable. Mixing patterns breaks things:

- `input.config({...})` with arguments in an Automation Script → TypeError
- `output.markdown(...)` in an Automation Script → TypeError
- `await input.buttonsAsync(...)` in an Automation Script → TypeError

## Common patterns (both environments)

### Batch updates — Airtable caps at 50 records per call

```js
// CORRECT — batched
let remaining = updates.slice();
while (remaining.length > 0) {
  await table.updateRecordsAsync(remaining.slice(0, 50));
  remaining = remaining.slice(50);
}

// WRONG — single-record updates in a loop are dramatically slower and chew quota
for (let r of records) {
  await table.updateRecordAsync(r.id, { ... });   // don't
}
```

The same 50-record cap applies to `createRecordsAsync`. `selectRecordsAsync` has no batch cap but loads the whole table — keep that in mind for large tables.

### Linked records — array of `{ id }` objects

```js
await table.updateRecordAsync(recordId, {
  'Linked Field': [{ id: 'recXYZ' }],
});
```

Plain strings, arrays of strings, and objects with `recordId` keys all fail. The shape is `[{ id: ... }]`.

### Single-select / multi-select — `{ id }` or `{ name }`

```js
// Either works for writes — prefer `{ id }` for rename safety:
'Status': { id: 'selXXXXX' }      // ← survives option rename
'Status': { name: 'Active' }      // ← breaks if "Active" is renamed
```

For multi-selects, wrap in an array: `'Tags': [{ id: 'sel1' }, { id: 'sel2' }]`.

### Attachments — `{ url, filename }`

```js
'Photos': [
  { url: 'https://example.com/photo.jpg', filename: 'photo.jpg' },
]
```

### Reading fields

- `record.getCellValue('Field Name')` — returns the raw value (linked records as `[{id, name}]`, selects as `{id, name, color}`, attachments as `[{id, url, filename, ...}]`).
- `record.getCellValueAsString('Field Name')` — returns the user-facing display string. Use for text comparisons (esp. when computed fields could surprise you).

### Field type validation before writing

```js
let field = table.getField('Target');
if (field.type !== 'multipleRecordLinks') {
  throw new Error('Target must be a linked-record field');
}
```

### Error handling

```js
try {
  // ... operation ...
} catch (e) {
  console.log('ERROR: ' + e.message);
  // In Automation Scripts, also surface to downstream steps:
  output.set('error', e.message);
  throw e;  // re-throw so Airtable flags the run as failed
}
```

## Cheat sheet

| Operation | Pattern |
|---|---|
| Batch update | `table.updateRecordsAsync(updates.slice(0, 50))` |
| Batch create | `table.createRecordsAsync(records.slice(0, 50))` |
| Single fetch | `await table.selectRecordAsync(recordId, { fields: ['Name'] })` |
| All records | `await table.selectRecordsAsync({ fields: ['Name'] })` — loads whole table |
| Lookup by id (in-memory) | `query.getRecord(recordId)` after a `selectRecordsAsync` |
| Write linked | `{ 'Field': [{ id: 'recXXX' }] }` |
| Write select | `{ 'Field': { id: 'selXXX' } }` |
| Write attachment | `{ 'Field': [{ url: '...', filename: '...' }] }` |
| Today's date (ISO) | `new Date().toISOString()` |
| Field type guard | `table.getField('X').type === 'singleSelect'` |

## DOs and DON'Ts

**DO:**
- Use `getCellValueAsString()` for text comparisons across field types.
- Cache `base.getTable(...)` results in variables — don't re-call inside loops.
- Batch updates/creates in 50s.
- Re-throw caught errors in Automation Scripts so Airtable flags failed runs.
- Use option *ids* (not names) for select-field writes — survives renames.
- Verify field types with `table.getField(...).type` before writing exotic shapes.

**DON'T:**
- Don't hardcode table/field strings deep inside business logic — pull them to the top as constants so renames are one-place fixes.
- Don't await inside synchronous loops the wrong way: `for (let r of records) await table.updateRecordAsync(...)` is correct syntactically but creates a 1-by-1 round-trip storm. Use batched `updateRecordsAsync` instead.
- Don't try to write to computed fields (formula, rollup, lookup, createdTime, lastModifiedTime). Airtable will reject the write.
- Don't use `input.config({...})` with arguments in an Automation Script.
- Don't call `output.markdown` / `output.table` / `input.buttonsAsync` in an Automation Script.

## Airtable Formulas

For formula fields inside Airtable itself (NOT scripts). Quick rules:

- **NEVER add comments inside Airtable formulas.** Airtable's formula engine doesn't have a comment syntax — anything that looks like a comment will fail to compile.
- Reference fields by name with curly braces: `{Field Name}` (single field) or `{Other Table}` is not valid — formulas are scoped to the current table only.
- Functions are case-insensitive (`IF` = `if`) but field names ARE case-sensitive.
- Use `&` for concatenation, NOT `+` (the latter is numeric).
- For conditional logic, prefer `IF()` nested or `SWITCH()` for many branches.

Common patterns:

```
IF({Status} = "Paid", "✓", "")

CONCATENATE({First Name}, " ", {Last Name})

DATETIME_FORMAT({Created}, 'YYYY-MM-DD')

IF(AND({Amount} > 100, {Paid} = TRUE()), "VIP", "Standard")

SWITCH({Tier},
  "gold", "Premium",
  "silver", "Standard",
  "Free"
)
```

If a complex formula isn't compiling, suspect:
- An invisible character (smart quote, em-dash) that the formula parser can't read — retype the offending chunk.
- A field name that contains parentheses or punctuation — wrap in `{Field (Name)}` carefully or rename the field.
- An accidental comment-looking sequence.

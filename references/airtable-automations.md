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

**Default to Automation Script unless the user explicitly says Scripting Extension.** The Automations panel is most Airtable users' default entry point for scripting — Scripting Extension requires installing an extension first and isn't part of the base UI. Most "write me an Airtable script" requests are about Automation Scripts.

### 1. Automation Script (the "Run a script" action inside an automation) — DEFAULT

Background-only. No UI. Receives input from the automation trigger; can output values for downstream automation steps. Reachable in Airtable's left sidebar → **Automations** → add a step → **Run a script**.

- Read trigger inputs via `input.config()` — call it WITHOUT arguments. Input variables are configured in the automation's left panel, not in code.
- Read workspace-level secrets via `input.secret('SECRET_NAME')`. **Critical:** the secret has to be granted to each step that uses it. Each automation **step** that calls `input.secret()` must ALSO declare a matching input variable in its left panel that references the workspace secret — having the secret defined at the workspace level is NOT enough. Calling `input.secret('FOO')` without granting that step access returns falsy, NOT throws. So `if (!token) throw` is the standard guard. When chaining multiple "Run a script" steps in one automation, configure the secret access on EVERY step that needs it — they don't inherit from each other.
- Output to downstream steps via `output.set(key, value)`.
- `console.log()` appears in the automation's run log (NOT the browser console). This is your ONLY progress / debug surface.
- **NO `output.markdown`, NO `output.text`, NO `output.table`, NO `output.inspect`** — those throw `TypeError: output.<x> is not a function` here. They're Scripting-Extension-only.
- **NO `input.buttonsAsync` / `input.textAsync`** — interactive UI is not available in the background runner.
- Execution cap: 120 seconds (recently raised from 30s).
- Can be triggered manually via the "Test" button on the automation, useful for one-shot scripts you don't want to set up a real trigger for.

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

### 2. Scripting Extension (run-in-the-UI scripts) — only when explicitly asked

Foreground, interactive. Used for one-off transforms, bulk fixes, building admin dashboards. Has a richer API. Requires installing the "Scripting" extension in the base — most bases don't have it by default.

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

- Default: **Automation Script** (the user is in the Automations panel).
- **Scripting Extension** only when the user says "Scripting Extension" or describes installing/using the Scripting extension specifically.

The two are NOT interchangeable. Mixing patterns breaks things:

- `input.config({...})` with arguments in an Automation Script → TypeError
- `output.markdown(...)` in an Automation Script → TypeError (verified — common mistake when porting a Scripting Extension script)
- `output.table(...)` / `output.text(...)` / `output.inspect(...)` in an Automation Script → TypeError
- `await input.buttonsAsync(...)` in an Automation Script → TypeError

## Default to table IDs and field IDs, NOT names

For any non-throwaway Airtable script (automations, recurring scripts, anything that lives past one run), reference tables and fields by their **stable IDs** — not their user-facing names. Names are renamed and pluralized constantly during a base's lifecycle; IDs never change once assigned.

```js
// CORRECT — IDs with names in comments. Renames don't break anything.
const T_CLIENTS = 'tbllPOXe15SMC81QS';         // Clients
const F_NAME = 'fldNFd931LGhkIWpE';            // Clients.Name (singleLineText)
const F_SQUARE_ID = 'fldMDtw2hQCQcDbuX';       // Clients.Square Customer ID

const clientsTable = base.getTable(T_CLIENTS);
const record = await clientsTable.selectRecordAsync(recId, {
  fields: [F_NAME, F_SQUARE_ID],
});
const name = record.getCellValueAsString(F_NAME);
await clientsTable.updateRecordAsync(recId, {
  [F_SQUARE_ID]: 'cust_abc',
});

// WRONG — names break silently when someone renames a field. Two failure
// modes seen today: (1) Airtable pluralizes reciprocal linked-record fields
// without warning ("Client" → "Clients"), (2) string-replace refactors of
// constant names can clobber neighbouring identifiers ("APPT_CLIENT" is a
// substring of the new "APPT_CLIENTS").
const F_NAME = 'Name';
const F_SQUARE_ID = 'Square Customer ID';
```

**Where this works:** every API that accepts a field reference also accepts the field ID — `getCellValue()`, `getCellValueAsString()`, `selectRecordsAsync({ fields: [...] })`, `selectRecordAsync(id, { fields: [...] })`, the `fields` keys in `createRecordsAsync` / `updateRecordsAsync`, `table.getField(...)`. Same for `base.getTable(...)`.

**The one exception — Airtable formulas.** Formula fields reference other fields with `{Field Name}` curly-brace syntax; there is no `{fld...}` ID form. Inside a formula, you're stuck with names.

**Practical setup:** declare a constants block at the top of every script with all the IDs you'll use, each with the user-facing name as a trailing comment. When the base schema is exported, IDs are right there in the JSON next to the names — easy to copy in.

```js
// Tables
const T_CLIENTS = 'tbllPOXe15SMC81QS';              // Clients
const T_APPOINTMENTS = 'tbleTXCyKb3v7IOPY';         // Appointments

// Clients fields
const F_CL_NAME = 'fldNFd931LGhkIWpE';              // Name
const F_CL_EMAIL = 'fld1BHkfMAd6McaHx';             // Email
const F_CL_SQUARE_ID = 'fldMDtw2hQCQcDbuX';         // Square Customer ID

// Appointments fields
const F_AP_CUSTOMER = 'fldNw09E911YV2S8X';          // Customer (linked → Customers)
const F_AP_CLIENTS = 'fldcCUrXf8AUtZRgr';           // Clients (linked → Clients)
```

Reads like noise the first time, but renames stop being a class of bugs.

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

### `updateRecordsAsync` rejects duplicate record IDs in a single batch

If the same record ID appears twice in the array passed to `updateRecordsAsync`, Airtable rejects the ENTIRE call with:

```
Error: Record "recXXXXXXXXXXXXX" was specified twice in this request.
```

No records get updated — it's all-or-nothing per batch. The duplicate doesn't have to be in the same chunk of 50; any duplicate across the full payload triggers it.

This is the typical failure mode of a **many-to-one migration** — e.g. consolidating two source tables when multiple source rows map to the same destination row (Customer A and Customer B both match Client X by email, so each one pushes an update for Client X). The fix is to dedupe by destination ID using a Map instead of an Array:

```js
// WRONG — duplicate Client IDs across the Array trigger the rejection
const updates = [];
for (const src of sources) {
  const dest = findDestinationFor(src);
  updates.push({ id: dest.id, fields: { /* merge from src */ } });
}
await table.updateRecordsAsync(updates);  // throws when two `src` map to same `dest`

// CORRECT — Map keyed by destination ID, last-write-wins (or merge in-place)
const updatesById = new Map();
for (const src of sources) {
  const dest = findDestinationFor(src);
  let entry = updatesById.get(dest.id);
  if (!entry) {
    entry = { id: dest.id, fields: {} };
    updatesById.set(dest.id, entry);
  }
  Object.assign(entry.fields, mergeFrom(src, entry.fields));
}
const updates = Array.from(updatesById.values());
// ... batch-write as usual
```

For "fill if empty"-style merges, read the empty check off the **original destination record** (loaded once at the start), not off the in-progress merge entry — otherwise the first source row's value blocks subsequent ones from filling other empty fields.

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

All examples use field-ID style (the recommended default). Field IDs come from the schema export (`base-schema-*.json`) or from Studio's Data tab → "Customize field type" panel.

| Operation | Pattern |
|---|---|
| Get table by ID | `base.getTable('tblXXX')` |
| Get field on a table | `table.getField('fldXXX')` |
| Batch update | `table.updateRecordsAsync(updates.slice(0, 50))` |
| Batch create | `table.createRecordsAsync(records.slice(0, 50))` |
| Single fetch | `await table.selectRecordAsync(recordId, { fields: ['fldNAME', 'fldEMAIL'] })` |
| All records | `await table.selectRecordsAsync({ fields: ['fldNAME'] })` — loads whole table |
| Read field | `record.getCellValue('fldXXX')` or `getCellValueAsString('fldXXX')` |
| Lookup by id (in-memory) | `query.getRecord(recordId)` after a `selectRecordsAsync` |
| Write linked | `{ 'fldLINK': [{ id: 'recXXX' }] }` |
| Write select | `{ 'fldSEL': { id: 'selXXX' } }` |
| Write attachment | `{ 'fldATT': [{ url: '...', filename: '...' }] }` |
| Today's date (ISO) | `new Date().toISOString()` |
| Field type guard | `table.getField('fldXXX').type === 'singleSelect'` |

## DOs and DON'Ts

**DO:**
- **Reference tables and fields by ID, not by name.** See "Default to table IDs and field IDs" above. Pulls renames out of the failure-mode set entirely.
- Use `getCellValueAsString()` for text comparisons across field types.
- Cache `base.getTable(...)` results in variables — don't re-call inside loops.
- Batch updates/creates in 50s.
- Re-throw caught errors in Automation Scripts so Airtable flags failed runs.
- Use option *ids* (not names) for select-field writes — survives renames (same principle as field IDs above).
- Verify field types with `table.getField(...).type` before writing exotic shapes.

**`output` API by environment** — this is the most common mistake when porting scripts:

| Method | Automation Script | Scripting Extension |
|---|---|---|
| `output.set(key, value)` | ✅ — pass values to downstream automation steps | ❌ — not available |
| `output.markdown(string)` | ❌ — `TypeError` | ✅ — rendered markdown |
| `output.text(string)` | ❌ — `TypeError` | ✅ — plain text |
| `output.table(array | object)` | ❌ — `TypeError` | ✅ — tabular view |
| `output.inspect(value)` | ❌ — `TypeError` | ✅ — inspectable view |
| `output.clear()` | ❌ — **doesn't exist anywhere** | ❌ — **doesn't exist anywhere** |
| `console.log(...)` | ✅ — appears in the automation's run log | ✅ — appears in browser devtools |

For Automation Scripts, your ONLY user-visible surfaces are `console.log()` (run log) and `output.set()` (step output panel). If you need to report a list of results, log them line-by-line with `console.log` or `output.set("resultsJson", JSON.stringify(results))` so the JSON shows up in the step output inspector.

`output.clear()` is sometimes listed in older third-party reference docs as a valid Scripting Extension method — it isn't. Calling it throws `TypeError: output.clear is not a function` in both environments.

**DON'T:**
- Don't hardcode table/field strings deep inside business logic — pull them to the top as constants so renames are one-place fixes.
- Don't await inside synchronous loops the wrong way: `for (let r of records) await table.updateRecordAsync(...)` is correct syntactically but creates a 1-by-1 round-trip storm. Use batched `updateRecordsAsync` instead.
- Don't try to write to computed fields (formula, rollup, lookup, createdTime, lastModifiedTime). Airtable will reject the write.
- Don't use `input.config({...})` with arguments in an Automation Script.
- Don't call `output.markdown` / `output.table` / `input.buttonsAsync` in an Automation Script.
- Don't push duplicate record IDs into a single `updateRecordsAsync` call. Airtable rejects the WHOLE batch with `Error: Record "X" was specified twice in this request.` Dedupe by destination ID with a Map before flushing — see the many-to-one migration pattern in "Batch updates" above.

## Airtable Formulas

For formula fields inside Airtable itself (NOT scripts). Quick rules:

- **NEVER add comments inside Airtable formulas.** Airtable's formula engine doesn't have a comment syntax — anything that looks like a comment will fail to compile.
- **Guard against blank inputs by default.** Airtable surfaces `#ERROR!` (or `#NaN!` for divide-by-blank) when arithmetic, date, or many string operations touch a blank field — `{A} * {B}` errors when either is blank, `{A} / {B}` errors when `{B}` is blank, `DATEADD({Start At}, 20, 'minutes')` errors when `{Start At}` is blank, and one upstream `#ERROR!` propagates through every downstream formula that references it. Wrap any formula whose inputs could be empty with an `IF()` guard returning `BLANK()` in the empty branch. Prefer explicit `IF()` / `AND()` guards over a catch-all `IFERROR(<expr>, BLANK())` — explicit guards keep intent readable and don't mask unrelated bugs (a typo'd field name silently returns blank instead of failing loudly). Reach for `IFERROR()` only when inputs come from genuinely uncontrolled sources.

  ```
  IF({Start At}, DATEADD({Start At}, 20, 'minutes'), BLANK())
  IF(AND({Quantity}, {Price}), {Quantity} * {Price}, BLANK())
  IF({Divisor}, {Numerator} / {Divisor}, BLANK())
  ```
- Reference fields by name with curly braces: `{Field Name}` (single field) or `{Other Table}` is not valid — formulas are scoped to the current table only.
- Functions are case-insensitive (`IF` = `if`) but field names ARE case-sensitive.
- Use `&` for concatenation, NOT `+` (the latter is numeric).
- For conditional logic, prefer `IF()` nested or `SWITCH()` for many branches.

Common patterns (blank-guards applied where inputs could be empty):

```
IF({Status} = "Paid", "✓", "")

CONCATENATE({First Name}, " ", {Last Name})

IF({Created}, DATETIME_FORMAT({Created}, 'YYYY-MM-DD'), BLANK())

IF(AND({Amount} > 100, {Paid} = TRUE()), "VIP", "Standard")

IF({Start At}, DATEADD({Start At}, 20, 'minutes'), BLANK())

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

# Multiple Data Sources in One Block

A Vibe Coding block can connect to **several data sources at once**. Declare them with
`datasource.define()` and target one per hook with `from:`.

This supersedes the old one-table-per-block limit. Blocks that needed a second table used to
require an invisible helper block publishing to a `window` global — that workaround is no
longer necessary for plain multi-table reads. See [../references/helper-blocks.md](../references/helper-blocks.md)
for what helper blocks are still genuinely for.

## The pattern

```jsx
import { datasource, useRecords, useRecordCreate, q } from "@/lib/datasource";

var ds = datasource.define({
  people: "74d2cbfd-f2cb-4f5c-82d9-0d3a0651e531",
  shifts: "ec7a6311-f6c3-4c99-881d-aae308148716",
  feedback: "52461ab9-9912-4e15-bcf4-8838d38c64ea",
});

var peopleSelect = q.select({ email: "Email", firstName: "First name" });
var shiftSelect = q.select({ jobCode: "Job Code" });
var feedbackCreateFields = q.select({ comments: "Comments", crewMember: "Crew Member" });

export default function Block() {
  var people = useRecords({ from: ds.people, select: peopleSelect, count: 20 });
  var shifts = useRecords({ from: ds.shifts, select: shiftSelect, count: 5 });

  var createFeedback = useRecordCreate({
    from: ds.feedback,
    fields: feedbackCreateFields,
    onSuccess: function () { /* … */ },
  });
  // …
}
```

**`from:` is required on every data hook once a block has more than one source.** Omitting it
throws. With exactly one source you can skip `datasource.define` and omit `from` entirely —
the hooks default to that source.

Applies to: `useRecords`, `useRecord`, `useLinkedRecords`, `useFieldOptions`, `useMetric`,
`useChartData`, `useRecordCreate`, `useRecordUpdate`, `useRecordDelete`.

Does **not** apply to `useUpload` and `useCurrentRecordId` — those are app-level and take no `from`.

`useProxyFetch` (REST API sources) is **also datasource-scoped**, but takes the alias as its **function argument** rather than a `from:` option — `useProxyFetch(ds.store)`. With a single datasource `useProxyFetch()` works bare; once the block has more than one, omitting the alias throws, exactly like omitting `from:` on a record hook. See [rest-api.md](rest-api.md#multiple-datasources).

## The values must be inline string literals

Softr statically analyses `datasource.define()`, exactly like `q.select()`. Hoisting the ids
into constants fails to compile:

```jsx
// WRONG — "datasource.define() object values must be string literals"
var PEOPLE_DS_ID = "74d2cbfd-…";
var ds = datasource.define({ people: PEOPLE_DS_ID });

// CORRECT — literals, in place
var ds = datasource.define({ people: "74d2cbfd-…" });
```

The error text is explicit, so this one fails fast rather than silently — but it's an easy
reflex to hoist "magic strings" into named constants, and that reflex is wrong here.

## `select:` must be a plain module-scope identifier

*Verified live 2026-09-18 (Softr Database; probe block + network capture in a draft preview).*

With more than one connection, Softr has to attribute every `q.select` to the connection it is
used with. The observed behaviour says it does that statically, from the identifier you pass as
`select:` (the mechanism is inferred; the outcome below is what was captured). An expression
breaks the attribution:

```jsx
// WRONG — compiles, runs, and the query returns records with `fields: {}`. No error.
var order = useRecord({ from: ds.orders, select: isAdmin ? adminSelect : publicSelect, recordId: id });

// CORRECT — one module-scope identifier per hook
var orderSelect = q.select({ title: "FIELD_ID1", status: "FIELD_ID2" });
var order = useRecord({ from: ds.orders, select: orderSelect, recordId: id });
```

Treat an inline `q.select({...})` written inside the hook options the same way: hoist it to
module scope and pass the identifier (the pattern at the top of this file already does). The
same goes for a mutation hook's `fields:`.

In a **single-datasource** block the same ternary *works* — there is nothing to attribute — but
it behaves as a **union** of both branches, not a choice between them. Which is the next rule.

## One connection = one read payload (the union of its selects)

*Verified live 2026-09-18; the block-visibility gate 2026-10-05.*

The records endpoint is per block + connection —
`/blocks/<blockId>/datasources/<name>/records` (`<name>` is the name given in `datasource.define`; see the note below) — and it returns the **UNION of every field
named by any READ `q.select` attributed to that connection**. Two selects on one connection do
NOT produce two payloads: every read hook on that connection gets all the fields, for every
viewer.

*On `<name>`.* Block reads go to `…/blocks/<block>/datasources/<name>/records`, where `<name>` is the name given in `datasource.define` (seen on Softr Database on 2026-10-08 and on HubSpot on 2026-10-05), while saves go to `…/records-trigger/…` under a UUID. The 2026-09-18 Softr Database capture recorded an id in that position, which is still unexplained. It only matters when reading or routing a network log; the route patterns for failing reads are in the Forcing states section of [browser-checks.md](../references/browser-checks.md).

**So "request the private field only for admins" is not privacy.** A second select, or a ternary
between a public and an admin select, still ships the private field to every browser that loads
the block — it is simply not rendered. Anyone can read it in the network tab.

What does *not* join the union: a mutation hook's `fields:` select. Write-only fields stay out of
the read payload.

**Every row carries its record id, whatever the select.** The union governs *fields*; the records
endpoint returns each row's own record id beside them however narrow the select is. A connection
whose only select was one email field still gave anyone who crafted the request every row's id
with its email (noted in a production block's security review, 2026-09-19). So wherever knowing a
record id lets someone act (a by-id fetch, an update addressed by `recordId`, a link write that a
Source condition then keys on), treat ids as access keys: a connection hands every row it releases,
with its id, to every viewer allowed to call it. Narrowing the select does not withhold ids; only
fewer rows (a Source condition) or a gated page or block does. A link field in a select ships the
*linked* records' ids too (`{ id, label }`). To filter by a link without shipping them, filter on
a readonly key looked up through the link instead
([reading.md](reading.md#operator-semantics-on-the-server)).

**Remedy.** Connect the **same table a second time** — Softr allows it, and the second connection
gets its own `dataSourceId` — and read the private field only through that connection, from a
hook that non-privileged browsers never run:

```jsx
var ds = datasource.define({
  orders: "11111111-…",        // everyone: public fields only
  ordersAdmin: "22222222-…",   // same table, second connection: the private fields
});

var orderSelect = q.select({ title: "FIELD_ID1", status: "FIELD_ID2" });
var orderAdminSelect = q.select({ internalNotes: "FIELD_ID9" });

// Mounted by Block() ONLY when the viewer is an admin — so a non-admin browser never
// issues the request. (`useRecord` honours `enabled: false`; `useRecords` does NOT —
// see reading.md — which is why the gate is the mount, not an option.)
function AdminNotes({ recordId }) {
  var admin = useRecord({ from: ds.ordersAdmin, select: orderAdminSelect, recordId: recordId, enabled: !!recordId });
  // …
}
```

Or put the private field in a separate block whose visibility is group-gated.

Know what this buys you. Not *rendering* the hook keeps the field out of ordinary browsers, but
the endpoint still exists. Two all-or-nothing gates are enforced on it, list and by-id: page VIEW
permission, and the **block's own Visibility** (`predefinedUserGroup` + `customUserGroupIds`). A
viewer outside either gets a 403 (block gate verified 2026-10-05, on HubSpot). Past those gates, on
an ungated block on a page any logged-in user may view, **every connected datasource is readable by
any logged-in user who crafts the request**. A connection's **Source conditions are the only
server-side ROW gate**; the only server-side gate on the *field* is a page or block the viewer
cannot see.

**A block gated to a user group may therefore read unfiltered connections** (verified 2026-10-05).
A staff dashboard gated to an "Account managers" group, with no Source condition on its deals and
tickets connections, gave both members all 41 deals and 16 tickets, and gave clients, a Softr-only
user and logged-out visitors 403 on list and by-id. The gate belongs to the block, not the table:
connect the same table to an ungated block and it is open again. See
[../references/softr-mcp.md](../references/softr-mcp.md#what-the-server-enforces-on-a-blocks-data-endpoints).

Two selects on different connections may reuse an alias name (`customer` on both) without
colliding. Aliases resolve **per hook**, though: a hook's `where` / `orderBy` may name only aliases
from that hook's own `select`, or the block crashes at runtime — see
[reading.md](reading.md#filter-and-sort-aliases-must-be-in-the-same-hooks-select).

## Mutation Actions register per TABLE, not per connection

*Verified live 2026-09-18.*

The second connection above is for **reads**. Actions are filed per table:

- Several `useRecordUpdate` hooks on one table merge into **ONE `UPDATE_RECORD` action** whose
  field list is the union of their `fields:` selects.
- A hook pointed at the *second* connection of a table (`from: ds.ordersAdmin`) was still filed
  under the **first** connection's `dataSourceId`.

So **point every write at the table's first connection**, and expect one action per table and
operation in `vibe_coding_block_get_settings` / the Actions tab — that is the row you re-tighten
after each push. Details in [writing.md](writing.md#actions-register-per-table-not-per-hook-or-connection).

## Getting the datasource ids — ask for CODE, never for a value

The id is a plain **UUID**. It is *not* the underlying table id (`tbl…` in Airtable), and not
the `ds_id_1` shape used as a placeholder in Softr's own developer guide.

**Studio's AI chat fabricates these when asked in prose.** Verified 2026-07-22: asked three
times for the ids of the same three connected tables, it returned three different sets, once
recycling a previously-mentioned table's uuid for a different table. All three answers were
confidently worded. None were flagged as uncertain.

Ask it to **write code** instead:

```
Write a datasource.define call covering every data source connected to this
block, plus one useRecords per source. Output code only.
```

Code generation is bound to the block's real connections, so the ids come out correct — the
same reason Softr's assistant reliably inlines real select options when scaffolding a form but
invents values when asked to recite one.

**Then verify by running it.** The scaffold renders a list per source; if real rows appear
under each heading, every alias maps to the table you think it does. A wrong uuid fails safe
(it matches no datasource, so the block errors) — but a *swapped* pair of correct uuids does
not, and only running it will catch that.

## When you still want a helper block

Multi-datasource removes the need for helpers as a *data-access* workaround. They remain the
right tool for:

- **Cross-block communication** — one block triggering or feeding another on the same page.
- **Publishing computed state** — expensive derivations shared by several consumers.
- **Rich foreign data via `useLinkedRecords`** — that hook still only returns `{id, title}`
  and silently ignores extra fields in `select`. Reading the foreign table directly with its
  own `from:` is now the simpler fix.

## Worked example

`crew-feedback-form.jsx` — a public feedback form that reads a person from **People** by an
`email` URL param, resolves a **Shifts** record from a job-code param, and writes a row to
**Feedback** linking both. One block, three sources, no helpers, no `window` globals.

**Read it against the rules above before copying it.** On a public page every logged-out visitor
may call the People connection, and the endpoint returns every row the Source conditions allow,
with every field the block's read selects name. The `email` URL param narrows nothing on the
server: it ends up in a `where`, which is a request parameter the caller controls, and there is no
logged-in user for a Source condition to match. Select only what the form must show, assume every
row of it is public, and if that is not acceptable resolve the person server-side (a Softr
Workflow) instead of reading People from the block.

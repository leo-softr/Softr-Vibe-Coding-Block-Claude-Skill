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

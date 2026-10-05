# Reading Data

Fetching, filtering, sorting, pagination, metrics, charts, and current user.

## Table of Contents

- [Query Builder](#query-builder)
- [useRecords -- Fetch a Paginated List](#userecords----fetch-a-paginated-list) — incl. [`enabled: false` is ignored](#userecords-ignores-enabled-false)
- [useRecord -- Fetch a Single Record](#userecord----fetch-a-single-record) — the detail-page pattern; no auto-scoping
- [useLinkedRecords -- Fetch Linked/Related Options](#uselinkedrecords----fetch-linkedrelated-options)
- [useFieldOptions -- Fetch Single/Multi-Select Choices](#usefieldoptions----fetch-singlemulti-select-choices)
- [Filtering](#filtering) — incl. [server-side linked-record filters](#filtering-by-a-linked-record-server-side)
- [Sorting](#sorting)
- [Current User](#current-user)
- [Metrics](#metrics)
- [Chart Data](#chart-data)

## Query Builder

Field mappings must be static (no dynamic keys or computed values -- hard constraint for Softr's static analysis):

```jsx
import { q } from "@/lib/datasource";

var select = q.select({
  title: "FIELD_ID1",
  description: "FIELD_ID2",
  createdAt: "FIELD_ID3",
});
```

**Declare every `q.select` at module scope and pass it by identifier** (verified live 2026-09-18).
In a multi-datasource block a `select:` that is a ternary (`select: a ? X : Y`) cannot be
attributed to a connection and the query returns `fields: {}` with no error; treat an inline
`q.select({...})` inside hook options the same way and hoist it. And a connection's read payload
is the **union** of every read select on it — a second or conditional select never narrows what
the browser receives, so it is not a privacy tool. Both rules, with the remedy, in
[multi-datasource.md](multi-datasource.md#select-must-be-a-plain-module-scope-identifier).
(The short inline `q.select` snippets below are single-datasource illustrations.)

## useRecords -- Fetch a Paginated List

```jsx
import { useRecords, q } from "@/lib/datasource";

var result = useRecords({
  select: q.select({ name: "FIELD_ID1", email: "FIELD_ID2" }),
  count: 6,           // records per page (default 6, max 100)
  where: q.text("name").contains("Alice"),  // optional filter
  orderBy: q.desc("createdAt"),             // optional sort
  enabled: true,                            // accepted, but `false` is IGNORED — see below
});

var data = result.data;
var status = result.status;       // "pending" | "success" | "error"
var error = result.error;
var fetchNextPage = result.fetchNextPage;
var hasNextPage = result.hasNextPage;
var isFetching = result.isFetching;
var isFetchingNextPage = result.isFetchingNextPage;
var refetch = result.refetch;
var isRefetching = result.isRefetching;

// Flatten pages into a single array:
var items = (data && data.pages) ? data.pages.flatMap(function(p) { return p.items; }) : [];
```

**CRITICAL:** Only ONE `useRecords` call **per datasource**. Fetch that table's data in one call and filter client-side. Multiple `useMetric` calls ARE allowed.

**CRITICAL:** The options object must be an **inline literal** at the call site. Passing it
through a variable or a wrapper function (`useRecords(buildOpts())`) **fails to compile** —
verified live 2026-08-25, hit in a production block; the fix was changing the wrapper to take
the hook's *result* instead. Share `q.select` mappings between hooks, never whole options
objects.

A block can connect to **several data sources** and call `useRecords` once per source — declare them with `datasource.define()` and pass `from:` on every hook. See [multi-datasource.md](multi-datasource.md). (This replaces the old one-table-per-block limit; blocks no longer need an invisible helper block just to read a second table.)

### `useRecords` ignores `enabled: false`

*Verified live 2026-09-18 (network capture).* `useRecords({ ..., enabled: false })` **fetches
anyway** — with a literal `false` and with a variable alike. `useRecord` is different: it honours
`enabled: false` and issues no request. (`useLinkedRecords`, `useMetric` and `useChartData` were
not probed — don't assume either behaviour for them.)

So `enabled` cannot make a list query conditional, and it cannot keep a query away from viewers
who should not run it. Two things that do work:

```jsx
// 1. Gate by MOUNT — put the hook in a child component and render it only when needed.
function CommentsSection({ orderId }) {
  var comments = useRecords({ from: ds.comments, select: commentSelect, count: 50,
    where: q.array("order").hasAllOf([orderId]) });
  // …
}
// in Block():  {canSeeComments && <CommentsSection orderId={recordId} />}

// 2. Keep the hook mounted but give it a match-nothing `where` until it should load.
var rows = useRecords({ select: select, count: 50,
  where: q.text("email").is(email || "__no_match__") });
```

Option 1 is the only one that sends no request at all; option 2 still calls the endpoint and gets
zero rows back. Remember the child must be defined at **module scope** (SKILL.md Self-validate).

### Loading All Records (Auto-Pagination)

```jsx
import { useState, useEffect } from "react";

var result = useRecords({ select: select, count: 100 });

useEffect(function() {
  if (result.hasNextPage && !result.isFetchingNextPage && result.status === "success") {
    result.fetchNextPage();
  }
}, [result.hasNextPage, result.isFetchingNextPage, result.status, result.fetchNextPage]);
```

## useRecord -- Fetch a Single Record

```jsx
import { useRecord, useCurrentRecordId, q } from "@/lib/datasource";

var detailSelect = q.select({ title: "FIELD_ID1", description: "FIELD_ID2" });

var recordId = useCurrentRecordId(); // the URL's `recordId` param — can be null
var result = useRecord({
  select: detailSelect,
  recordId: recordId,
  enabled: !!recordId,               // honoured by useRecord: no id → no request
});

var record = result.data && result.data.id === recordId ? result.data : null; // trust only a matching id
```

**There is NO detail-page auto-scoping (verified live 2026-09-18, Softr Database, network
capture).** The runtime sends `pageContext: null` with the block's data requests — nothing tells
the server which record the page is "about". Consequences:

- `useRecords({ count: 1 })` on a detail page returns the **FIRST row of the table**, not the
  URL's record. It looks right on the first record you test and wrong on every other.
- `useCurrentRecordId()` **does** return the URL's `recordId`, and
  `useRecord({ from, select, recordId })` fetches exactly that record (it hits `/records/<id>`).
  That is the detail-page pattern — the only one.
- `useRecord` with a **null / missing id falls back to a list call** and hands back whatever that
  returns. So always pass `enabled: !!recordId` (`useRecord` honours `enabled: false` — no
  request is made) and verify `data.id === recordId` before rendering or, worse, writing.

**A recordId-less `useRecord` — what the older note here meant, and its limits.** This file used
to say that `useRecord({ select })` with no `recordId` "loads the record the block is bound to
via its data-source binding in Studio" (seen on one deployed Airtable-backed stats block, July
2026, which rendered live values that way). Read that in the light of the capture above: no
record context is sent, and a null-id `useRecord` falls back to a list call — so the likeliest
explanation of the July block is that it was showing the list fallback's row, which is the
"right" record only when the connection's Source conditions/sort leave exactly that row first.
(That reading is an inference: the Airtable block was not re-probed, and the 2026-09-18 capture
was on Softr Database.) Either way it is not a binding you can rely on, and never the way to
build a detail page. The review corollary
survives in a narrower form: a recordId-less `useRecord` in a **working, deployed** block is not
by itself proof of a defect — check what it actually loads (and for which viewers) before
flagging it, and when editing such a block, know that adding an explicit `recordId` changes what
it loads on pages whose URL carries no `recordId` param.

## useLinkedRecords -- Fetch Linked/Related Options

```jsx
import { q, useLinkedRecords } from "@/lib/datasource";

var result = useLinkedRecords({
  select: q.select({ category: "$CATEGORY_FIELD_ID" }),
  field: "category",    // the ALIAS from q.select(), NOT the raw field ID
  sortOrder: "ASC",     // "ASC" | "DESC"
  search: "",           // optional search string
  enabled: true,        // defer loading until needed
  count: 50,            // optional page size — default 100, max 1000
});

var options = (result.data && result.data.pages) ? result.data.pages.flatMap(function(p) { return p.items; }) : [];
```

**CRITICAL:** The `field` prop takes the ALIAS from `q.select()`, NOT the raw field ID. Items are shaped as `{ id, title }` -- use `opt.title` (NOT `opt.label`).

## useFieldOptions -- Fetch Single/Multi-Select Choices

Returns the current option list for any `singleSelect` / `multipleSelects` field — without hardcoding option IDs in your block. Useful when the schema's option list changes (renames, additions, reorders) and you don't want to redeploy the block every time.

```jsx
import { useFieldOptions, useRecords, q } from "@/lib/datasource";

var specSelect = q.select({ status: "Status" });

// REQUIRED: a companion records query in the SAME block loads the table schema that
// useFieldOptions reads from. Without it, useFieldOptions settles to `{ options: [] }`
// (isLoading false, length 0) even though the field has choices. count: 1 is enough.
useRecords({ select: specSelect, count: 1 });

var statusOptions = useFieldOptions({
  select: specSelect,
  field: "status",   // the ALIAS from q.select(), NOT the raw field ID
});

// statusOptions → { options: [...], isLoading: bool }
// statusOptions.options → [{ id: "sel...", label: "Active", color: "greenLight1" }, ...]
//   id    — stable option id (use as a React key; NOT needed in mutate payloads — SELECT
//           fields write by LABEL string on the current platform, verified 2026-08-25)
//   label — display string AND the value to write in mutate payloads
//   color — Airtable swatch color name (optional; handy for tinting chips)
```

**⚠️ Gotcha — requires a companion `useRecords` (verified 2026-06-12).** `useFieldOptions`
only populates once an active `useRecords` in the same block has loaded that table's schema.
This bites hardest in **write-only / invisible helper blocks** (the natural home for an
option-publishing helper) because they otherwise never query records — so `options` stays
`[]` forever with `isLoading: false`, which looks like "the field has no choices." The fix is
a throwaway `useRecords({ select, count: 1 })` alongside the `useFieldOptions` call(s); the
same `select` object can be shared by both. Reuse one `select` for many fields and call
`useFieldOptions` once per field (alias). Symptom to recognise: hook returns
`{ options: [], isLoading: false }` while the block is correctly bound to the data source.

**When to use this vs. hardcoding:**

- **Use `useFieldOptions`** when option labels could change post-deploy — selects with rapidly-evolving lists, user-editable choices, or any case where re-pasting blocks for an option rename is annoying. Since SELECT fields write by label (verified 2026-08-25), live options also keep write payloads rename-proof: render and write `option.label`. Hardcoded labels remain fine as a display-only loading fallback while the live options fetch. Cross-table case: to render a select field from table B inside a block bound to table A (e.g. an intake form bound to Jobs that needs the Wigs `Color` options), put the `useRecords` + `useFieldOptions` in a hidden helper block bound to table B and publish the options to a `window` global (see [helper-blocks.md](../references/helper-blocks.md)).
- **Hardcode** when the option set is stable and frequently referenced (e.g. a status enum that drives a state machine), so the label vocabulary lives in source and rename-safety is enforced by greppable constants. A robust middle ground: prefer the live options, fall back to a hardcoded list per field so the UI still renders if the helper hasn't published yet.

`useFieldOptions` is the read-side equivalent of using `useLinkedRecords` for foreign records — it abstracts away the field's option store. Items are shaped `{ id, label, color }` (note: `label`, not `title` like `useLinkedRecords`).

## Filtering

Build filters with typed builders. Filters support up to 2 levels of nesting.

**Text fields** -- `q.text(field)`:
`is`, `isNot`, `contains`, `startsWith`, `endsWith`, `isOneOf`, `isNoneOf`, `hasAllOf`, `isEmpty`, `isNotEmpty`

**Number fields** -- `q.number(field)`:
`is`, `isNot`, `gt`, `gte`, `lt`, `lte`, `between`, `isEmpty`, `isNotEmpty`

**Boolean fields** -- `q.boolean(field)`:
`is`, `isNot`, `isEmpty`, `isNotEmpty`

**Date fields** -- `q.date(field)`:
`is`, `isNot`, `gt`, `gte`, `lt`, `lte`, `between`, `isNotBetween`, `isEmpty`, `isNotEmpty`

**Array fields** -- `q.array(field)`:
`is`, `isOneOf`, `isNoneOf`, `hasAllOf`, `isEmpty`, `isNotEmpty`

**Logical combinators**: `q.and(...)`, `q.or(...)`

```jsx
where: q.and(
  q.text("name").contains("Alice"),
  q.number("age").gte(18),
  q.or(
    q.boolean("isActive").is(true),
    q.text("notes").isNotEmpty()
  )
)
```

### Filtering by a linked record (server-side)

*Verified live 2026-09-18 (Softr Database, network capture).* A linked-record field filters on
the server with the array builder and the linked record's id — no need to load the whole child
table and filter client-side:

```jsx
var commentSelect = q.select({ order: "LINK_FIELD_ID", body: "FIELD_ID2" });

var comments = useRecords({
  from: ds.comments,
  select: commentSelect,
  count: 50,
  where: q.array("order").hasAllOf([orderId]),   // "order" = the link field's ALIAS
});
```

On the wire the alias is resolved to the field id:
`{ subject: <fieldId>, type: "ARRAY", operator: "HAS_ALL_OF", value: [orderId] }`. Alias → field
attribution is **per datasource**, so two selects on different connections may use the same alias
name for different fields and each filter still resolves against its own connection.

`orderId` must be a real id when the hook runs — `useRecords` cannot be switched off with
`enabled: false` ([above](#userecords-ignores-enabled-false)), so mount this query in a child
component that only renders once the parent record has loaded.

**Reading the link back:** a linked field can arrive as a **single `{ id, label }` object**, not
only as an array of them. Normalise before you `.map()` or compare ids:

```jsx
var links = Array.isArray(v) ? v : (v ? [v] : []);
```

## Sorting

```jsx
orderBy: q.desc("createdAt")
orderBy: q.asc("lastName")
orderBy: [q.asc("lastName"), q.asc("firstName")]  // multiple fields
```

## Current User

```jsx
import { useCurrentUser } from "@/lib/user";

var user = useCurrentUser();
// Returns null if not logged in
// Fields: { id, fullName, firstName, lastName, email, avatar } (all string or null)
// Note: `id` is only present when user sync is enabled.
```

**`where: q.text("ownerEmail").is(user.email)` is not access control.** It shapes the UI, but the
caller controls that parameter. To restrict rows to the logged-in user on the server, put the
condition in the connection's Source conditions, as the whole value: `{USER:::EMAIL}` (with
braces) for the user's email, or `USER:::<user field id>` (no braces) for one of the user's own
fields, e.g. their company (verified 2026-10-05 on HubSpot; fails closed when the field is empty).
See [../references/softr-mcp.md](../references/softr-mcp.md#logged-in-user-values-in-source-conditions).

**Custom user-record fields** are first-class: pass a `properties` map (aliased like a `select` query) and read them under `user.properties`:

```jsx
var user = useCurrentUser({
  properties: {
    stripeId: "FIELD_ID1",
    plan: "FIELD_ID2",
  },
});
// user.properties.stripeId, user.properties.plan
```

**For user groups / role ONLY** -- these are not exposed by `useCurrentUser()` (not even via `properties`); use `window.__softr_current_user`:

```jsx
var softrUser = window.__softr_current_user || {};
var userGroups = softrUser.userGroups || [];
var isPremium = userGroups.some(function(g) { return g.name === "Premium Member"; });
```

## Metrics

```jsx
import { useMetric, q, metric } from "@/lib/datasource";

var result = useMetric({
  select: q.select({ revenue: "$REVENUE_FIELD_ID" }),
  metric: metric.sum("revenue"),
  where: q.date("createdAt").gte("2025-01-01"),
});
// result.data is the aggregated value (number)
```

Aggregations: `metric.sum(field)`, `metric.avg(field)`, `metric.max(field)`, `metric.min(field)`, `metric.distinct(field)`, `metric.count()`

## Chart Data

```jsx
import { useChartData, q, metric } from "@/lib/datasource";

var result = useChartData({
  select: q.select({ date: "$DATE_FIELD_ID", revenue: "$REVENUE_FIELD_ID" }),
  orderBy: q.asc("date"),
  metric: { revenue: metric.sum("revenue") },
  groupBy: metric.groupBy("date", metric.bucket.month.long),
});
```

**Grouping buckets** — pick by what you want the x-axis to show:

| Bucket constant | Sample output | Use for |
|---|---|---|
| `metric.bucket.year` | `"2025"` | Yearly trends |
| `metric.bucket.month.iso` | `"2025-03"` | Monthly trends, sortable x-axis |
| `metric.bucket.month.long` | `"March 2025"` | Monthly trends, human-readable labels |
| `metric.bucket.day.iso` | `"2025-03-15"` | Daily trends, sortable x-axis |
| `metric.bucket.day.long` | `"Mar 15, 2025"` | Daily trends, human-readable labels |

Pair `.iso` variants with `orderBy: q.asc(...)` for correct chronological sorting; use `.long` variants when the bucket value is rendered directly as a label.

Use **recharts** with shadcn's chart wrapper:

```jsx
import { LineChart, Line, XAxis, CartesianGrid } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
```

# Reading Data

Fetching, filtering, sorting, pagination, metrics, charts, and current user.

## Table of Contents

- [Query Builder](#query-builder)
- [useRecords -- Fetch a Paginated List](#userecords----fetch-a-paginated-list)
- [useRecord -- Fetch a Single Record](#userecord----fetch-a-single-record)
- [useLinkedRecords -- Fetch Linked/Related Options](#uselinkedrecords----fetch-linkedrelated-options)
- [useFieldOptions -- Fetch Single/Multi-Select Choices](#usefieldoptions----fetch-singlemulti-select-choices)
- [Filtering](#filtering)
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

## useRecords -- Fetch a Paginated List

```jsx
import { useRecords, q } from "@/lib/datasource";

var result = useRecords({
  select: q.select({ name: "FIELD_ID1", email: "FIELD_ID2" }),
  count: 6,           // records per page (default 6, max 100)
  where: q.text("name").contains("Alice"),  // optional filter
  orderBy: q.desc("createdAt"),             // optional sort
  enabled: true,                            // optional, defer loading
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

A block can connect to **several data sources** and call `useRecords` once per source — declare them with `datasource.define()` and pass `from:` on every hook. See [multi-datasource.md](multi-datasource.md). (This replaces the old one-table-per-block limit; blocks no longer need an invisible helper block just to read a second table.)

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

var recordId = useCurrentRecordId(); // resolves from URL context, can be null
var result = useRecord({
  select: q.select({ title: "FIELD_ID1", description: "FIELD_ID2" }),
  recordId: recordId,
});
```

**`recordId` can be omitted when Softr Studio supplies the record context.** `useRecord({ select })` with no `recordId` loads the record the block is bound to via its data-source binding in Studio — verified by deployed block, July 2026 (an Airtable-backed stats block rendered live values this way). Keep `useCurrentRecordId()` + explicit `recordId` as the pattern for URL-driven detail pages (`/page?recordId=...`). When editing an existing **working** block that already omits `recordId`, leave the call shape as-is: adding an explicit `recordId` from `useCurrentRecordId()` can change behavior on pages whose URL carries no `recordId` param. Corollary for reviews: a recordId-less `useRecord` is NOT by itself a defect — check whether the block is deployed and loading data before flagging it.

## useLinkedRecords -- Fetch Linked/Related Options

```jsx
import { q, useLinkedRecords } from "@/lib/datasource";

var result = useLinkedRecords({
  select: q.select({ category: "$CATEGORY_FIELD_ID" }),
  field: "category",    // the ALIAS from q.select(), NOT the raw field ID
  sortOrder: "ASC",     // "ASC" | "DESC"
  search: "",           // optional search string
  enabled: true,        // defer loading until needed
  count: 50,
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
//   id    — the option's UUID, used in mutate payloads
//   label — display string
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

- **Use `useFieldOptions`** when option IDs / labels could change post-deploy — selects with rapidly-evolving lists, user-editable choices, or any case where re-pasting blocks for an option rename is annoying. Cross-table case: to render a select field from table B inside a block bound to table A (e.g. an intake form bound to Jobs that needs the Wigs `Color` options), put the `useRecords` + `useFieldOptions` in a hidden helper block bound to table B and publish the options to a `window` global (see [helper-blocks.md](../references/helper-blocks.md)).
- **Hardcode** when the option set is stable and frequently referenced (e.g. a status enum that drives a state machine), so the IDs live in source and rename-safety is enforced by greppable constants. A robust middle ground: prefer the live options, fall back to a hardcoded list per field so the UI still renders if the helper hasn't published yet.

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
```

**For user groups, role, or custom fields** -- use `window.__softr_current_user` (NOT `useCurrentUser()`):

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

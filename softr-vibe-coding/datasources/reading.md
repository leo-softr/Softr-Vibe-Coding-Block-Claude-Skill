# Reading Data

Fetching, filtering, sorting, pagination, metrics, charts, and current user.

## Table of Contents

- [Query Builder](#query-builder)
- [useRecords -- Fetch a Paginated List](#userecords----fetch-a-paginated-list)
- [useRecord -- Fetch a Single Record](#userecord----fetch-a-single-record)
- [useLinkedRecords -- Fetch Linked/Related Options](#uselinkedrecords----fetch-linkedrelated-options)
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

**CRITICAL:** Only ONE `useRecords` call per block. Fetch all data in one call and filter client-side. Multiple `useMetric` calls ARE allowed.

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

Grouping buckets: `metric.bucket.year`, `metric.bucket.month.iso`, `metric.bucket.month.long`, `metric.bucket.day.iso`, `metric.bucket.day.long`

Use **recharts** with shadcn's chart wrapper:

```jsx
import { LineChart, Line, XAxis, CartesianGrid } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
```

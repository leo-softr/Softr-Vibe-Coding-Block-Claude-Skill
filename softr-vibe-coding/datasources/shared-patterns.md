# Shared Vibe Coding Patterns

These patterns apply to all data sources that use `useRecords` + `q.select()` (everything except REST API). For REST API, see [rest-api.md](rest-api.md).

## Table of Contents

- [Query Builder](#query-builder)
- [useRecords — Fetch a Paginated List](#userecords----fetch-a-paginated-list)
- [useRecord — Fetch a Single Record](#userecord----fetch-a-single-record)
- [useLinkedRecords — Fetch Linked/Related Options](#uselinkedrecords----fetch-linkedrelated-options)
- [Filtering](#filtering)
- [Sorting](#sorting)
- [Record Mutations](#record-mutations) (useRecordCreate, useRecordUpdate, useRecordDelete)
- [File Uploads](#file-uploads)
- [Field Type Handling](#field-type-handling)
- [Current User](#current-user)
- [Metrics](#metrics)
- [Chart Data](#chart-data)
- [Cross-Table Operations](#cross-table-operations)
- [Debug Utilities](#debug-utilities) (Field Inspector, API Inspector, User Inspector)

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

## Field Type Handling

**Every field value rendered in JSX must pass through `getFieldValue()`** before rendering, parsing, or comparing. Softr returns many field types as `{label, ...}` objects, not strings. Rendering them raw crashes React with error #31 ("Objects are not valid as a React child"). The cost of unnecessary `getFieldValue()` calls is zero; the cost of debugging error #31 is 30 minutes.

```jsx
var getFieldValue = function(f) {
  if (f == null) return "";
  if (Array.isArray(f)) {
    return f.map(function(x) {
      if (x && typeof x === "object") return x.label || x.name || x.title || "";
      return String(x);
    }).filter(Boolean).join(", ");
  }
  if (typeof f === "object") return f.label || f.name || f.title || "";
  return String(f);
};
```

Property priority: `label` first (most common in Softr formatted fields), then `name`, then `title`.

Apply `getFieldValue()` everywhere you read fields:
- Table cells, badges, tooltips: `<td>{getFieldValue(f.subject)}</td>`
- Date parsing: `new Date(getFieldValue(f.dueDate))` -- raw value might be `{label: "2025-12-01"}`
- Number parsing: `parseInt(getFieldValue(f.count), 10)` -- formula numbers come back as objects
- String methods: `getFieldValue(f.status).toLowerCase()`
- Inside `useMemo` normalizers, BEFORE storing into state -- prevents the object from propagating

### Debugging error #31

If React crashes with error #31 ("Objects are not valid as a React child"), open console on the first record that crashes and run:

```js
JSON.stringify(record.fields, null, 2).slice(0, 1000)
```

You'll see exactly which field is an object. Add `getFieldValue()` around it.

For companion helpers (`getLinkedNames`, `getLinkedItems`) used in helper block consumers, see [../references/helper-blocks.md](../references/helper-blocks.md).

### Common Field Type Shapes

| Field type | Value shape |
|---|---|
| Text, Email, URL, Phone, Address | `string` |
| Number, Currency, Percent, Progress, Autonumber | `number or null` |
| Checkbox | `string or boolean` |
| Date, DateTime, Time, Created At, Updated At | `string` (ISO) |
| Date Range | `{ from: string, to: string }` |
| Rating, Duration | `string or number or null` |
| Select | `{ label: string, id: string }` |
| Linked Record (via useRecord/useRecords) | `{ label: string, id: string }` |
| Linked Record (via useLinkedRecords) | `{ id: string, title: string }` -- different! |
| User, Created By, Updated By | `{ avatarUrl, id, name, email }` |
| Attachment | `{ filename, id, type, url }` |
| Formula | `string or number` |

### Record Structure

Records returned by `useRecords` have: `{ id: "recXXX", fields: { alias1: value, alias2: value } }`. Keys inside `fields` are the **aliases from `q.select()`**, NOT the original field names.

```jsx
var rawRecord = items && items[0];
var f = rawRecord ? rawRecord.fields || {} : {};
var name = f.firstName || "";
```

### Linked Record Format for Mutations

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

## Debug Utilities

### Field Inspector Block

Paste this into a Vibe Coding block to see raw field structure from any `useRecords`-compatible data source:

```jsx
import { useRecords, q } from "@/lib/datasource";
var select = q.select({});
export default function Block() {
  var result = useRecords({ select: select, count: 3 });
  if (result.status === "pending") return <div className="container py-6"><div className="content"><p>Loading...</p></div></div>;
  var records = (result.data && result.data.pages) ? result.data.pages.flatMap(function(p) { return p.items; }) : [];
  return (
    <div className="container py-6">
      <div className="content">
        <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
          {JSON.stringify(records.slice(0, 2), null, 2)}
        </pre>
      </div>
    </div>
  );
}
```

### API Response Inspector Block

For REST API data sources, use `useProxyFetch` instead (see [rest-api.md](rest-api.md)):

```jsx
import { useProxyFetch } from "@/lib/datasource";
import { useQuery } from "@tanstack/react-query";
export default function Block() {
  var proxyFetch = useProxyFetch();
  var result = useQuery({
    queryKey: ["api-inspect"],
    queryFn: function() {
      return proxyFetch("YOUR_FULL_API_URL_HERE")
        .then(function(res) { return res.json(); });
    },
  });
  if (result.status === "pending") return <div className="container py-6"><div className="content"><p>Loading...</p></div></div>;
  if (result.status === "error") return <div className="container py-6"><div className="content"><p className="text-red-500">Error: {result.error && result.error.message}</p></div></div>;
  return (
    <div className="container py-6">
      <div className="content">
        <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", wordBreak: "break-all", background: "#f9fafb", padding: 16, borderRadius: 8 }}>
          {JSON.stringify(result.data, null, 2)}
        </pre>
      </div>
    </div>
  );
}
```

### User Inspector Block

```jsx
import { useCurrentUser } from "@/lib/user";
export default function Block() {
  var currentUser = useCurrentUser();
  var softrUser = window.__softr_current_user || {};
  return (
    <div className="container py-6">
      <div className="content">
        <h3>useCurrentUser():</h3>
        <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
          {JSON.stringify(currentUser, null, 2)}
        </pre>
        <h3 style={{ marginTop: 16 }}>window.__softr_current_user:</h3>
        <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
          {JSON.stringify(softrUser, null, 2)}
        </pre>
      </div>
    </div>
  );
}
```

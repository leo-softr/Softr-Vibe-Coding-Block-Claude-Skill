# Field Types & Debug Utilities

The `getFieldValue()` helper, field type shapes, record structure, and diagnostic blocks.

## Table of Contents

- [getFieldValue -- Never Render Raw Fields](#getfieldvalue----never-render-raw-fields)
- [Debugging Error #31](#debugging-error-31)
- [Common Field Type Shapes](#common-field-type-shapes)
- [Record Structure](#record-structure)
- [Debug Utilities](#debug-utilities)

## getFieldValue -- Never Render Raw Fields

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

For companion helpers (`getLinkedNames`, `getLinkedItems`) used in helper block consumers, see [../references/helper-blocks.md](../references/helper-blocks.md).

## Debugging Error #31

If React crashes with error #31 ("Objects are not valid as a React child"), open console on the first record that crashes and run:

```js
JSON.stringify(record.fields, null, 2).slice(0, 1000)
```

You'll see exactly which field is an object. Add `getFieldValue()` around it.

## Common Field Type Shapes

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

## Record Structure

Records returned by `useRecords` have: `{ id: "recXXX", fields: { alias1: value, alias2: value } }`. Keys inside `fields` are the **aliases from `q.select()`**, NOT the original field names.

```jsx
var rawRecord = items && items[0];
var f = rawRecord ? rawRecord.fields || {} : {};
var name = f.firstName || "";
```

## Debug Utilities

Two throwaway diagnostic blocks you can drop into a page to diagnose data problems. Neither is meant for production -- delete or hide them once the issue is resolved. During development, drop them on a `/debug` page that's only visible to admins, or on a hidden page you navigate to manually.

### Field Inspector Block

Use when records load but all fields come back empty, or when you're not sure which Field IDs exist on a Softr Database table. Dumps the first 2 raw records as JSON so you can see exactly what the datasource is returning and build the real `q.select()` mapping with confidence.

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

Use when debugging permissions, user groups, or the `useCurrentUser()` vs `window.__softr_current_user` distinction. Renders both side-by-side as JSON. This catches a common surprise: `userGroups` only lives on the `window.__softr_current_user` object, not on `useCurrentUser()`.

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

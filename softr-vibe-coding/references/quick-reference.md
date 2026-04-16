# Quick Reference

Fast lookup for imports, hook signatures, field mapping syntax, and common patterns. Use when you already know what you need and just want the shape.

## Imports

```jsx
// DATASOURCE
import { useRecords, useRecord, useRecordCreate, useRecordUpdate, useRecordDelete,
         useCurrentRecordId, useLinkedRecords, useUpload, useMetric, useChartData,
         q, metric } from "@/lib/datasource";

// USER
import { useCurrentUser } from "@/lib/user";

// EDITABLE SETTINGS
import { useTextSetting, useImageSetting, useVideoSetting, useArraySetting,
         useVibeCodingBlockIconSetting, useNavigationSetting,
         useBooleanSetting } from "@/lib/editable-settings";

// REACT
import { useState, useEffect, useMemo, useCallback, useRef } from "react";

// UI
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Target } from "lucide-react";
import { DynamicIcon } from "@/components/dynamic-icon";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
```

## Field Mapping (static, outside component)

```jsx
var select = q.select({ alias: "FIELD_ID" });
var updateFields = q.select({ alias: "FIELD_ID" });  // writable only
var createFields = q.select({ alias: "FIELD_ID" });  // writable only
```

## Read

```jsx
var result = useRecords({ select: select, count: 100 });
var records = (result.data && result.data.pages) ? result.data.pages.flatMap(function(p) { return p.items; }) : [];
```

## Filter + Sort

```jsx
useRecords({
  select: select, count: 100,
  where: q.and(q.text("status").is("Active"), q.date("due").lte("2025-12-31")),
  orderBy: q.desc("createdAt"),
});
```

## Single Record (detail pages)

```jsx
var recordId = useCurrentRecordId();
var result = useRecord({ recordId: recordId, select: select });
```

## Current User

```jsx
var currentUser = useCurrentUser();          // { id, fullName, email, avatar }
var softrUser = window.__softr_current_user; // full object with userGroups
```

## Create

```jsx
var createRecord = useRecordCreate({
  fields: createFields,
  onSuccess: function(newRecord) { refetch(); },
  onError: function(err) { toast.error(err.message); },
});
createRecord.mutate({ name: "Jane", email: "jane@example.com" });
```

## Update (THE CORRECT PATTERN)

```jsx
var updateRecord = useRecordUpdate({
  fields: updateFields,
  onSuccess: function(updatedRecord) { refetch(); },
  onError: function(err) { toast.error(err.message); },
});
updateRecord.mutate({ recordId: record.id, fields: { name: "New" } });
```

## Delete

```jsx
var deleteRecord = useRecordDelete({
  onSuccess: function(result) { refetch(); },
});
deleteRecord.mutate(record.id);  // Just the ID string
```

## Mutation Hook Properties (all hooks)

`.enabled`, `.status`, `.error`, `.mutate()`, `.mutateAsync()`, `.reset()`

## Linked Records Picker

```jsx
// field = alias from select, NOT raw field ID
var result = useLinkedRecords({ select: select, field: "aliasName", count: 100 });
var options = (result.data && result.data.pages) ? result.data.pages.flatMap(function(p) { return p.items; }) : [];
// items shaped as { id, title } -- use opt.title NOT opt.label
```

## Linked Records in Mutations

```jsx
teamMembers: [{ id: "MEMBER_ID" }]
```

## Formula Booleans

```jsx
item.fields.isOverdue === "1"  // true
item.fields.isOverdue === "0"  // false
```

## Metrics

```jsx
var result1 = useMetric({ select: select, metric: metric.sum("revenue") });
var result2 = useMetric({ select: select, metric: metric.count() });
```

## Editable Settings

```jsx
var title = useTextSetting({ name: "title", label: "Title", initialValue: "Hello" });
var show = useBooleanSetting({ name: "toggle", label: "Show header", initialValue: false });
```

## Field Value Helper (getFieldValue)

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

Wrap every field value in `getFieldValue()` before rendering, parsing, or comparing.

## Pagination Auto-Fetch

```jsx
useEffect(function() {
  if (result.hasNextPage && !result.isFetchingNextPage && result.status === "success") {
    result.fetchNextPage();
  }
}, [result.hasNextPage, result.isFetchingNextPage, result.status, result.fetchNextPage]);
```

## Component Skeleton

```jsx
export default function Block() {
  var result = useRecords({ select: select, count: 25 });

  if (result.status === "pending") return <div className="container py-6"><div className="content">Loading...</div></div>;
  if (result.status === "error") return <div className="container py-6"><div className="content">Error</div></div>;

  var records = (result.data && result.data.pages) ? result.data.pages.flatMap(function(p) { return p.items; }) : [];

  return (
    <div className="container py-6">
      <div className="content">
        {/* UI */}
      </div>
    </div>
  );
}
```

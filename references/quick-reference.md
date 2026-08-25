# Quick Reference

Fast lookup for imports, hook signatures, field mapping syntax, and common patterns. Use when you already know what you need and just want the shape.

The current platform compiles TypeScript with modern syntax (`?.`, `??`, arrows, `const`, generics) — verified live 2026-08-25. Snippets below in `var` style predate that and remain valid; both styles compile.

## Imports

```jsx
// DATASOURCE  (add `datasource` when the block connects to more than one source)
import { datasource, useRecords, useRecord, useRecordCreate, useRecordUpdate, useRecordDelete,
         useCurrentRecordId, useLinkedRecords, useFieldOptions, useUpload, useMetric, useChartData,
         q, metric } from "@/lib/datasource";

// USER
import { useCurrentUser } from "@/lib/user";

// EDITABLE SETTINGS
import { useTextSetting, useImageSetting, useVideoSetting, useArraySetting,
         useVibeCodingBlockIconSetting, useNavigationSetting,
         useBooleanSetting } from "@/lib/editable-settings";

// NAVIGATION GUARD (form unsaved-changes warning that also works on Softr's SPA nav)
import { useNavigationBlocker } from "@/lib/use-navigation-blocker";

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

## Multiple datasources (static, outside component)

```jsx
var ds = datasource.define({           // values MUST be inline string literals
  people: "74d2cbfd-f2cb-4f5c-82d9-0d3a0651e531",
  shifts: "ec7a6311-f6c3-4c99-881d-aae308148716",
});

useRecords({ from: ds.people, select: select });   // `from:` required once >1 source
var proxyFetch = useProxyFetch(ds.people);         // REST API source: alias is the ARGUMENT, not a from: option
```

Ids are plain UUIDs. Get them by asking Studio's AI chat to **write code**, never to recite a
value — it fabricates them in prose. Full detail: [../datasources/multi-datasource.md](../datasources/multi-datasource.md).

## Read

```jsx
var result = useRecords({ select: select, count: 100 });
var records = result.data?.pages.flatMap(p => p.items) ?? [];
```

⚠ The options object MUST be an inline literal — `useRecords(opts)` with `opts` built in a
variable or returned by a wrapper function **fails to compile** (verified live 2026-08-25).
Share `q.select` mappings, not options objects.

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

`recordId` may be omitted when the block's Studio data binding supplies the record context (verified by deployed block, July 2026) — see [reading.md](../datasources/reading.md#userecord----fetch-a-single-record).

## Current User

```jsx
var currentUser = useCurrentUser();          // { id, fullName, firstName, lastName, email, avatar } | null; id only with user sync
var withProps = useCurrentUser({ properties: { plan: "FIELD_ID" } });  // custom user fields → withProps.properties.plan
var softrUser = window.__softr_current_user; // userGroups/role ONLY — not exposed by the hook
```

## Create

```jsx
var createRecord = useRecordCreate({
  fields: createFields,
  onSuccess: function(newRecord) { refetch(); },
  onError: function(err) { toast.error(err.message); },
});
createRecord.mutate({ name: "Jane", email: "jane@example.com" });   // FLAT — no { fields } wrapper
```

## Update (THE CORRECT PATTERN)

```jsx
var updateRecord = useRecordUpdate({
  fields: updateFields,
  onSuccess: function(updatedRecord) { refetch(); },
  onError: function(err) { toast.error(err.message); },
});

// Payload is the nested {recordId, fields:{}} shape (create is flat — the asymmetry is by design).
// Per-call onSuccess/onError go in the second argument.
updateRecord.mutate(
  { recordId: record.id, fields: { name: "New" } },
  {
    onSuccess: function() { toast.success("Saved"); },
    onError: function(err) { toast.error(err.message); },
  }
);
```

**Payload shapes or `enabled` stays `false`:**
1. Update payload is `{ recordId, fields: {...} }` — NOT flat `{ recordId, status: "..." }`
2. Create payload is FLAT — `{ name: "..." }`, no `fields` wrapper

See [datasources/writing.md](../datasources/writing.md#critical-the-userecordupdate-payload-shape-and-the-retired-mutate-only-rule) for the full debugging path.

## Sequential Multi-Row Saves (mutateAsync)

`mutateAsync` is fully supported (verified live 2026-08-25 — the old ".mutate() only" parser
rule is retired). It's the tool whenever writes must happen in order:

```tsx
const header = await createHeader.mutateAsync({ name, date });      // header first
for (const line of lines) {
  await createLine.mutateAsync({ header: [header.id], ...line });   // then lines, in order
}
```

Stop on the first failure, render it with a Retry, never re-issue completed writes. Full queue
pattern: [datasources/writing.md](../datasources/writing.md#sequential-multi-row-writes-mutateasync).

## Delete

```jsx
var deleteRecord = useRecordDelete({
  onSuccess: function(result) { refetch(); },
});
deleteRecord.mutate(record.id);  // Just the ID string
```

## Mutation Hook Properties (all hooks)

`.enabled`, `.status`, `.error`, `.mutate()`, `.mutateAsync()`, `.reset()`

Both `.mutate(payload, { onSuccess, onError })` and `await .mutateAsync(payload)` derive
Actions correctly on the current platform (verified 2026-08-25). Use `.mutate` for
fire-and-forget single writes, `mutateAsync` for sequenced flows. (Pre-2026-08 platforms only
recognized the literal `.mutate(` token — relevant only when maintaining old apps.)

## Linked Records Picker

```jsx
// field = alias from select, NOT raw field ID
var result = useLinkedRecords({ select: select, field: "aliasName", count: 100 });
var options = (result.data && result.data.pages) ? result.data.pages.flatMap(function(p) { return p.items; }) : [];
// items shaped as { id, title } -- use opt.title NOT opt.label
```

## Linked Records in Mutations

```jsx
teamMembers: ["MEMBER_ID_1", "MEMBER_ID_2"]   // array of record-id STRINGS (verified Softr DB, 2026-08-25)
```

Legacy/Airtable: the `[{ id: "..." }]` object shape was the verified form on Airtable-backed
blocks (May 2026) — try it if a string-array write fails there.

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

## Navigation Blocker (unsaved-changes warning)

```jsx
// Boolean form: simplest case
useNavigationBlocker(isDirty);

// Callback form: reads from a ref without re-running on every render
useNavigationBlocker(function() { return dirtyRef.current; });
```

Catches BOTH Softr's in-app SPA navigation (nav bar, sidebar, `<NavigationAction>`) AND browser unload (tab close, refresh, external links). A plain `window.addEventListener("beforeunload", ...)` does NOT catch Softr's in-app nav. See [common-patterns.md](common-patterns.md#navigation-blocker-for-unsaved-changes).

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

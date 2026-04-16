# Helper Blocks & Cross-Block Patterns

Cross-block communication via `window` globals, the invisible helper block pattern for multi-table access, breadcrumb navigation, and advanced production-hardened patterns.

## Table of Contents

- [When You Need Helper Blocks](#when-you-need-helper-blocks)
- [Companion Field Helpers](#companion-field-helpers)
- [Breadcrumb / Back Navigation](#breadcrumb--back-navigation)
- [Multi-Table Access via Invisible Helper Blocks](#multi-table-access-via-invisible-helper-blocks)
- [Publisher Template](#publisher-template)
- [Consumer Pattern](#consumer-pattern)
- [useWindowData Custom Hook](#usewindowdata-custom-hook)
- [Advanced Patterns](#advanced-patterns)
- [Anti-Patterns](#anti-patterns)

## When You Need Helper Blocks

A Vibe Coding block can only connect to **one source table**. When your main block needs data from a second table (e.g., a task detail block that also needs the Users table for a team picker), you cannot add another `useRecords` for a different table.

**Solution:** Drop an invisible helper block on the same Softr page, connected to the second table. It fetches records, publishes them to a `window` global, and dispatches a custom event. The main block reads the global and listens for updates. The helper returns `null` so it renders nothing in the published app.

`useLinkedRecords` always returns `{id, title}` only and silently ignores extra fields in `select`. This is the core reason the helper block pattern exists. If your task involves showing status, due dates, or any non-title field from a linked table, skip `useLinkedRecords` entirely and build a helper -- there is no other way to get those fields.

Key rules:
- The helper block must be on the **same Softr page** as the consumer -- `window` is page-scoped, globals don't cross pages.
- **One helper block per foreign table.** Multiple helpers with distinct namespaces coexist fine on the same page.
- **Read-only pattern.** Helpers expose foreign table data for lookups, pickers, and display only. Writes still happen from the main block via its own `useRecordUpdate` / `useRecordCreate`. If the main block needs to write to the helper's table, use a webhook or the Softr Database REST API (see [shared-patterns.md Cross-Table Operations](../datasources/shared-patterns.md#cross-table-operations)), not the helper.

## Companion Field Helpers

The main `getFieldValue()` function lives in [shared-patterns.md](../datasources/shared-patterns.md). These companion helpers handle specific shapes needed for helper block consumers:

```jsx
/* For multi-value linked records / multi-selects when you need an array */
function getLinkedNames(f) {
  if (f == null) return [];
  if (Array.isArray(f)) return f.map(function(x) {
    return (x && typeof x === "object") ? (x.label || x.name || x.title || "") : String(x);
  }).filter(Boolean);
  if (typeof f === "object") {
    var v = f.label || f.name || f.title || "";
    return v ? [v] : [];
  }
  return [String(f)];
}

/* When you need {id, title} pairs for filtering by ID */
function getLinkedItems(f) {
  if (f == null) return [];
  if (Array.isArray(f)) return f.map(function(x) {
    if (x && typeof x === "object") return { id: x.id || "", title: x.label || x.name || x.title || "" };
    return { id: "", title: String(x) };
  }).filter(function(o) { return o.id || o.title; });
  return [];
}
```

## Breadcrumb / Back Navigation

For detail pages with a "back" button that returns to the listing:

```jsx
import { ArrowLeft, ChevronRight } from "lucide-react";

var BRAND_PRIMARY = "#386AF5";

<div className="flex items-center gap-2 mb-4">
  <button
    className="flex items-center gap-1 text-xs"
    style={{ color: "#595959" }}
    onClick={function() {
      if (window.history.length > 1) {
        setTimeout(function() { window.history.back(); }, 0);
      } else {
        window.location.href = "/listing-page";
      }
    }}
  >
    <ArrowLeft className="h-3.5 w-3.5" />
    Back
  </button>
  {parentName && (
    <>
      <ChevronRight className="h-3 w-3" style={{ color: "#E6E6E6" }} />
      <span className="text-xs" style={{ color: "#595959" }}>{parentName}</span>
    </>
  )}
  <ChevronRight className="h-3 w-3" style={{ color: "#E6E6E6" }} />
  <span className="text-xs font-medium" style={{ color: BRAND_PRIMARY }}>{currentItemName}</span>
</div>
```

Key points:
- `window.history.back()` uses the browser's native History API -- no routing library needed.
- The `window.history.length > 1` check is the fallback for users who land directly via shared URL (no history). Send them to a sensible default like the listing page.
- Wrap in `setTimeout(fn, 0)` to break out of Softr's event cycle (same as scroll commands).
- Use alongside `useNavigationSetting` when you also need a Studio-configurable destination -- they solve different problems (contextual back vs. fixed CTA).
- Works in any Vibe Coding block without extra dependencies.

## Multi-Table Access via Invisible Helper Blocks

### Naming Conventions

- Namespace: `window.__<app>_<resource>` -- e.g., `window.__myapp_team`, `window.__myapp_campaigns`
- Ready flag: `window.__<app>_<resource>_ready` (boolean) -- consumers check before reading
- Progress event: `<app>_<resource>_progress` -- dispatched on every paginated update
- Ready event: `<app>_<resource>_ready` -- dispatched once when all pages are loaded

### Publisher Template (the invisible helper block)

```jsx
import { useRecords, q } from "@/lib/datasource";
import { useEffect, useMemo, useRef } from "react";

var select = q.select({ fullName: "fldXXX", isActive: "fldYYY" });

function toOption(record) {
  return { id: record.id, title: record.fields.fullName || "" };
}

export default function Block() {
  var result = useRecords({ select: select, count: 100 });

  /* Auto-fetch all pages -- MUST be inside useEffect */
  useEffect(function() {
    if (result.hasNextPage && !result.isFetchingNextPage && result.status === "success") {
      result.fetchNextPage();
    }
  }, [result.hasNextPage, result.isFetchingNextPage, result.status, result.fetchNextPage]);

  var publishedPageCount = useRef(0);

  var allRecords = useMemo(function() {
    if (!result.data) return [];
    return result.data.pages.flatMap(function(p) { return p.items; });
  }, [result.data]);

  var pageCount = result.data ? result.data.pages.length : 0;

  /* Progressive publish -- push to window every time a new page arrives.
     Critical when the source table has hundreds of records: the consumer
     can render the first 100 options while later pages stream in. */
  useEffect(function() {
    if (result.status !== "success") return;
    if (pageCount <= publishedPageCount.current) return;

    var options = allRecords
      .filter(function(r) { return r.fields.isActive; })
      .map(toOption)
      .filter(function(o) { return o.title; })
      .sort(function(a, b) { return a.title.localeCompare(b.title); });

    window.__myapp_users = options;
    window.__myapp_users_ready = true;

    window.dispatchEvent(new CustomEvent("myapp_users_progress", {
      detail: { count: options.length, complete: !result.hasNextPage },
    }));

    if (!result.hasNextPage) {
      window.dispatchEvent(new CustomEvent("myapp_users_ready", {
        detail: { count: options.length },
      }));
    }

    publishedPageCount.current = pageCount;
  }, [allRecords, pageCount, result.status, result.hasNextPage]);

  return null; /* invisible in published app */
}
```

### Consumer Pattern (inside the main block)

```jsx
var [teamOptions, setTeamOptions] = useState([]);

useEffect(function() {
  function readFromWindow() {
    if (window.__myapp_users_ready && window.__myapp_users) {
      setTeamOptions(window.__myapp_users);
    }
  }

  /* Read immediately if helper already published */
  readFromWindow();

  /* Poll briefly in case helper hasn't mounted yet */
  var interval = setInterval(function() {
    if (window.__myapp_users_ready) {
      readFromWindow();
      clearInterval(interval);
    }
  }, 200);

  /* Listen for progressive updates */
  function onUpdate() { readFromWindow(); }
  window.addEventListener("myapp_users_progress", onUpdate);

  return function() {
    clearInterval(interval);
    window.removeEventListener("myapp_users_progress", onUpdate);
  };
}, []);
```

### useWindowData Custom Hook (cleaner consumer)

Wrap the listener + polling boilerplate in a reusable hook:

```jsx
function useWindowData() {
  var [tick, setTick] = useState(0);
  useEffect(function() {
    function bump() { setTick(function(t) { return t + 1; }); }
    window.addEventListener("myapp_projects_ready", bump);
    window.addEventListener("myapp_projects_progress", bump);
    var poll = setInterval(bump, 1500);
    return function() {
      window.removeEventListener("myapp_projects_ready", bump);
      window.removeEventListener("myapp_projects_progress", bump);
      clearInterval(poll);
    };
  }, []);
  return {
    projects: window.__myapp_projects_all || [],
    options: window.__myapp_projects_filter_options || null,
    ready: window.__myapp_projects_ready === true,
    tick: tick,
  };
}
```

The `tick` state forces re-renders on every event/poll, so consumers naturally pick up new data without managing local state of the globals.

## Advanced Patterns

These patterns were hardened in production on real features where the main block needed filtered, enriched data across multiple dimensions with live preview. Apply them whenever a helper serves more than a simple picker.

### Publishing Rich Filter Options

When the consumer needs dynamic filter UIs, have the helper compute options inside its `useMemo` and publish as a separate global:

- `window.__myapp_projects_all` -- raw records
- `window.__myapp_projects_filter_options` -- computed `{ workType: [...], industries: [...], dateRange: { min, max } }`

This avoids recomputing options in every consumer.

### Visible Dev Badge (instead of `return null`)

During development, render a minimal badge to see loading status at a glance:

```jsx
return (
  <div style={{
    display: "flex", alignItems: "center", gap: "8px",
    padding: "8px", fontSize: "12px", color: "#64748b",
  }}>
    Helper: {allRecords.length} loaded {result.hasNextPage ? "..." : "done"}
  </div>
);
```

Switch to `return null` only after the feature is stable in production.

### Two CustomEvents: `_progress` + `_ready`

Dispatch `_progress` on every paginated update AND `_ready` once when all pages are loaded. Consumers that need progressive data listen to both; consumers that need complete data listen only to `_ready`.

The `detail.complete` flag in `_progress` events lets consumers show a loading indicator while pages are still streaming, then switch to a final state when `complete === true`.

### Block Ordering Matters

If helper B depends on helper A's globals, helper A MUST be placed **above** helper B in Softr's page block order. Softr renders blocks top-to-bottom. A lower-ordered helper B will mount with A's globals still `undefined`, then catch up -- but this causes initial empty-state flashes.

Document the dependency at the top of helper B:

```jsx
/* Depends on: window.__myapp_accounts_ready */
```

### Shape Stability Is a Contract

When you change a helper's output shape (e.g., `advisorOffice` from array to string), ALL downstream consumers break silently. Two options:

1. Document the published shape as a comment at the top of the helper file and update all consumers in the same commit.
2. Version the namespace (`__myapp_projects_v2`) -- old consumers keep reading v1 until migrated.

Defensive consumers can use `Array.isArray(x) ? x.map(...) : x` when shape might vary, but don't lean on this -- it hides bugs.

### useState, Not useRef, for IDs Consumed by useMemo

IDs consumed by `useMemo` must live in `useState`. `useRef` mutations don't trigger re-renders, so `useMemo` never recomputes when the ID resolves asynchronously. This produces the confusing symptom of "data loads, but only after a manual refresh."

```jsx
/* CORRECT */
var [currentTeamMemberId, setCurrentTeamMemberId] = useState(null);

var filteredViews = useMemo(function() {
  if (!currentTeamMemberId) return [];
  return allViews.filter(function(v) { return v.createdBy === currentTeamMemberId; });
}, [allViews, currentTeamMemberId]);

/* WRONG -- useRef changes don't trigger useMemo recomputation */
var currentTeamMemberId = useRef(null);
```

### Saved Views Architecture (Two-Block Pattern)

For per-user saved filter views on a list page:

1. A hidden **Team Member Resolver** helper that maps `window.__softr_current_user.email` to a Team Member record ID (via `useRecords` + filter on email field).
2. A `viewScope` field on the SavedViews table to scope views per page (e.g., `"pursuits"`, `"client-work"`, `"my-projects"`).
3. The main list block reads the current Team Member ID from the resolver global and filters SavedViews where `createdBy === currentTeamMemberId AND viewScope === pageScope`.

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Helper block returning `null` during dev | Return a minimal visible badge until feature stable |
| Single CustomEvent on full load | Dispatch `_progress` per page AND `_ready` on completion |
| Helper publishes only raw records | Also publish computed `filterOptions` as separate globals |
| Refactoring helper shape without updating consumers | Version namespace OR update all consumers in same commit |
| Helper B placed above A when B depends on A | A must be above B -- Softr renders top-to-bottom |
| `useRef` for IDs consumed by `useMemo` | Use `useState` -- ref mutations don't trigger recomputation |
| Using `useLinkedRecords` for rich foreign data | It only returns `{id, title}` -- use a helper block instead |

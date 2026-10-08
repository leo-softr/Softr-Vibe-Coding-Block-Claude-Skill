# Reading Data

Fetching, filtering, sorting, pagination, metrics, charts, and current user.

## Table of Contents

- [Query Builder](#query-builder)
- [useRecords -- Fetch a Paginated List](#userecords----fetch-a-paginated-list) — incl. [`enabled: false` is ignored](#userecords-ignores-enabled-false)
- [useRecord -- Fetch a Single Record](#userecord----fetch-a-single-record) — the detail-page pattern; no auto-scoping
- [useLinkedRecords -- Fetch Linked/Related Options](#uselinkedrecords----fetch-linkedrelated-options)
- [useFieldOptions -- Fetch Single/Multi-Select Choices](#usefieldoptions----fetch-singlemulti-select-choices)
- [Filtering](#filtering) — incl. [operator semantics on the server](#operator-semantics-on-the-server), [filters fail open](#filters-fail-open), [server-side linked-record filters](#filtering-by-a-linked-record-server-side)
- [Sorting](#sorting)
- [Current User](#current-user) — user groups need a short, bounded poll
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

**Two behaviours that look like bugs** (measured with reads aborted, LCDB QA pass, 2026-10-08):

- **The hooks refetch when the window regains focus,** so `isRefetching` turns true with no click. A busy label driven by it flickers each time the user comes back to the tab; drive busy labels from the click.
- **A failed read is retried about three times before `status` turns `"error"`.** The error shows 6 to 20 seconds after the failure starts (7 to 13 seconds in most checks), and the block shows loading until then. A check that waits 3 to 5 seconds sees "Loading", not the error state.

**House rule: one `useRecords` per connection.** It is not a documented platform limit — Hard Constraint 13 in SKILL.md says when to filter client-side, when to add a connection, and when a server-side `where` is the better choice. Multiple `useMetric` calls ARE allowed.

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
not probed — don't assume either behaviour for them.) The official developer guide still
describes `enabled` on `useRecords` as an "optional boolean to defer loading" (checked
2026-10-06); the capture says otherwise, so trust it until a newer one does not.

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
  // `!result.error` is defensive: never re-request a page while the hook reports an error
  // (how a failed later page surfaces has not been verified).
  if (result.hasNextPage && !result.isFetchingNextPage && result.status === "success" && !result.error) {
    result.fetchNextPage();
  }
}, [result.hasNextPage, result.isFetchingNextPage, result.status, result.error, result.fetchNextPage]);
```

**A total, count or export built from a paginated list waits until every page has loaded** (`hasNextPage` false) and no read is in error. Until then it shows loading, never a number from the pages so far: a summary line read "0 children" while the children read was still on its first page or had failed, and a history list was capped instead of paged. [Printing](../references/printing.md#4-the-print-button-waits-for-the-data) applies the same rule to Print.

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

**A record the connection's Source conditions exclude comes back as no record, not as an error**
(verified live 2026-09-18, Softr Database). The by-id request answers HTTP 200 with an empty
body, not 403 or 404, so `useRecord` reports no error and holds no record. Render that as "not
found"; never wait for a 403/404 to learn the viewer was refused. A production block also sends
any denial-shaped error (401/403/404, or a JSON parse error on an empty body) to the same "not
found" state, in case a later build answers differently, and keeps the error panel with a retry
for real failures.

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
  enabled: true,        // documented as deferral; not verified live (see the useRecords note)
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
//   id    — stable option id (use as a React key; NOT needed in mutate payloads on Softr
//           Database — SELECT fields write by LABEL string there, verified 2026-08-25.
//           HubSpot is the exception: write the id, verified 2026-10-05)
//   label — display string AND the value to write in mutate payloads (not on HubSpot)
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

- **Use `useFieldOptions`** when option labels could change post-deploy — selects with rapidly-evolving lists, user-editable choices, or any case where re-pasting blocks for an option rename is annoying. Since SELECT fields write by label on Softr Database (verified 2026-08-25), live options also keep write payloads rename-proof: render and write `option.label`. HubSpot writes the choice id instead (verified 2026-10-05; see [hubspot.md](hubspot.md#writing)). Hardcoded labels remain fine as a display-only loading fallback while the live options fetch. Cross-table case: to render a select field from table B inside a block bound to table A (e.g. an intake form bound to Jobs that needs the Wigs `Color` options), put the `useRecords` + `useFieldOptions` in a hidden helper block bound to table B and publish the options to a `window` global (see [helper-blocks.md](../references/helper-blocks.md)).
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

### Operator semantics on the server

*Softr Database: `is` verified live 2026-09-18, `contains` 2026-09-19.* What the operators do once
the filter reaches the server:

- **Text `is` is case-insensitive.** `q.text("email").is("Ann@Example.com")` matches
  `ann@example.com`. Compare client-side when case matters.
- **`contains` is a case-insensitive substring test, and on a multi-value lookup it tests each
  element** — never the elements joined into one string. Multi-value lookups arrive in the browser
  as arrays of strings ([fields.md](fields.md#common-field-type-shapes)). To match one whole value inside a
  lookup, wrap every value in delimiters it cannot contain (a formula such as
  `CONCATENATE("#", {Order No}, "#")`, looked up through the link), search for the delimited
  value, and re-check the exact value client-side: an undelimited `contains("1042")` also
  matches `10420`.
- **`contains("")` returned 0 rows, not every row** (measured 2026-09-19 against a lookup field; a
  plain text field was not probed). Don't build on it either way. When a hook must match nothing
  until a value exists, give it an explicit sentinel, as in option 2 under
  [`useRecords` ignores `enabled: false`](#userecords-ignores-enabled-false); for `contains` the
  sentinel must not be a substring of any real value either.

```jsx
var KEY_NONE = "#no-key#";   // no real "#<number>#" key can contain this
var orderKey = orderNo ? "#" + orderNo + "#" : "";

// orderKeys = a lookup, through the link, of the order's "#<number>#" key formula
var lines = useRecords({ from: ds.lines, select: lineSelect, count: 100,
  where: q.text("orderKeys").contains(orderKey || KEY_NONE) });

// The server test is a substring test: keep only rows whose lookup holds the exact key.
// (items = the flattened pages of `lines`)
var mine = !orderKey ? [] : items.filter(function(r) {
  var v = r.fields.orderKeys;
  var keys = Array.isArray(v) ? v : (v ? [String(v)] : []);
  return keys.indexOf(orderKey) !== -1;
});
```

A key like this also lets a block filter by a link without selecting the link field, which would
ship the linked records' ids to the browser
([multi-datasource.md](multi-datasource.md#one-connection--one-read-payload-the-union-of-its-selects)).

### Filter and sort aliases must be in the same hook's select

*Seen live 2026-09-18 (Softr Database, on a `useMetric`).* Aliases are resolved **per hook**, not
per connection. A `where` or `orderBy` that names an alias missing from that hook's own `select`
crashes the whole block at runtime ("Could not find an alias for subject \"undefined\"" and
Softr's "Oh snap" panel), although the push compiled clean:

```jsx
// WRONG — "status" is not in this hook's select: compiles, then crashes the block
var countSelect = q.select({ orderNo: "FIELD_ID1" });
var open = useMetric({ select: countSelect, metric: metric.count(), where: q.text("status").is("Open") });

// CORRECT — every alias the where / orderBy names is in the hook's own select
var countSelect = q.select({ orderNo: "FIELD_ID1", status: "FIELD_ID2" });
```

Adding the field to the select also adds it to the connection's read payload
([multi-datasource.md](multi-datasource.md#one-connection--one-read-payload-the-union-of-its-selects)),
so put a filter on a private field on the connection that is allowed to carry it.

### Filters fail open

*Verified live 2026-09-19 (Softr Database).* A filter on a field that is **not in the
connection's read-select union**
([multi-datasource.md](multi-datasource.md#one-connection--one-read-payload-the-union-of-its-selects))
is **silently ignored**: no error, and the query returns everything, as if there were no `where`.
(This was recorded for the filter a block sends with its request, the hook's `where`. Source
conditions were not part of the finding.) How a block's own `where` can name a field outside the
union while passing the per-hook alias rule above was not established: the session that found it
also sent hand-built requests to the endpoint, which can name any field. Either way there is no
way to filter on a field without shipping it: leave it out of every read select and the filter
stops applying.

The two rules fail in opposite directions. An alias missing from the hook's own `select` crashes
the block ([above](#filter-and-sort-aliases-must-be-in-the-same-hooks-select)); a field missing from
the connection's union drops the filter without a word. A block that compiles and renders
plausible rows has passed the first check and proved nothing about the second.

Treat every `where` as unproven until you have seen it narrow:

1. Confirm each field the `where` names is in a read select on that connection.
2. Load the block as a viewer who can see more rows than the filter should leave (an admin is
   usually easiest) and compare the count with and without the `where`, or read the response in
   the network tab: 7 rows without it and 3 with it, not 7 and 7.
3. Where an ignored filter would make the block show the wrong rows (another order's lines on
   this order's page), apply the same condition client-side to every row as well, so the block
   stays correct even if the server returns everything.

A `where` is not access control in any case ([Current User](#current-user)); this is about the
block showing the rows it says it shows.

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
`{ subject: <fieldId>, type: "ARRAY", operator: "HAS_ALL_OF", value: [orderId] }`. Aliases resolve
**per hook** ([above](#filter-and-sort-aliases-must-be-in-the-same-hooks-select)), so two selects on
different connections may use the same alias name for different fields, and each filter resolves
against its own hook's `select`.

**`isOneOf` filters a link the same way**, for "linked to any of these" (verified live 2026-09-18):
`q.array("order").isOneOf(orderIds)` goes out as `operator: "IS_ONE_OF"` with the id array as
`value`, next to `hasAllOf([id])`.

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

**`window.__softr_current_user` has no change event.** It is a plain global the Softr shell fills
in, and nothing re-renders the block when it lands. An empty `userGroups` early on means the
shell is not ready yet, not that the user has no groups; read once at mount, an admin can be
settled as a non-admin for good. The shell is usually ready before the block's data arrives. Two
production blocks (2026-09-18) cover the case where it isn't: they hold the user in state, poll
with a bound, and treat an empty list as not loaded yet, since every logged-in user carries at
least Softr's predefined groups.

```jsx
import { useState, useEffect } from "react";

// Module scope. An empty userGroups means the shell is still filling in: return null until then.
function readShellUser() {
  var u = window.__softr_current_user || null;
  if (!u || !Array.isArray(u.userGroups) || u.userGroups.length === 0) return null;
  return u;
}

// In Block():
var [shellUser, setShellUser] = useState(readShellUser());
var [groupsSettled, setGroupsSettled] = useState(!!readShellUser());

useEffect(function() {
  if (groupsSettled) return;
  var tries = 0;
  var timer = setInterval(function() {
    tries += 1;
    var found = readShellUser();
    if (found) {
      clearInterval(timer);
      setShellUser(found);
      setGroupsSettled(true);
    } else if (tries >= 14) {   // about 2 s at 150 ms, then settle with no groups
      clearInterval(timer);
      setGroupsSettled(true);
    }
  }, 150);
  return function() { clearInterval(timer); };
}, [groupsSettled]);

var userGroups = (shellUser && shellUser.userGroups) || [];
var isAdmin = userGroups.some(function(g) { return g.name === "Admin"; });
```

Gate anything role-dependent on `groupsSettled` (show a skeleton until then), so a viewer never
flashes the wrong panel. The bound settles a viewer whose list never fills in, instead of leaving
them on a skeleton.

**Block code can only test group names, so a rename in Studio silently breaks a name check.** `userGroups` items arrive as names (a string, or an object with a `name`; no id was seen), and nothing in the global lets block code gate by group id. Block Visibility and action permissions are set by group id and survive a rename. While a rename is pending, accept both the old and the new name, and drop the old one afterwards: the push and the rename can then land in either order. One block did this in an app that renamed its three groups (LCDB, 2026-10-07).

```jsx
// Module scope. userGroups items arrive as strings or as objects with a name.
function groupName(g) { return typeof g === "string" ? g : (g && g.name) || ""; }

// In Block(): this replaces the `isAdmin` line in the example above.
var isAdmin = userGroups.some(function(g) {
  var n = groupName(g);
  return n === "Administrator" || n === "Admin";   // new name, then the old one until the rename is done
});
```

Before writing copy such as "they will lose access", check how each group gets its members, a manual list or a condition: that sentence was false for a user added to a group by hand.

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

- **A per-item server sum is one `useMetric` per item.** Hooks can't run in a loop over a list of variable length, so mount one inside a module-scope probe component per item, only while the figures are needed, each reporting into a state map. Not yet seen live in a block (built in a QA round that paused before its live check); the structure follows from the rules of hooks.
- **A metric that is not a finite number shows "unknown," never 0.** `Number(x) || 0` hides a NaN.
- **Before reusing an existing read for a new figure, check that read's `where`.** A work list assumed an existing read covered on-hand stock, while its `where` cut it to one transaction type (LCDB QA pass, 2026-10-08).

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

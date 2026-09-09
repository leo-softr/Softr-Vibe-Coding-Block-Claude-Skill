# The searchable dropdown (`Combo`)

**Use this instead of shadcn's `<Select>` and instead of a native `<select>`, always.**
A Vibe Coding block renders inside a **shadow DOM**, and that one fact rules out both of
the obvious choices:

| Option | Why it fails in a block |
|---|---|
| Native `<select>` | Hands the list to the OS. No keyword filter, none of your styling, and on macOS it paints a grey slab over the page. Fine for 5 options, unusable at 90. |
| shadcn `<Select>` / `<Command>` | **Portals to `document.body`, which is outside the block's shadow root**, so the styles arrive stripped. It also cannot be searched. |
| `Combo` (below) | Local DOM, brand-styled, keyword filter, A→Z, keyboard, create-new, drop-up. |

Copy the component into the block. A Vibe block is one self-contained file — there is no
shared module to import, so each block carries its own copy. Keep one canonical copy in the
project (e.g. `Assets/Softr App/Shared/combo.jsx`) and port changes from there.

## The three things that will bite you

**1. Click-outside must use `composedPath()`, not `contains()`.**
By the time a click reaches `document`, the shadow DOM has *retargeted* its `target` to the
shadow **host**. So the usual `root.contains(e.target)` test calls the panel's own rows
"outside" and closes the panel before the click can land on one — the dropdown appears to
ignore every selection.

```jsx
function onDown(e) {
  var root = rootRef.current;
  if (!root) return;
  var path = e.composedPath ? e.composedPath() : [];
  for (var i = 0; i < path.length; i++) {
    if (path[i] === root) return;      // inside — leave it open
  }
  if (path.length === 0 && e.target && root.contains(e.target)) return;  // fallback
  setOpen(false);
}
document.addEventListener("mousedown", onDown, true);
```

**2. Define it at MODULE scope, never inside `Block()`.**
A component redefined inside `Block()` gets a fresh identity every render, so React unmounts
and remounts the `<input>` and the search box loses focus after one keystroke. This is the
single most common Vibe Coding bug and it looks like a platform fault.

**3. `onMouseDown` on a row must `preventDefault()`.**
Otherwise focus leaves the search input before the click resolves.

## Sort A→Z *inside* the component

Sorting at the call site gets forgotten. Do it in the component, with an opt-out:

```jsx
function comboSortLabels(a, b) {
  return String(a.label || "").localeCompare(String(b.label || ""), undefined, {
    sensitivity: "base",   // case-insensitive
    numeric: true,         // "Item 2" before "Item 10" — a plain compare gets this backwards
  });
}
```

`autoSort` defaults to **true**. Pass `autoSort={false}` only where the given order *is* the
meaning — a pipeline of statuses (Not ordered → Ordered → … → Delivered), a physical
journey, a curated short list. Alphabetising a workflow puts "Damaged" first and buries the
starting state in the middle, which is worse than not sorting at all.

Grouped lists sort **within** a group and keep first-seen group order, so a "this project's
rooms first, everyone else after" grouping survives being alphabetised.

## Filter on every token, in any order

```jsx
var tokens = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
var filtered = options.filter(function (o) {
  if (tokens.length === 0) return true;
  var hay = String(o.label || "").toLowerCase();
  for (var i = 0; i < tokens.length; i++) {
    if (hay.indexOf(tokens[i]) === -1) return false;
  }
  return true;
});
```

So `rural art` finds *The Rural Art Company*. A single `indexOf(query)` would not.

## Searchable by default — not by option count

```jsx
var searchable = props.onCreate
  ? true
  : props.searchable === true || (props.searchable !== false && !props.bare);
```

Every **framed** dropdown — a table filter, a form field — gets the search box, whatever the
option count. `bare` inline editors are click-only. `onCreate` forces the box on, because the
typed text is what gets created.

**Why not a threshold (changed 2026-09-10).** The first version of this component showed the
search box at 8+ options. On one filter row that made "All projects" (2 options) a plain
picker and "All vendors" (99) a type-to-filter, side by side, and the client read the
difference as a bug — the project filter looked like the broken one. The count of options is
*data*; whether a dropdown is searchable is *design*, and design must not change under the
user's hands the day a third project is added. Leo, 2026-09-10: type-to-filter is the default
for table filters, even a two-option one, so the desk never has to check whether *this*
dropdown is the searchable kind. The other half of the same instruction: a status update in a
table row is a click, not a search — which is what `bare` already is.

### Which dropdowns get a search box

| Dropdown | Search box | How |
|---|---|---|
| Table filter — project, vendor, status, room, any of them | yes | default |
| Open-ended or data-driven picker in a form — vendor, project, room, item, purchase order, saved list | yes | default |
| Short **fixed** enum the user is **setting** — a status, a location, a purpose, a group-by / sort-by | no | `searchable={false}` |
| Inline `bare` editor in a table cell — a status chip, a location string | no | `bare` is click-only |
| Anything with `onCreate` | yes, always | forced |

The third row is the only place `searchable={false}` belongs: four fixed options the user is
choosing *between*, where a search box is noise. A *filter* on that same status field still
gets the box — filtering and setting are different jobs, and the filter row is exactly where
the rule has to hold uniformly. If a wrapper sits between the call site and `Combo`
(`ColumnFilter`, `SelectInput`, …), thread `searchable={props.searchable}` through it rather
than reaching past the wrapper.

## One flat row list for the keyboard

Build `rows` as a single array — the optional *clear* row, then the filtered options, then
the optional *create* row — so arrow-key navigation has one index to walk. Clamp the active
index (`Math.min(active, rows.length - 1)`): filtering shrinks the list under the highlight.

## Drop up near the fold

```jsx
var r = rootRef.current.getBoundingClientRect();
var below = window.innerHeight - r.bottom;
setDropUp(below < 300 && r.top > below);
```

A filter row near the bottom of the viewport otherwise opens into nothing.

## Variants worth having

- **`bare`** — inline-editor mode. No border, no fill; `triggerContent` (a status chip, a
  cell's text) *is* the trigger. Lets a table cell become editable without every row growing
  a form control. Click-only: the search box is off in this variant, because a status update
  in a row is a click, not a search (Leo, 2026-09-10).
  ⚠ If any column width in your table is derived from the trigger's chrome, keep the
  chevron the SAME size in both variants. Shrinking it in `bare` silently changes those
  widths in a different file.
- **`triggerStyle`** — merged over the defaults, for a trigger that is part of the design
  (a chip painted in its own status colour) rather than a plain field.
- **`onCreate(text)`** — offers `Add "<typed>"` when nothing matches. If creating the record
  and *linking* it happen at different times, say so in the toast: the two halves landing
  separately is exactly what gets reported as "it didn't save".
- **`emptyLabel`** — a row that clears the selection. Call sites that pass a leading
  `{ value: "" }` "any / none" option should have it lifted into `emptyLabel` rather than
  rendered twice.

## The one shadow you are allowed

DESIGN-system rules that ban shadows are about cards. A white panel floating over a white
card with only a hairline between them reads as part of the card, so the menu gets a shadow:

```js
boxShadow: "0 10px 30px rgba(0, 0, 0, 0.16)"
```

Everything else — the trigger, the card, the rows — stays flat.

## Checklist before shipping a dropdown

- [ ] Defined at module scope
- [ ] `composedPath()` click-outside
- [ ] Sorted A→Z inside the component, with `autoSort={false}` only where order is meaning
- [ ] Multi-token filter
- [ ] Searchable by default; `bare` is click-only; `searchable={false}` only on a short fixed enum the user is setting
- [ ] Keyboard: ↑ ↓ Enter Esc Tab, active row scrolled into view
- [ ] `aria-haspopup="listbox"`, `aria-expanded`, `role="listbox"` / `role="option"`,
      `aria-selected`, and an `aria-label` on the trigger
- [ ] Loading and empty states (`"Nothing matches that."`)
- [ ] No `@/components/ui/select` import anywhere in the file

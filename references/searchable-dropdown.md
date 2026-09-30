# The searchable dropdown (`Combo`)

**Use this instead of shadcn's `<Select>` and instead of a native `<select>`, always.**
A Vibe Coding block renders inside a **shadow DOM**, and that one fact rules out both of
the obvious choices:

| Option | Why it fails in a block |
|---|---|
| Native `<select>` | Hands the list to the OS. No keyword filter, none of your styling, and on macOS it paints a grey slab over the page. Fine for 5 options, unusable at 90. |
| shadcn `<Select>` / `<Command>` | **Portals to `document.body`, which is outside the block's shadow root**, so the styles arrive stripped. It also cannot be searched. |
| `Combo` (below) | Local DOM, brand-styled, keyword filter, A→Z, keyboard, create-new, clip-aware drop-up. |

Copy the component into the block. A Vibe block is one self-contained file — there is no
shared module to import, so each block carries its own copy. Keep one canonical copy in the
project (e.g. `Assets/Softr App/Shared/combo.jsx`) and port changes from there.

## The four things that will bite you

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

**4. The panel is clipped by any ancestor whose `overflow` is not `visible`.**
The panel is `position: absolute` inside the trigger's `relative` wrapper, in the block's own
DOM, because it cannot portal out of the shadow root (see *Why not portal* below). Its
containing block is that wrapper, so *every* ancestor whose `overflow` is `hidden`, `auto`,
`scroll` or `clip` clips it, however far up. In Tailwind that is `overflow-hidden`,
`overflow-auto`, `overflow-y-auto`, `overflow-x-auto` (an `overflow-x` of `hidden`, `auto` or
`scroll` turns `overflow-y: visible` into `auto`, so it clips vertically too), `truncate` (it
sets `overflow: hidden`) and `line-clamp-*` (so does that). A clipped `<td>` is the height of
its row, and the menu opens inside it. Three rules follow.

**Rule 1 — never put a clipping class on an element that contains a `Combo`:** a `<td>`, a
card, a flex cell, anything between the Combo and the scroller it belongs to. If a chip or
label inside the trigger can overflow, bound it at the chip: `truncate` (or `overflow-hidden`)
plus `min-w-0` on the chip itself. The trigger is a flex row, and `min-w-0` is what lets a flex
item shrink below its text — strictly redundant while the chip clips itself, load-bearing the
moment the ellipsis moves to a span inside it. Clipping at the chip clips the chip. Clipping at
the cell clips the menu.

```jsx
<td className="px-4">{/* no overflow class on the cell */}
  <Combo
    bare
    triggerContent={<span className="min-w-0 truncate px-2" style={chipStyle}>{label}</span>}
    …
  />
</td>
```

**Rule 2 — decide the drop-up and the list's height against the clipping ancestors, not the
window.** `window.innerHeight - rect.bottom` cannot see scroll containers: a table with its own
`max-height` + `overflow: auto` scroller, a dialog body with `overflow-y-auto`, a horizontally
scrollable table wrapper. A row near the bottom of one of those opens its menu downward into
the scroller's hidden area while the window still has plenty of room. Measure inside the strip
the panel can actually paint into:

```jsx
var COMBO_LIST_MAX = 256; // the list's normal ceiling (max-h-64)
var COMBO_LIST_MIN = 120; // the floor: below this, accept a clip rather than a useless list

/* The strip of screen the panel can paint into: the viewport, cut down by every ancestor
   that clips vertically. overflowY is enough on its own: an overflow-x of hidden, auto or
   scroll already turns a visible overflow-y into auto in the computed style. */
function comboClipBox(node) {
  var top = 0;
  var bottom = window.innerHeight;
  var el = node;
  while (el && el !== document.body && el !== document.documentElement) {
    // clientHeight is 0 for the boxes overflow does not apply to (inline, display: contents)
    if (el.clientHeight > 0 && window.getComputedStyle(el).overflowY !== "visible") {
      var r = el.getBoundingClientRect();
      var t = r.top + el.clientTop; // the clip edge is the padding box: inside the border
      var b = t + el.clientHeight; //  and above a horizontal scrollbar
      if (t > top) top = t;
      if (b < bottom) bottom = b;
    }
    // Where the parent chain ends at the shadow root, carry on from its host.
    el = el.parentElement || el.getRootNode().host || null;
  }
  return { top: top, bottom: bottom };
}

/* chrome = the panel's height outside the list: the search box and the borders. */
function comboPlace(wrapper, chrome) {
  var clip = comboClipBox(wrapper);
  var r = wrapper.getBoundingClientRect();
  var below = clip.bottom - r.bottom - 10; // the 2px gap to the trigger + 8px to spare
  var above = r.top - clip.top - 10;
  var up = below < chrome + COMBO_LIST_MAX && above > below;
  var room = (up ? above : below) - chrome;
  return { up: up, listMax: Math.max(COMBO_LIST_MIN, Math.min(COMBO_LIST_MAX, room)) };
}
```

Call it when the panel opens, and give the list its height as an inline style in place of
`max-h-64`:

```jsx
var [listMax, setListMax] = useState(COMBO_LIST_MAX);

// in toggle(), before setOpen(true):
if (rootRef.current) {
  var place = comboPlace(rootRef.current, searchable ? 51 : 2);
  setDropUp(place.up);
  setListMax(place.listMax);
}

// the list:
<div ref={listRef} role="listbox" className="overflow-y-auto py-1" style={{ maxHeight: listMax }}>
  {/* rows */}
</div>
```

Downward when the whole panel fits below, otherwise toward the larger side, with the list
capped to the room it gets. `chrome` is the panel's height outside the list — about 51px with
the search box (`p-2` around an `h-8` input, a 1px rule, the panel's two borders) and 2px
without; measure yours if the panel differs. The fit test assumes a full-height list, so a
three-option menu may flip up when it would have fit below, which costs nothing. The walk
starts at the wrapper, whose own overflow would clip the panel too; it leaves the shadow root
through its host, so a clipping container outside the block still counts; and it stops below
`<body>`, because `body` and `html` hand their overflow to the viewport — their computed
`overflow` can say `hidden` while they clip nothing. The four cases it has to get right: a row
mid-way down a tall table scroller opens down; the last visible row of a scroller whose bottom
edge is mid-window opens up, inside the scroller (the window-only rule opened it down, into
the hidden part); a picker at the bottom of a dialog body opens up, inside the dialog; a filter
row at the window's bottom edge opens up, as before. All four, plus a scroller outside the
shadow root, checked in Chromium on 2026-09-30 on a test page — not yet in a deployed block.

Rule 2 does not rescue a clipped cell. The cell is the height of its row, so neither side has
room, the list falls to its 120px floor and is clipped anyway. Rule 1 is not optional.

**Rule 3 — keep the active row visible by scrolling the list, never with `scrollIntoView`.**
`scrollIntoView` scrolls *every* scrollable ancestor until the element shows, and an
`overflow: hidden` box is still scrollable from script. In a clipped cell it scrolls the
cell's content until the option shows, pushing the trigger out of view; near the edge of a
table it scrolls whatever the menu hangs out of — the table's own scroller, the page — so the
table jumps as the menu opens. Scroll the list element and nothing else:

```jsx
useEffect(
  function () {
    var list = listRef.current;
    if (!open || !list) return;
    var el = list.querySelector('[data-active="true"]');
    if (!el) return;
    var lr = list.getBoundingClientRect();
    var er = el.getBoundingClientRect();
    var viewTop = lr.top + list.clientTop; // inside the list's top border
    var viewBottom = viewTop + list.clientHeight; // clientHeight excludes border and scrollbar
    if (er.top < viewTop) list.scrollTop -= viewTop - er.top;
    else if (er.bottom > viewBottom) list.scrollTop += er.bottom - viewBottom;
  },
  [open, activeIdx, query]
);
```

Rects rather than `offsetTop`: a row's `offsetParent` is the nearest positioned ancestor,
which is the panel, not the list, so `offsetTop` comes out too large by the search box's
height unless the list is made `position: relative`. Rects need no such arrangement. The
effect runs after the commit, outside the event cycle Hard Constraint 17's `setTimeout` is
there to escape — the `scrollIntoView` it replaces ran from the same kind of effect and took
effect. `focus()` scrolls ancestors the same way, so focus the search box with
`inputRef.current.focus({ preventScroll: true })`.

**Why not portal the panel, or make it `position: fixed`?** A portal to `document.body`
leaves the shadow root, and the styles stay behind — the shadcn row at the top of this page.
`position: fixed` inside the shadow root escapes the clipping only while no ancestor has a
`transform`, `filter`, `perspective`, `contain` or `will-change`: any of those becomes the
containing block for fixed descendants, and scroll-reveal animations on Softr pages commonly
leave a transform behind (the same trap as the block-owned header in
[static-blocks.md](static-blocks.md#block-owned-landing-page-header)). A fixed panel also stops
moving with its trigger, so it has to be re-placed on every scroll. The clip-aware absolute
panel has neither problem, which is why it is the design here.

**The incident — ROSIE, 2026-09-30.** Three item tables put `overflow-hidden` on the `<td>`
holding the status chip, as a backstop so the chip, 1–2px too wide at the column's narrowest
drag width, would clip at its own column instead of painting over the next one. The comment
beside it said the status menu was portaled to the body, so the clip could not reach it. That
was true of the shadcn `<Select>` the tables used before and stopped being true when they moved
to `Combo`; nobody re-checked. The menu opened inside the 48px cell: one and a half options
showing, the chip scrolled out of view by `scrollIntoView`, the other six unreachable by
mouse. The Location dropdown in the same rows kept working, because its cell had no overflow
class. A 2px backstop cost the whole feature. A comment that says how a component renders is
a claim to verify in the component, not in the comment.

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
Keep the highlighted row in view by scrolling the list only (rule 3 of item 4 above).

## Variants worth having

- **`bare`** — inline-editor mode. No border, no fill; `triggerContent` (a status chip, a
  cell's text) *is* the trigger. Lets a table cell become editable without every row growing
  a form control. Click-only: the search box is off in this variant, because a status update
  in a row is a click, not a search (Leo, 2026-09-10).
  ⚠ If any column width in your table is derived from the trigger's chrome, keep the
  chevron the SAME size in both variants. Shrinking it in `bare` silently changes those
  widths in a different file.
  ⚠ A `bare` Combo sits in a table cell, which is exactly where `overflow-hidden` and
  `truncate` get added. Keep them off the cell and bound the chip instead — rule 1 of item 4
  in [The four things that will bite you](#the-four-things-that-will-bite-you).
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
- [ ] No overflow-clipping class (`overflow-hidden`, `overflow-*-auto`, `truncate`,
      `line-clamp-*`) between the Combo and the scroller it belongs to; an over-wide chip
      bounded at the chip (`min-w-0 truncate`)
- [ ] Drop-up and list `maxHeight` measured against the clipping ancestors, not the window
- [ ] Keyboard: ↑ ↓ Enter Esc Tab; the active row kept visible by scrolling the list only
      (never `scrollIntoView`), and the search box focused with `preventScroll`
- [ ] `aria-haspopup="listbox"`, `aria-expanded`, `role="listbox"` / `role="option"`,
      `aria-selected`, and an `aria-label` on the trigger
- [ ] Loading and empty states (`"Nothing matches that."`)
- [ ] No `@/components/ui/select` import anywhere in the file

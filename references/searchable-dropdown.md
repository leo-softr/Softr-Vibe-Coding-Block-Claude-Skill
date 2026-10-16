# The searchable dropdown (`Combo`)

**Use this instead of shadcn's `<Select>` and instead of a native `<select>`, always.**
A Vibe Coding block renders inside a **shadow DOM**, and that one fact rules out both of
the obvious choices:

| Option | Why it fails in a block |
|---|---|
| Native `<select>` | Hands the list to the OS. No keyword filter, none of your styling, and on macOS it paints a grey slab over the page. Fine for 5 options, unusable at 90. |
| shadcn `<Select>` / `<Command>` | **Portals to `document.body`, which is outside the block's shadow root**, so the styles arrive stripped. It also cannot be searched. |
| `Combo` (below) | Local DOM, brand-styled, keyword filter, A→Z, keyboard, create-new, a `position: fixed` panel placed against whatever can clip it. |

The date field has the same problem with the same answer: `<input type="date">` hands its calendar
to the browser, so a block uses the in-DOM `DatePicker` kit in [date-picker.md](date-picker.md),
which follows rule 1 of item 4 below, the Escape rule and the focus-on-open rule of this page.

Copy the component into the block. A Vibe block is one self-contained file — there is no
shared module to import, so each block carries its own copy. Keep one canonical copy in the
project (e.g. `Assets/Softr App/Shared/combo.jsx`) and port changes from there. Pasting it
verbatim between marker lines that carry its sha makes that port mechanical:
[date-picker.md → The kit between markers](date-picker.md#the-kit-between-markers).

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

**4. The panel is `position: fixed`, and a fixed box has two traps of its own.**
The panel lives in the block's own DOM, because it cannot portal out of the shadow root (see *Why not
portal* below). Until 2026-09-30 it was `position: absolute` inside the trigger's `relative` wrapper, and
then *every* ancestor whose `overflow` was `hidden`, `auto`, `scroll` or `clip` clipped it, however far up.
In Tailwind that is `overflow-hidden`, `overflow-auto`, `overflow-y-auto`, `overflow-x-auto` (an
`overflow-x` of `hidden`, `auto` or `scroll` turns `overflow-y: visible` into `auto`, so it clips
vertically too), `truncate` (it sets `overflow: hidden`) and `line-clamp-*` (so does that). A clipped
`<td>` was the height of its row, and a table's own scroll box squeezed the menu on a table holding a row
or two, however cleverly it was placed inside it.

ROSIE's `Shared/combo.jsx` is `position: fixed` now, anchored to its trigger. **A fixed box escapes every
clipping ancestor below its containing block**, so a cell, a card or a table's scroll box no longer cuts
the menu: the one-row Damages tab that Leo called "cramped" shows all eight statuses whole. The price is
two traps, and four rules.

- **The containing block.** A fixed box is placed against the viewport only while no ancestor has a
  `transform`, `filter`, `perspective`, `contain`, `container-type` or a `will-change` naming one of those,
  or an individual `translate`, `rotate` or `scale`. Any of them becomes the containing block, and the panel
  must be placed against *that*, and can still be clipped by it and what sits above it. A Radix dialog
  centres itself with `translate` and zooms in from 0.95; Softr's scroll fade-in leaves a `transform` behind
  on a block while it runs.
- **It does not travel.** A fixed panel stays where it was put while its trigger moves, so anything that
  moves the trigger has to close it.

**Rule 1 — still bound an over-wide chip at the chip, not at the cell.** With a fixed panel an
`overflow-hidden` cell no longer cuts the menu, but it still clips the trigger and everything else in the
cell, and the placement code measures the clipping boxes at and above the containing block. ROSIE keeps the
old rule: no clipping class (`overflow-hidden`, `overflow-*-auto`, `truncate`, `line-clamp-*`) on an element
that contains a `Combo`. If a chip or label inside the trigger can overflow, bound it at the chip: `truncate`
(or `overflow-hidden`) plus `min-w-0` on the chip itself. The trigger is a flex row, and `min-w-0` is what
lets a flex item shrink below its text. Clipping at the chip clips the chip.

```jsx
<td className="px-4">{/* no overflow class on the cell */}
  <Combo
    bare
    triggerContent={<span className="min-w-0 truncate px-2" style={chipStyle}>{label}</span>}
    …
  />
</td>
```

**Rule 2 — place the panel against its containing block, and decide the drop-up and the list's height
against what can clip it, not against the window.** Three functions do it, all in ROSIE's `Shared/combo.jsx`
(verbatim below; the constants mirror the panel's classes, so change them together):

- `comboClipBox(node)` — the box a panel can paint into: the viewport cut down by every ancestor that clips,
  from `node` up across shadow roots to (not including) `<body>`, whose overflow belongs to the viewport.
  Padding boxes, both axes tested separately, boxes overflow does not apply to skipped.
- `comboFixedBase(node)` — the nearest ancestor that is the fixed panel's containing block, or `null` for
  the viewport. It checks `transform`, the individual `translate`, `rotate` and `scale`, `perspective`,
  `filter`, `backdrop-filter`, `contain`, `container-type` and `will-change`, and walks across shadow roots.
- `comboPlacement(root, rowCount, searchable)` — `{ up, right, x, y, listMax, maxW, minW }`. The room is the
  viewport, or, with a containing block, that block's clip and everything above it (the boxes *below* it no
  longer count, because a fixed panel paints over them). The anchor is the trigger's bottom-left corner, 2px
  clear, converted into the containing block's own pixels: the screen distance divided by the block's scale
  (`rect.width / offsetWidth`), minus its border, plus its scroll. Without the scale term a panel in a dialog
  part-way through its 0.95 → 1 zoom lands about 5% of the distance away from its trigger.

```jsx
/* ---- Placement ------------------------------------------------------------------------------
   The panel is positioned in the block's own DOM because it cannot portal out of the shadow
   root (see the header). Until 2026-09-30, late, it was `absolute`, so EVERY ancestor that clips
   clipped it: a status <td> with overflow-hidden cut the Order status menu to one row, and the
   tables' scroll boxes squeezed it on a table holding only a row or two, however cleverly it was
   placed inside them. It is `fixed` now, which escapes all of that; what is left to measure is
   the containing block a fixed box still answers to (comboFixedBase) and the clipping at or
   above it. These sizes mirror the panel's classes below — change them together. */
var COMBO_ROW_H = 32; // one option: py-1.5 around a 20px text-sm line
var COMBO_LIST_PAD = 8; // the list's py-1
var COMBO_LIST_MAX = 264; // eight 32px rows + the py-1: all eight statuses fit whole (was 256, max-h-64)
var COMBO_LIST_MIN = 120; // the floor: below this, accept a clip rather than a useless list
var COMBO_SEARCH_H = 49; // p-2 around the h-8 search input, plus its 1px rule
var COMBO_EDGE = 10; // the 2px gap to the trigger, the panel's borders, a little air
var COMBO_MAX_W = 380;
var COMBO_PLACE_DEFAULT = { up: false, right: false, x: 0, y: 0, listMax: COMBO_LIST_MAX, maxW: COMBO_MAX_W, minW: 0 };

/* The box a panel can paint into: the viewport, cut down by every ancestor that clips, from
   `node` up across shadow roots to (not including) <body>, whose own overflow belongs to the
   viewport. For the fixed panel, `node` is its containing block (see comboPlacement). The axes
   are tested separately: an overflow-x of hidden, auto or scroll already turns a visible
   overflow-y into auto in the computed style, while overflow-x: clip does not. Edges are
   padding boxes — inside the border, clear of a scrollbar — and boxes overflow does not apply
   to (inline, display: contents) are skipped. */
function comboClipBox(node) {
  var box = { top: 0, left: 0, bottom: window.innerHeight, right: window.innerWidth };
  var el = node;
  while (el && el !== document.body && el !== document.documentElement) {
    if (el.clientHeight > 0 || el.clientWidth > 0) {
      var cs = window.getComputedStyle(el);
      var clipY = cs.overflowY !== "visible";
      var clipX = cs.overflowX !== "visible";
      if (clipY || clipX) {
        var r = el.getBoundingClientRect();
        if (clipY && el.clientHeight > 0) {
          var t = r.top + el.clientTop;
          if (t > box.top) box.top = t;
          if (t + el.clientHeight < box.bottom) box.bottom = t + el.clientHeight;
        }
        if (clipX && el.clientWidth > 0) {
          var l = r.left + el.clientLeft;
          if (l > box.left) box.left = l;
          if (l + el.clientWidth < box.right) box.right = l + el.clientWidth;
        }
      }
    }
    el = el.parentElement || (el.getRootNode && el.getRootNode().host) || null;
  }
  return box;
}

/* The element a `position: fixed` panel is placed against when it is not the viewport: the
   nearest ancestor with a transform — or an individual translate, rotate or scale, which is how
   the dialogs centre themselves here (verified 2026-09-30: the Add items dialog's panel landed
   exactly the dialog's own offset away until `translate` was checked) — a filter, perspective,
   backdrop-filter, paint or layout containment, a container type, or a will-change naming one of
   those. A block caught mid-way through the page's scroll fade-in (a `transform`) counts too.
   null means the viewport. Walks across shadow roots, starting at the panel's own parent. */
function comboFixedBase(node) {
  var el = node;
  while (el && el !== document.body && el !== document.documentElement) {
    var cs = window.getComputedStyle(el);
    if (
      (cs.transform && cs.transform !== "none") ||
      (cs.translate && cs.translate !== "none") ||
      (cs.rotate && cs.rotate !== "none") ||
      (cs.scale && cs.scale !== "none") ||
      (cs.perspective && cs.perspective !== "none") ||
      (cs.filter && cs.filter !== "none") ||
      (cs.backdropFilter && cs.backdropFilter !== "none") ||
      /paint|layout|strict|content/.test(cs.contain || "") ||
      (cs.containerType && cs.containerType !== "normal") ||
      /transform|perspective|filter/.test(cs.willChange || "")
    ) {
      return el;
    }
    el = el.parentElement || (el.getRootNode && el.getRootNode().host) || null;
  }
  return null;
}

/* Down when the whole list fits below, else toward the side with more room, with the list capped
   to that room — every option stays reachable, scrolling inside the list if it must. Rows are a
   fixed 32px, so the fit test counts real rows rather than assuming a full list: a four-option
   menu near an edge does not flip for room it will never use. "Room" is the viewport, or — when
   a transformed ancestor is the containing block — that ancestor's clip and everything above
   it; the boxes BELOW it (a table's scroll box, a card, a cell) no longer count, because a fixed
   panel paints over them. Horizontally a trigger near the right edge of that room hangs its
   panel from its right edge, growing leftward; an edge of the trigger that runs past the room is
   pulled back inside so the panel never starts out of sight. The anchor comes back in the
   containing block's own coordinates; the panel's transform does the rest (see panelStyle), so it
   never has to be measured before it is shown. */
function comboPlacement(root, rowCount, searchable) {
  var place = { up: false, right: false, x: 0, y: 0, listMax: COMBO_LIST_MAX, maxW: COMBO_MAX_W, minW: 0 };
  if (!root) return place;
  var base = comboFixedBase(root);
  var box = base
    ? comboClipBox(base)
    : {
        top: 0,
        left: 0,
        bottom: window.innerHeight,
        right: Math.min(window.innerWidth, document.documentElement.clientWidth || window.innerWidth),
      };
  var r = root.getBoundingClientRect();
  var chrome = COMBO_EDGE + (searchable ? COMBO_SEARCH_H : 0);
  var want = Math.min(COMBO_LIST_MAX, Math.max(1, rowCount) * COMBO_ROW_H + COMBO_LIST_PAD);
  var below = box.bottom - r.bottom - chrome;
  var above = r.top - box.top - chrome;
  place.up = below < want && above > below;
  place.listMax = Math.max(COMBO_LIST_MIN, Math.min(COMBO_LIST_MAX, Math.floor(place.up ? above : below)));
  var visLeft = Math.max(r.left, box.left);
  var visRight = Math.min(r.right, box.right);
  var toRight = box.right - visLeft;
  var toLeft = visRight - box.left;
  place.right = toRight < 300 && toLeft > toRight;
  place.maxW = Math.max(0, Math.floor(Math.min(COMBO_MAX_W, place.right ? toLeft : toRight)));
  place.minW = Math.max(0, Math.min(Math.round(r.width), place.maxW));
  var ax = place.right ? visRight : visLeft;
  var ay = place.up ? r.top - 2 : r.bottom + 2;
  if (!base) {
    place.x = Math.round(ax);
    place.y = Math.round(ay);
    return place;
  }
  /* Screen pixels → the containing block's own pixels. A dialog part-way through its zoom-in is
     SCALED (0.95 → 1), and a fixed box inside it is scaled with it, so measure the scale (the
     rect's size over the layout size) and divide it out, then step in past the border and add
     any scroll. Without the scale term the panel lands ~5% of the distance off its trigger —
     seen in the preview, where the dialog sat at 0.95. */
  var br = base.getBoundingClientRect();
  var sx = base.offsetWidth ? br.width / base.offsetWidth : 1;
  var sy = base.offsetHeight ? br.height / base.offsetHeight : 1;
  if (!sx) sx = 1;
  if (!sy) sy = 1;
  place.x = Math.round((ax - br.left) / sx - base.clientLeft + base.scrollLeft);
  place.y = Math.round((ay - br.top) / sy - base.clientTop + base.scrollTop);
  place.listMax = Math.floor(place.listMax / sy);
  place.maxW = Math.floor(place.maxW / sx);
  place.minW = Math.round(place.minW / sx);
  return place;
}
```

Call it when the panel opens, store the result, and style the panel from it (`SURFACE` and `BORDER` are the block's own colour constants). Dropping up or hanging from the
right edge is a `translate` by the panel's own size, so the panel lands flush without being measured first:

```jsx
var [place, setPlace] = useState(COMBO_PLACE_DEFAULT);

// in toggle(), before setOpen(true):
setPlace(comboPlacement(rootRef.current, options.length + (props.emptyLabel ? 1 : 0), searchable));

  /* Fixed, at the anchor comboPlacement worked out: the trigger's bottom-left corner, 2px clear.
     Dropping up or hanging from the right edge is a translate by the panel's OWN size, so the
     panel lands flush without being measured first. */
  var shiftX = place.right ? "translateX(-100%)" : "";
  var shiftY = place.up ? "translateY(-100%)" : "";
  var panelStyle = {
    position: "fixed",
    top: place.y + "px",
    left: place.x + "px",
    transform: shiftX || shiftY ? (shiftX + " " + shiftY).trim() : "none",
    zIndex: 1000,
    backgroundColor: SURFACE,
    border: "1px solid " + BORDER,
    boxShadow: "0 10px 30px rgba(59, 31, 43, 0.16)",
    minWidth: place.minW + "px",
    width: "max-content",
    maxWidth: place.maxW + "px",
  };

// the list, capped to the room it gets:
<div ref={listRef} role="listbox" className="overflow-y-auto py-1" style={{ maxHeight: place.listMax }}>
  {/* rows */}
</div>
```

Down when the whole list fits below, otherwise toward the side with more room, with the list capped to that
room, so every option stays reachable by scrolling inside the list. Rows are a fixed 32px, so the fit test
counts the real rows rather than assuming a full list, and a four-option menu near an edge does not flip for
room it will never use. The list is capped at 264px (eight rows and the list's padding), so the eight order
statuses fit whole; below 120px it accepts a clip rather than a useless list.

**The same room decides which edge the panel hangs from.** A panel hung from the trigger's left edge with
`width: max-content` runs past the right edge of the room when the trigger sits in the last column. When the
room to the right of the trigger is under about 300px and there is more to the left, the panel hangs from the
trigger's right edge (`translateX(-100%)`) and `maxWidth` is capped to the room on that side; an edge of the
trigger that runs past the room is pulled back inside, so the panel never starts out of sight.

**On app pages with Softr navigation, the viewport room doesn't reach the window's edges either.**
Softr's bars sit over the page, outside the block: from a 768px window, a 56px sticky top bar;
below it, a sticky tab bar at the bottom, 57px as rendered (Softr's variable says 55px; both bars
z-index 800, measured live 2026-10-05). `comboPlacement` starts the viewport room at `0` and
`window.innerHeight`, so a trigger just under the top bar can open its menu up and under the bar, and
on a phone a menu can open down behind the tab bar. That clash is inferred from the measurements, not
seen. Start the room inside the bars (an untested variant):

```jsx
var SOFTR_TOP_BAR = 56; // Softr's sticky top bar, window 768px and up
var SOFTR_TAB_BAR = 57; // Softr's phone tab bar, window below 768px: measured 57px; its variable says 55px

// in comboPlacement, the box used when there is no containing block (and the first line of comboClipBox):
var phone = window.innerWidth < 768; // Softr's own switch: 767px = tab bar, 768px = top bar
var box = {
  top: phone ? 0 : SOFTR_TOP_BAR,
  left: 0,
  bottom: window.innerHeight - (phone ? SOFTR_TAB_BAR : 0),
  right: Math.min(window.innerWidth, document.documentElement.clientWidth || window.innerWidth),
};
```

On a page without Softr navigation (log in, a landing page) the top offset only makes the
panel open upward a little less readily. The same bar heights apply to any other room check
or window scroll in a block:
[common-patterns.md → Clear Softr's sticky bars](common-patterns.md#clear-softrs-sticky-bars).

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

A scroll of any ancestor also closes the fixed panel (Rule 4), so `scrollIntoView` would now close the menu as well as move the page.

**Rule 4 — close the panel when its trigger moves.** A fixed panel stays where it was put, so a scroll of the
page or of any box the trigger sits in, or a resize, closes it, the way a native select behaves. Listen on
`window` and on every ancestor whose `overflow` can scroll, walking up through the shadow host. Scrolling
the panel's own list never reaches these listeners: scroll does not bubble, and the list is not an ancestor
of the trigger.

```jsx
  /* A fixed panel stays where it was put while its trigger moves, so anything that moves the
     trigger closes it: a scroll of the page or of any box the trigger sits in, or a resize.
     Scrolling the panel's own list never reaches these listeners — scroll does not bubble, and
     the list is not an ancestor of the trigger. */
  useEffect(
    function () {
      if (!open) return undefined;
      var targets = [window];
      var el = rootRef.current;
      while (el && el !== document.documentElement) {
        var cs = window.getComputedStyle(el);
        if (/auto|scroll|overlay|hidden/.test(cs.overflowX + " " + cs.overflowY)) targets.push(el);
        el = el.parentElement || (el.getRootNode && el.getRootNode().host) || null;
      }
      function close() {
        setOpen(false);
      }
      targets.forEach(function (t) {
        t.addEventListener("scroll", close, { passive: true });
      });
      window.addEventListener("resize", close);
      return function () {
        targets.forEach(function (t) {
          t.removeEventListener("scroll", close);
        });
        window.removeEventListener("resize", close);
      };
    },
    [open]
  );
```

**Why not portal the panel, and why `position: fixed` after all?** A portal to `document.body` leaves the
shadow root, and the styles stay behind: the shadcn row at the top of this page. `position: fixed` inside the
shadow root escapes the clipping only while no ancestor is its containing block, and scroll-reveal animations
on Softr pages commonly leave a transform behind (the same trap as the block-owned header in
[static-blocks.md](static-blocks.md#block-owned-landing-page-header)). This page used to recommend an
absolute panel for that reason, together with the fact that a fixed panel does not move with its trigger.
ROSIE moved to a fixed panel on 2026-09-30, late, because a short table squeezes an absolute one however well
it is placed, and made the two costs cheap: `comboFixedBase` finds the containing block and `comboPlacement`
converts the anchor into its coordinates, and the panel closes on scroll and resize instead of following the
trigger. Two containing-block sources were found the hard way, on the list page's Add items dialog (verified
2026-09-30): the dialog centres itself with the individual `translate` property, not `transform`, so the
panel landed exactly the dialog's own offset away until `translate` was checked; and it zooms in from 0.95,
so the placement has to divide the scale out.

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

**The follow-up, the same evening.** Leo's screenshot of a one-row Damages table, "cramped", showed the other
half: an absolute panel inside a short table's scroll box is squeezed to the box however well it is placed.
That is why the panel is `position: fixed` now. Placement against the containing block, and closing on
scroll, are what that costs.

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

## Move focus into the Combo when it opens

When the panel opens, the Combo moves focus into itself: to the search box if it has one,
otherwise to the trigger. Do not count on the click to do it. **Safari (macOS and iPadOS) and
Firefox on macOS do not focus a `<button>` when it is clicked** (Chrome does), so on a click-only
Combo focus stays in whatever field had it, usually the text input above it in a form. Two things then
break at once: the keys the user types land in that input, and Escape goes past the Combo to the
next listener. Inside the [in-block modal](common-patterns.md#a-modal-above-softrs-bars), that
listener closes the modal or asks to discard the typed input, with the list still open.

```jsx
useEffect(
  function () {
    if (!open) return;
    if (searchable) {
      if (inputRef.current) inputRef.current.focus({ preventScroll: true });
    } else if (triggerRef.current) {
      triggerRef.current.focus({ preventScroll: true });
    }
  },
  [open, searchable]
);
```

A click-only list is then driven from the trigger: ↑ ↓ move the highlight, Enter picks, Escape
closes. Give that trigger `role="combobox"` with `aria-activedescendant` pointing at the
highlighted row, because `aria-activedescendant` is not valid on a plain button.
`preventScroll` is there for the same reason as on the search box (rule 3 of item 4).

**Escape closes the list and nothing else.** While the list is open, the Combo's keydown
handler calls `e.preventDefault()` and `e.stopPropagation()`, closes the list and puts focus
back on the trigger. React's handler on the Combo root runs inside the shadow root, before the
event reaches `document`. The in-block modal's document listener returns early on
`e.defaultPrevented`, so the modal stays open and clean. Either guard alone covers that modal,
but keep both: another document-level listener may not check `defaultPrevented`.

**To reproduce Safari in any browser,** focus the text field before the Combo, call `.click()`
on the trigger from the console (a synthetic click does not move focus either), and read
`activeElement` on the block's shadow root. It must be the search box or the trigger. Test
typing with real key events. A browser-automation "type" action that inserts text without key
events drops it into the last focused text field, which makes a correct Combo look broken.

**The incident, 2026-10-07.** A browser check reported that in B4's New
partner modal, letters typed after opening the click-only "Partner type" list went into
Organization name, and Escape then showed the modal's "Discard your changes?" strip while the
list stayed open. Part of that report came from the test tool, whose "type" action wrote into the
last focused text field. But the code audit it prompted found the real gap: every copy of the
component moved focus on open only when the list was searchable. On Safari, where a click leaves
focus where it was, a click-only list never got the keyboard. Eight of the fifteen blocks had
it. Chrome hid it, because there the click itself focuses the trigger. The effect above fixed
all eight, rechecked on every page with a synthetic click and real key presses.

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
- [ ] The panel is `position: fixed`, placed with `comboFixedBase` and `comboPlacement`: drop-up, right-edge
      hang and list height measured against the viewport, or against a transformed ancestor (a dialog) and
      what clips it, never against the window alone; closed on a scroll of any ancestor and on resize
- [ ] On app pages, the room starts inside Softr's top bar and phone tab bar (an untested variant, see above)
- [ ] Keyboard: ↑ ↓ Enter Esc Tab; the active row kept visible by scrolling the list only
      (never `scrollIntoView`), and the search box focused with `preventScroll`
- [ ] Opening moves focus into the Combo: the search box, or the trigger on a click-only
      list, because Safari does not focus a clicked button. Escape on an open list calls
      `preventDefault` + `stopPropagation` and closes only the list
      ([Move focus into the Combo when it opens](#move-focus-into-the-combo-when-it-opens))
- [ ] `aria-haspopup="listbox"`, `aria-expanded`, `role="listbox"` / `role="option"`,
      `aria-selected`; a click-only trigger that carries `aria-activedescendant` also gets
      `role="combobox"`
- [ ] The trigger is named with `aria-labelledby="<label id> <trigger id>"`, so its accessible
      name holds the field and the selected value. An `aria-label` with only the field name
      replaces the button's own text, so a screen reader never hears the value (QA write
      pass, 2026-10-08: an edit dialog's dropdowns announced "Partner type" and nothing else,
      while another block's dropdowns announced both)
- [ ] Loading and empty states (`"Nothing matches that."`)
- [ ] No `@/components/ui/select` import anywhere in the file

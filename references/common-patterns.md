# Common Patterns

Small reusable patterns that come up across Vibe Coding blocks but don't warrant their own reference file. Each is a copy-pasteable snippet. The first three snippets use legacy var-style (`var`, `function() {}`), which remains valid; the newer patterns use modern TS — both compile (see SKILL.md Style Conventions).

**Browser environment note.** Vibe blocks render in a shadow root in the MAIN document — not an iframe — so window-level APIs behave normally from block code: `window.scrollY` reflects the real page scroll, window-level events (scroll, resize, keydown) fire, `localStorage`/`navigator.clipboard`/`window.history` all work. Standard `useEffect` add/remove-listener with cleanup is the right shape for event-driven UI; use `{ passive: true }` for scroll/touch listeners. (SKILL.md Hard Constraint 17's `setTimeout` rule applies to ISSUING programmatic scrolls only, not to listening.)

## Table of Contents

- [Cross-Page State with localStorage + URL Parameters](#cross-page-state-with-localstorage--url-parameters)
- [Clipboard Copy Button](#clipboard-copy-button)
- [Navigation Blocker for Unsaved Changes](#navigation-blocker-for-unsaved-changes)
- [Scroll-Condensing Fixed Header (Landing-Page Hero)](#scroll-condensing-fixed-header-landing-page-hero)
- [Auth-Aware Header CTA](#auth-aware-header-cta)
- [Edge-Fade Image Mask (Editorial Hero)](#edge-fade-image-mask-editorial-hero)
- [Decorative Background Blobs (Editorial Layering)](#decorative-background-blobs-editorial-layering)
- [Dot-Separated Inline List](#dot-separated-inline-list)
- [Drag-to-Reorder Rows](#drag-to-reorder-rows)
- [Create → open](#create--open)
- [Clickable Row with an Inner Link](#clickable-row-with-an-inner-link)
- [Measure the block, not the window](#measure-the-block-not-the-window)
- [Clear Softr's sticky bars](#clear-softrs-sticky-bars)
- [A modal above Softr's bars](#a-modal-above-softrs-bars)

## Cross-Page State with localStorage + URL Parameters

When a block needs to remember user state across pages (currently selected record, last filter, last viewed dashboard), `localStorage` works inside Vibe Coding blocks just like in any browser context. Pair with a URL parameter so deep links also work:

```jsx
import { useState, useEffect } from "react";

export default function Block() {
  var fromUrl = new URLSearchParams(window.location.search).get("eventId");
  var saved = localStorage.getItem("softr_myapp_selected_event_id");
  var initialId = fromUrl || saved || null;

  var [selectedId, setSelectedId] = useState(initialId);

  useEffect(function() {
    if (selectedId) {
      localStorage.setItem("softr_myapp_selected_event_id", selectedId);
    }
  }, [selectedId]);

  /* ... rest of block ... */
}
```

Why both:

- **`localStorage`** survives page navigation and refresh. Depending on the browser, it may also survive logout.
- **URL parameter** makes the state shareable -- a user can paste a link and the destination page lands on the same record.
- **URL wins** over localStorage so explicit links override stored state.

### Namespacing

Always namespace your keys: `softr_<app>_<resource>_<key>`. Without a namespace, two Vibe Coding blocks on the same domain can stomp on each other's state:

```jsx
/* Good */
localStorage.setItem("softr_acme_pursuits_filter", JSON.stringify(filter));

/* Bad -- collides with anything else using "filter" */
localStorage.setItem("filter", JSON.stringify(filter));
```

### Clearing on logout

If state should NOT survive logout (e.g. it references record IDs the next user shouldn't see), clear it explicitly when the user signs out, or scope keys to the current user's email:

```jsx
var currentUser = useCurrentUser();
var key = "softr_myapp_selected_event_" + ((currentUser && currentUser.email) || "anon");
```

## Clipboard Copy Button

Standard browser `navigator.clipboard.writeText` works inside Vibe Coding blocks. Softr-published apps run on HTTPS, which is the only requirement for the Clipboard API, so no fallback is needed.

```jsx
import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

function CopyButton(props) {
  var [copied, setCopied] = useState(false);

  function handleClick() {
    navigator.clipboard.writeText(props.value).then(function() {
      setCopied(true);
      toast.success("Copied " + (props.label || "value"));
      setTimeout(function() { setCopied(false); }, 1500);
    });
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={handleClick}
      aria-label={"Copy " + (props.label || "value")}
    >
      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
    </Button>
  );
}
```

Usage:

```jsx
<CopyButton value={record.fields.invoiceUrl} label="invoice URL" />
<CopyButton value={getFieldValue(record.fields.email)} label="email" />
```

The `aria-label` is required because the button has no visible text, only an icon. Without it the button is not screen-reader accessible.

## Navigation Blocker for Unsaved Changes

Softr apps use SPA-mode client-side navigation — when a user clicks a link in Softr's nav bar, sidebar, or any `<NavigationAction>`, the route changes without a full page reload. The browser's standard `beforeunload` event only fires for tab close / refresh / browser back-forward / external nav, so the classic dirty-form warning misses every internal Softr click.

Softr's `useNavigationBlocker` hook intercepts BOTH internal SPA navigation AND browser-level unload with a single API. Import it from `@/lib/use-navigation-blocker`.

**Boolean form — simplest case:**

```jsx
import { useState } from "react";
import { useNavigationBlocker } from "@/lib/use-navigation-blocker";

export default function Block() {
  var [isDirty, setIsDirty] = useState(false);

  useNavigationBlocker(isDirty);

  function handleFieldChange(newValue) {
    setIsDirty(true);
    /* ... update form state ... */
  }

  /* ... form rendering ... */
}
```

**Callback form — when you need to read a ref without re-running on every render:**

```jsx
import { useRef } from "react";
import { useNavigationBlocker } from "@/lib/use-navigation-blocker";

export default function Block() {
  var dirtyRef = useRef(false);

  useNavigationBlocker(function() { return dirtyRef.current; });

  function handleFieldChange() {
    dirtyRef.current = true;
    /* ... update local state without re-rendering the hook ... */
  }

  /* ... rest ... */
}
```

The hook automatically handles:

- Browser's "Leave site?" dialog on tab close / refresh / external nav.
- Softr's in-app confirmation modal when the user clicks an internal Softr link or `<NavigationAction>`.
- Letting navigation through if the user confirms; cancelling if they decline.

**Most form blocks don't need to wire this manually** — Softr's Vibe Coding bundler often adds the blocker automatically when it detects form dirty state. You only need to add it explicitly for advanced cases:

- Multi-step forms where the dirty state spans several panels.
- Manual dirty tracking that doesn't go through standard form-state hooks.
- Blocks where you want to block on something other than form dirtiness (e.g., a pending background upload).

**Asking Softr to add the blocker automatically:** when generating or refining a form block in the Vibe Coding editor, you can prompt with "Block the navigation when the form is dirty" and Softr will wire `useNavigationBlocker` for you — useful when you don't want to write the import + hook call yourself.

## Scroll-Condensing Fixed Header (Landing-Page Hero)

For block-owned landing headers (see [static-blocks.md](static-blocks.md#block-owned-landing-page-header) for when this pattern applies and its caveat set): the header starts tall and transparent, then condenses to a translucent, blurred bar once the page scrolls. Verified pattern from Studio-AI output, 2026-08-31 (renders live; scroll behavior consistent with window-scrolled Softr pages).

```tsx
import { useState, useEffect } from "react";

export default function Block() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll(); // sync immediately — Softr is a SPA, so the block can mount with a restored scroll offset
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 transition-all duration-300 ${
        scrolled
          ? "py-3 bg-[#FAF5EC]/85 backdrop-blur-md border-b border-[#E7DECD]"
          : "py-6 bg-transparent border-b border-transparent"
      }`}
    >
      {/* logo / nav / CTA */}
    </header>
  );
}
```

Notes:

- **The initial `onScroll()` call matters** — without it, a block mounting mid-page (SPA back-navigation with restored scroll) renders the transparent state over content.
- **No throttle/rAF needed** — the handler sets a boolean; React skips re-renders when the value doesn't change.
- **`backdrop-blur-md` works across the shadow-DOM boundary**: `backdrop-filter` operates on the composited backdrop (everything painted beneath the element in the viewport), so a block's translucent fixed header blurs other blocks' content scrolling under it. Requirements: the element needs a semi-transparent background for the blur to be visible, and `backdrop-filter` must sit on the fixed element itself — on an ancestor it creates a containing block that would re-anchor the fixed header. (Compositing claim is standard CSS; the blurred-over-content visual on a published Softr page is inferred, not screenshot-proven.)
- This translucent-blur bar is a deliberate, single-surface exception to the anti-glassmorphism taste rule in ui-ux-guidelines.md — don't extend the treatment to cards/panels.
- **Fixed-position fragility**: `position: fixed` anchors to the viewport only while no ancestor has a `transform`/`filter`/`perspective`/`will-change`. Keep those off the block root and the header's ancestors, and verify in the published app, not just the Studio canvas.

## Auth-Aware Header CTA

A landing header's "Sign in" button should swap for a logged-in destination. `useCurrentUser()` returns `null` when logged out (documented in [../datasources/reading.md](../datasources/reading.md)); verify whether it has a transient loading state before adding flicker handling — the docs only document `null`.

```tsx
import { useCurrentUser } from "@/lib/user";
import { NavigationAction } from "@/components/navigation-action";
import { Button } from "@/components/ui/button";

// signInLink, dashboardLink: two useNavigationSetting hooks so both destinations stay builder-editable
const user = useCurrentUser();

<Button asChild>
  {user ? (
    <NavigationAction navigation={dashboardLink}>Dashboard</NavigationAction>
  ) : (
    <NavigationAction navigation={signInLink}>Sign in</NavigationAction>
  )}
</Button>
```

Default label is "Sign in" (the ui-ux-guidelines.md glossary term), not "Log in". This is the default for any block-owned landing header with a login button — Studio AI omits the swap; add it.

## Edge-Fade Image Mask (Editorial Hero)

Fade a photo's edges into the block background (no hard rectangle) with multiple gradient masks — one linear-gradient per edge to fade — combined by intersection. Renders fine inside the block's shadow DOM (verified from Studio output, 2026-08-31).

```tsx
// Module scope. Left edge fades into the background; bottom edge fades so the photo doesn't butt the block edge.
const photoMask = {
  WebkitMaskImage:
    "linear-gradient(to right, rgba(0,0,0,0) 0%, rgba(0,0,0,0.35) 6%, rgba(0,0,0,1) 18%), linear-gradient(to bottom, rgba(0,0,0,1) 84%, rgba(0,0,0,0) 100%)",
  WebkitMaskComposite: "source-in",
  maskImage:
    "linear-gradient(to right, rgba(0,0,0,0) 0%, rgba(0,0,0,0.35) 6%, rgba(0,0,0,1) 18%), linear-gradient(to bottom, rgba(0,0,0,1) 84%, rgba(0,0,0,0) 100%)",
  maskComposite: "intersect",
};

<div className="absolute top-0 right-0 h-[92%] w-[58%]" style={photoMask}>
  <img src={image.src} alt={image.alt} className="w-full h-full object-cover object-[62%_25%]" />
</div>
```

**The trap: the two composite properties take DIFFERENT keyword vocabularies.** `-webkit-mask-composite` uses Porter-Duff names (`source-in`), standard `mask-composite` uses `intersect`. Setting only one property, or using the wrong vocabulary, silently loses the fade in one browser family — always set both, with each one's own keyword. Pairs naturally with `object-cover` + arbitrary `object-[x%_y%]` for the crop.

## Decorative Background Blobs (Editorial Layering)

Large soft shapes behind hero content. Three load-bearing gotchas, then the recipe:

1. **`overflow-hidden` on the block root** — negatively-offset off-canvas shapes otherwise create horizontal scroll (this operationalizes ui-ux-guidelines.md §21's no-horizontal-overflow rule).
2. **`pointer-events-none` on every decorative layer** — so they never intercept clicks on content.
3. **vw sizing paired with px max-caps** — shapes scale with the viewport but don't balloon on ultrawide.

```tsx
<div className="relative overflow-hidden ...">
  {/* decoration: z-0 */}
  <div className="pointer-events-none absolute -top-[22%] -right-[10%] w-[62vw] h-[62vw] max-w-[900px] max-h-[900px] rounded-full bg-[#AE5E3D] z-0" />
  {/* art layer (e.g. masked photo): z-[1] */}
  {/* content: z-10 */}
  <main className="relative z-10 ...">...</main>
</div>
```

The z-0 / z-[1] / z-10 stack is block-internal layering — it complements (does not replace) the overlay z-scale in ui-ux-guidelines.md §7.

## Dot-Separated Inline List

Certifications, feature tags, meta rows: `GMP Manufacturing ● ISO 22716 ● Low MOQs`. Render separators LEADING (never trailing), keep the two gap values identical, and hide the glyphs from screen readers:

```tsx
<div className="flex flex-wrap items-center gap-x-8 gap-y-3">
  {items.map((item, index) => (
    <span key={index} className="flex items-center gap-x-8">
      {index > 0 && <span aria-hidden="true" className="text-[7px] text-muted-foreground leading-none">●</span>}
      <span>{item.label}</span>
    </span>
  ))}
</div>
```

- **Two gap declarations, deliberately equal** — the container's `gap-x-8` spaces item→item, the item span's `gap-x-8` spaces dot→label; symmetry depends on the two values matching, so keep them identical (hoist to a shared constant if you touch them often). The real fix over Studio AI's emitted shape is the **leading**-separator guard (`index > 0`): Studio puts a trailing dot inside each item, which dangles alone at the end of a wrapped line, and its two gap values match only by accident.
- **Keep `gap-y-*`** on the container for multi-line rhythm when the list wraps.
- **If the list is expected to wrap often**, drop the dots and let the gap carry the rhythm — any inline separator looks orphaned at a line break.
- `aria-hidden="true"` on the glyph — screen readers announce `●` as "black circle" otherwise.


## Drag-to-Reorder Rows

Reordering a list by dragging, written against a Softr block's constraints. Four of the five decisions
below are non-obvious, and each one is a bug if you get it wrong.

```jsx
var [drag, setDrag] = useState(null);            // { from, over } while dragging, else null
var [optimisticOrder, setOptimisticOrder] = useState(null);  // ids, post-drop, pre-refetch
var rowElsRef = useRef([]);

/* The pointer is CAPTURED, so no other element receives enter/leave — rects are the only
   thing that can answer "what is under the cursor". Compare against each row's MIDPOINT so
   the row you are over is the one that yields. */
function dropIndex(count, clientY) {
  for (var i = 0; i < count; i++) {
    var el = rowElsRef.current[i];
    if (!el) continue;
    var r = el.getBoundingClientRect();
    if (clientY < r.top + r.height / 2) return i;
  }
  return count - 1;
}
```

The handle — never the whole row, so text selection and the row's own buttons keep working:

```jsx
<span
  role="button"
  aria-label={"Drag to reorder " + row.name}
  className="touch-none select-none"          // or the browser scrolls instead of dragging
  style={{ cursor: "grab" }}
  onPointerDown={function (e) {
    e.preventDefault();
    try { e.currentTarget.setPointerCapture(e.pointerId); } catch (err) {}
    setDrag({ from: index, over: index });
  }}
  onPointerMove={function (e) {
    if (!drag) return;
    var over = dropIndex(rows.length, e.clientY);
    if (over !== drag.over) setDrag({ from: drag.from, over: over });
  }}
  onPointerUp={function () {
    if (!drag) return;
    var from = drag.from, to = drag.over;
    setDrag(null);
    if (from !== to) {
      var next = rows.slice();
      next.splice(to, 0, next.splice(from, 1)[0]);
      applyOrder(next);
    }
  }}
  onPointerCancel={function () { setDrag(null); }}
>
  <GripVertical className="h-3.5 w-3.5" />
</span>
```

**Pointer capture, not mouse events.** Capture makes the handle the target of every move and of the up
*wherever the pointer travels*, and obliges the browser to send `pointercancel` if it takes the pointer
away. Without it, a drag released over another application never delivers its up and the row stays
stuck mid-drag until a reload.

**Measure rects, don't listen for `onPointerEnter` on each row.** While the pointer is captured, no
other element gets enter/leave at all, so per-row handlers silently never fire. And
`document.elementFromPoint` is not the escape hatch — inside a block it returns the shadow host (see
[anti-patterns.md](anti-patterns.md#layout--styling)).

**Draw the insertion line with an INSET box-shadow, never a border.** A real 2px border grows the row
by 2px and shoves every row below it down a notch, so the list crawls under the pointer as the target
changes:

```jsx
style={Object.assign({}, ROW_STYLE, isTarget
  ? (drag.over < drag.from
      ? { boxShadow: "inset 0 2px 0 0 " + ACCENT }     // landing above
      : { boxShadow: "inset 0 -2px 0 0 " + ACCENT })   // landing below
  : null)}
```

**Renumber the whole run — never swap a pair.** A swap cannot express "drop three rows up", and on a
nullable order field it corrupts the sort: positions start null, so numbering only the two rows that
moved leaves the rest null, and any "nulls last" comparator then throws every untouched row to the
bottom the moment the user switches to that sort. Write `position = i + 1` for every row whose slot
actually changed. The first reorder on a fresh list costs N writes; later ones cost the distance
travelled.

**Hold an optimistic order until the refetch lands.** The position writes are in flight while the
records still carry their OLD numbers, so re-sorting on those throws the row back to where it was
dragged from for a beat — which reads as the drag having failed. Apply `optimisticOrder` ahead of both
sorts and clear it when the refetch resolves. Writes stay sequential (`await mutateAsync` per row, in
order, stop on first failure — see [../datasources/writing.md](../datasources/writing.md#sequential-multi-row-writes-mutateasync));
on failure, clear the override and refetch, because a half-applied renumber is worse than none.

**Only gate the drag on permissions, not on a sort mode.** If the list has an alternative sort, let the
drag switch to manual order rather than disabling the handle — see the disabled-control note in
[../ui-ux-guidelines.md](../ui-ux-guidelines.md#26-finishing-touches).

## Create → open

When the user creates a record they are about to work on — a new item, a new saved list — land them on it. They made it in order to fill it in, so closing the dialog back into the list and leaving them to find the row they just made is a step nobody asked for. Leo, 2026-09-10: "when you create a new item anywhere in the interface, once it's created, you need to open the item details page of the item you just created … when you create a new list, once it's created, you need to open this list details, as you'll likely want to fill the list straight after."

`useRecordCreate`'s `onSuccess` receives the created record, but the wrapper around its id has moved before. Read it defensively — a miss is survivable, a crash is not:

```jsx
/* What useRecordCreate hands onSuccess is the created record. The exact wrapper has moved
   before, so read the id defensively — a miss is survivable (the row still gets created and
   the list still refetches, the user just picks it) but a crash is not. */
function getCreatedId(created) {
  if (!created) return "";
  if (typeof created === "string") return created;
  if (created.id) return String(created.id);
  if (created.recordId) return String(created.recordId);
  if (created.record && created.record.id) return String(created.record.id);
  if (created.data && created.data.id) return String(created.data.id);
  return "";
}
```

Then navigate on success — and only when there is an id to navigate to:

```jsx
createItem.mutate(payload, {
  onSuccess: function (created) {
    setBusy(false);
    var id = getCreatedId(created);
    if (id) {
      window.location.href = "/item?recordId=" + encodeURIComponent(id);
      return;
    }
    // The record exists; we just can't address it. Stay put, refetch, say so.
    setOpen(false);
    itemsResult.refetch();
    toast.success('"' + name + '" created — it is in the list below.');
  },
  onError: function () {
    setBusy(false);
  },
});
```

**Never navigate with an empty id.** `/item?recordId=` would render the detail page's own "record not found" state, and the user would conclude the create failed when it did not. The fallback keeps them where the new row will appear once the refetch lands.

**Keep the path relative.** `/item?recordId=…`, never the app's domain — the same block runs on the preview URL and on the custom domain (SKILL.md's no-hardcoded-domains rule).

**Where the id comes from is not always where it goes.** For an `onCreate` inside a Combo — a vendor typed into a picker — the created id is patched into the form and the user keeps editing; there is nothing to open. See [searchable-dropdown.md](searchable-dropdown.md#variants-worth-having). Navigation is for records that have their own page and that the user will work on next.

## Clickable Row with an Inner Link

An index table exists to get the user into a record, so the hit area is the whole row. But a row is not a link: cmd-click, middle-click, right-click → "Copy link" and hover-to-see-the-URL all come from a real `<a>`. Keep both — the row handler for the plain click, an anchor on the name for everything the browser does with anchors — and make sure they do not fight:

```jsx
function ProjectRow(props) {
  var row = props.row;
  var href = "/project?recordId=" + encodeURIComponent(row.id);

  // The row handler bows out the moment a modifier is held — those clicks belong to the
  // anchor (new tab, new window, select).
  function openRow(event) {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (typeof window !== "undefined") window.location.href = href;
  }

  return (
    <TableRow className="cursor-pointer hover:bg-[#FFF7EF]" onClick={openRow}>
      <TableCell>
        <a
          href={href}
          className="hover:underline"
          onClick={function (e) {
            e.stopPropagation(); // the anchor navigates itself; without this the row handler ALSO fires
          }}
        >
          {row.name}
        </a>
      </TableCell>
      {/* … */}
    </TableRow>
  );
}
```

Two things go wrong without the two guards. Without `stopPropagation` on the anchor, a cmd-click on the name opens the new tab AND navigates the current one, because the row handler runs too. Without the modifier check on the row, a cmd-click on the cell padding (next to the anchor, not on it) navigates the current tab — the opposite of what the user asked for.

Any *other* control inside the row — an inline status chip, a checkbox, a menu — needs `stopPropagation` on its own handler as well, or every click on it opens the record. (The drag handle in [Drag-to-Reorder Rows](#drag-to-reorder-rows) already does this.)

### Keyboard picker over the same rows

Where a table has a quick-find box, wire it like a picker so the keyboard alone gets into a record: the box takes focus, ↑ ↓ move a highlight, Enter opens the highlighted row, Escape clears the query (and the highlight with it).

```jsx
var [active, setActive] = useState(0);
// Filtering shrinks the list under the highlight, so clamp rather than index past the end.
var activeIdx = rows.length === 0 ? 0 : Math.min(active, rows.length - 1);

function onKeyDown(e) {
  if (e.key === "ArrowDown" || e.key === "ArrowUp") {
    e.preventDefault();
    var step = e.key === "ArrowDown" ? 1 : -1;
    setActive(function (a) {
      return Math.min(Math.max(a + step, 0), Math.max(rows.length - 1, 0));
    });
  } else if (e.key === "Enter") {
    e.preventDefault();
    var hit = rows[activeIdx];
    if (hit) window.location.href = "/project?recordId=" + encodeURIComponent(hit.id);
  } else if (e.key === "Escape") {
    e.preventDefault();
    setQuery("");
    setActive(0);
  }
}

<input autoFocus value={query} onChange={function (e) { setQuery(e.target.value); setActive(0); }} onKeyDown={onKeyDown} … />
```

Make the rows themselves focusable too (`tabIndex={0}`, an `onKeyDown` that opens on Enter only when `event.target === event.currentTarget`, so an Enter on the anchor inside the row is not handled twice), and let `onMouseEnter` *and* `onFocus` both move the highlight onto the row — the highlight is the single answer to "which record does Enter open", whichever device last touched it. That is the shape `projects-table.jsx` shipped on 2026-09-10.

Paint the highlighted row with the same colour the mouse hover gets (`data-active="true"` + `bg-[#FFF7EF]`) and scroll it into view when it moves (`querySelector('[data-active="true"]').scrollIntoView({ block: "nearest" })` in a `useEffect` on `activeIdx`). That is right here, because these rows are page content and the table's scroller and the page *should* move to them. On a page with Softr's top bar, a row scrolled in from above the window can land under the bar: give the rows a `scroll-margin-top` or scroll the window yourself, as in [Clear Softr's sticky bars](#clear-softrs-sticky-bars). Inside a dropdown it is wrong, and the Combo scrolls only its own list — see [searchable-dropdown.md](searchable-dropdown.md#the-four-things-that-will-bite-you), item 4, rule 3. Reset `active` to 0 whenever the query changes: the old index points at a row that may no longer be in the list. `autoFocus` is right only when the block *is* the page's reason to exist — an index page whose first act is always a search; on a page with content above the table, a focus steal scrolls the page to the box.

## Measure the block, not the window

Beside Softr's sidebar navigation, the window over-reports the block's width by the width of the sidebar: 280px by default, 57px collapsed, 200 to 360px when dragged. Lay the block out by its own width. CSS container queries do most of it (`@container` on a wrapper, `@min-[NNrem]:` on what is inside it; see [ui-ux-guidelines.md → Breakpoint strategy](../ui-ux-guidelines.md#breakpoint-strategy)), so reach for CSS first. When a decision can't be made in CSS, measure the block in JS. Typical cases: rendering a different tree (list and detail side by side, or a phone flow with its own back control), or choosing how many chart ticks to draw.

```tsx
import { useLayoutEffect, useRef, useState } from "react";

// Module scope, like any hook or component. The block's own width: the space Softr gives it.
function useElementWidth(ref: { current: HTMLElement | null }) {
  const [width, setWidth] = useState<number>(() => (typeof window !== "undefined" ? window.innerWidth : 1200));
  // useLayoutEffect, not useEffect: measured before the first paint, so no frame is laid out at the window's width.
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const update = () => setWidth(el.getBoundingClientRect().width);
    update();
    if (typeof ResizeObserver === "undefined") {
      window.addEventListener("resize", update);
      return () => window.removeEventListener("resize", update);
    }
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return width;
}

export default function Block() {
  const rootRef = useRef<HTMLDivElement>(null);
  const width = useElementWidth(rootRef);
  const wide = width >= 860; // 340px list + 20px gap + at least 440px of detail + padding
  return (
    <div ref={rootRef} className="@container">
      {wide ? <ListAndDetail /> : <PhoneFlow />}
    </div>
  );
}
```

- **`useLayoutEffect`, not `useEffect`.** A passive `useEffect` runs after the browser paints, so the first frame is laid out with the initial guess: the window's width. Beside a sidebar that guess is out by up to 360px, and the layout visibly flips. At a 1200px window with a 360px sidebar the block is 840px, but the first frame would paint the two-column skeleton and then switch to one column. `useLayoutEffect` measures and re-renders before the first paint. (A code-review finding, 2026-10-05; the fix shipped in two blocks.)
- **Put the ref on the block's outer wrapper, and render that wrapper in every state, loading included.** The effect runs once, so a ref that attaches only after the data loads is never observed. Measure the wrapper, not an element whose width depends on the decision the width drives.
- **Keep padding off the `@container` element** when CSS and JS both switch on width. Container queries read its content box and `getBoundingClientRect()` reads its border box. With no padding or border they are the same number, so `@min-[860px]:` and `width >= 860` agree.
- The window `resize` listener is only the fallback for a browser without `ResizeObserver`. The observer also sees what a resize event never reports: the sidebar collapsing or being dragged while the window stays the same size.
- Thresholds one app uses: a chart labels every other month below a 640px block, and list and detail sit side by side from an 860px block.

## Clear Softr's sticky bars

On a page with Softr navigation, Softr's bars live in the main document, outside the block, and the page scrolls under them (measured live 2026-10-05):

| Bar | Shows at | Element | Height | Position |
|---|---|---|---|---|
| Top bar | a window of 768px and up | `#topbar-root` | 56px | sticky, top 0, z-index 800 |
| Phone tab bar | a window below 768px | `#bottombar-root` | 57px rendered (`#bottombar-root` and its `ul` both measured 57px; Softr's variable says 55px) | sticky in the page grid's bottom row (not `fixed`), z-index 800 |

The block host hands their sizes to block CSS. `--nav-height` is 56px with the top bar; on phones Softr leaves its own variable empty and the host's fallback gives 0px. `--bottombar-height` is `calc(0px + 55px)` on phones (2px short of the rendered bar) and 0px otherwise. `--sidebar-width` is 280px with the sidebar open, 57px collapsed and 0px on phones. The host maps them from Softr's `:root` variables `--sticky-nav-height`, `--softr-bottombar-height` and `--softr-sidebar-width`, each with a `0px` fallback (all measured live 2026-10-05). The variable table is in [quick-reference.md → Softr navigation variables](quick-reference.md#softr-navigation-variables); the whole page layout is in [native-chrome-styling.md → App frame (navigation layout)](native-chrome-styling.md#app-frame-navigation-layout).

**Sticky elements inside a block.** A `sticky top-4` slides under the top bar. Offset it by the bar, and cap a sticky pane so its foot stays on screen:

```tsx
<section
  className="sticky flex flex-col"
  style={{
    top: "calc(var(--nav-height, 0px) + 16px)",
    maxHeight: "calc(100dvh - var(--nav-height, 0px) - 32px)", // 16px of air above and below
  }}
>
```

Measured live 2026-10-05 in the preview at a 1440px window: the pane's top sat at 72px (56 + 16). The mirror image for a phone, `bottom: calc(var(--bottombar-height, 0px) + 16px)`, is untested.

**Scripted window scrolls and room checks.** JS sees the window, not the bars. Code that scrolls the window to bring something into view, or asks whether a popover has room above or below, must take the top bar (56px) off the top edge and, on phones, the tab bar (57px as rendered) off the bottom edge. Softr switches its navigation on the window width, so here the window is the right thing to test:

```tsx
const TOP_BAR = 56; // Softr's sticky top bar, window 768px and up
const TAB_BAR = 57; // Softr's phone tab bar, window below 768px: measured 57px; --softr-bottombar-height says 55px
const AIR = 16;

// The strip of the window that Softr's bars leave visible.
function visibleStrip() {
  const phone = window.innerWidth < 768; // 767px = tab bar, 768px = top bar + sidebar
  return {
    top: (phone ? 0 : TOP_BAR) + AIR,
    bottom: window.innerHeight - (phone ? TAB_BAR : 0) - AIR,
  };
}

function keepInView(el: HTMLElement) {
  const { top, bottom } = visibleStrip();
  const r = el.getBoundingClientRect();
  if (r.top < top) window.scrollBy(0, r.top - top);
  else if (r.bottom > bottom) window.scrollBy(0, r.bottom - bottom);
}

// It issues a window scroll, so call it as setTimeout(() => keepInView(el), 0) (Hard Constraint 17).
```

The project this comes from hard-coded 72px (a bar plus 16px) at the top, and at the bottom wherever a tab bar could be. That number is a project choice; subtracting the bars is the rule. `visibleStrip` generalises it and is untested as written. A confirm strip that opens below a row, or a drop-up test, uses the same strip in place of `0` and `window.innerHeight`. For the dropdown, see [searchable-dropdown.md → rule 2](searchable-dropdown.md#the-four-things-that-will-bite-you).

**Read the host variables only inside CSS `calc()`.** They are unregistered custom properties, so in JS `getComputedStyle(el).getPropertyValue(...)` returns the token that was set, not a length. `--nav-height` reads `56px` on desktop, but `--bottombar-height` reads `calc(0px + 55px)` on phones (both measured live 2026-10-05). `parseFloat` turns that into `NaN` (inferred, not run in a block), and a `|| 0` fallback would then scroll content under the tab bar without a sound. In CSS both forms work. In JS, use the bar heights above.

**Fragment jumps are offset; inner scrolls are not.** Softr's page CSS gives every block's outer wrapper (`div[data-block]`, with a page-assigned id such as `ai1`; the Vibe host sits two levels inside it) `#main-content [data-block] { scroll-margin-top: var(--sticky-nav-height, 0px) }` (the rule was read from Softr's live page CSS on 2026-10-05; the jump itself is untested), so a URL fragment that targets that wrapper lands below the top bar. Nothing offsets a scroll to an element *inside* the block: `scrollIntoView` on a row or a section can put it at the window's top edge, under the bar. Give the target `scroll-margin-top: calc(var(--nav-height, 0px) + 16px)`, which `scrollIntoView` honours (untested in a block), or scroll the window with `keepInView`. A fragment can't reach inside the shadow root in the first place; see [static-blocks.md → Section anchors](static-blocks.md#section-anchors-on-landing-pages).

## A modal above Softr's bars

On an app page with Softr's navigation, shadcn's `Dialog` and `Sheet` don't work cleanly. Two things go wrong:

- **It sits under the top bar.** shadcn's overlay is `z-50`; Softr's sticky `#topbar-root` is z-index 800. The top bar stays undimmed and clickable, and a tall modal slides under it. Measured live 2026-10-06 in the preview at 1440×900 with the top bar and sidebar: a `position: fixed` layer inside a block's shadow root at z-index 50 lost to the top bar (`document.elementFromPoint` inside the bar returned the bar); at z-index 801 and at 1000 the same layer covered the top bar and the sidebar. A walk up from the block host to `<html>` found no stacking context (every ancestor static / `auto`, no `transform`, `contain` or `container-type`), so a block's z-index competes directly with Softr's bars.
- **It leaves the shadow root.** Radix portals the dialog to `document.body`, outside the block's shadow root, and the block's styles stay behind — the same reason shadcn `<Select>` is out ([searchable-dropdown.md](searchable-dropdown.md)).

Render the modal in the block's own DOM instead. This is the reusable core of the record modal that shipped in the Partner Spotlight review block on 2026-10-06:

```tsx
import { useEffect, useRef } from "react";
import { X } from "lucide-react";

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), textarea:not([disabled]), video[controls], [tabindex]:not([tabindex="-1"])';

// Module scope. onDismiss must itself refuse while a save runs (Escape and the backdrop call it too).
function InBlockModal({ labelledBy, describedBy, onDismiss, dismissDisabled, children }: {
  labelledBy: string; describedBy?: string; onDismiss: () => void; dismissDisabled?: boolean; children: React.ReactNode;
}) {
  const panelRef = useRef<HTMLDivElement | null>(null);
  const dismissRef = useRef(onDismiss); // the latest handler; the listener is attached once per opening
  dismissRef.current = onDismiss;

  useEffect(() => {
    const panel = panelRef.current;
    // Inside a shadow root document.activeElement is the block's host; the root knows the real element.
    const root: any = panel ? panel.getRootNode() : document;
    const opener = (root.activeElement as HTMLElement | null) || null;

    // Lock the page behind the modal; the stable gutter stops a sideways jump where scrollbars take space.
    const html = document.documentElement;
    const prevOverflow = html.style.overflow;
    const prevGutter = html.style.getPropertyValue("scrollbar-gutter");
    html.style.overflow = "hidden";
    html.style.setProperty("scrollbar-gutter", "stable");
    const focusTimer = window.setTimeout(() => panel?.focus({ preventScroll: true }), 0);

    const onKey = (e: KeyboardEvent) => {
      if (e.defaultPrevented || e.isComposing) return;
      if (e.key === "Escape") { e.preventDefault(); dismissRef.current(); return; }
      if (e.key !== "Tab" || !panel) return;
      // Visible controls only: getClientRects() is empty for anything display: none.
      const items = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE)).filter((el) => el.getClientRects().length > 0);
      if (!items.length) { e.preventDefault(); panel.focus(); return; }
      const current = root.activeElement as HTMLElement | null;
      const inside = !!current && current !== panel && panel.contains(current);
      const first = items[0], last = items[items.length - 1];
      if (e.shiftKey && (!inside || current === first)) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && (!inside || current === last)) { e.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKey);

    return () => {
      window.clearTimeout(focusTimer);
      document.removeEventListener("keydown", onKey);
      html.style.overflow = prevOverflow;
      if (prevGutter) html.style.setProperty("scrollbar-gutter", prevGutter);
      else html.style.removeProperty("scrollbar-gutter");
      if (opener && opener !== panel && opener.isConnected) opener.focus({ preventScroll: true });
    };
  }, []);

  return (
    // z-[1000]: above Softr's top bar, sidebar and phone tab bar (all z-index 800 or below).
    <div className="fixed inset-0 z-[1000] flex items-center justify-center p-2 sm:p-6">
      <div aria-hidden="true" className="absolute inset-0 bg-gray-950/50" onClick={() => dismissRef.current()} />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        aria-describedby={describedBy}
        tabIndex={-1}
        className="@container relative flex max-h-full w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl outline-none"
      >
        {children}
        <button
          type="button"
          onClick={() => dismissRef.current()}
          disabled={dismissDisabled}
          aria-label="Close"
          className="absolute right-3 top-3 rounded-lg p-2 text-gray-500 hover:bg-gray-100 disabled:pointer-events-none disabled:opacity-40"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

export default function Block() {
  // ... state, `active` record, `saving`, a `close` that returns early while saving ...
  return (
    <>
      <div className="@container">{/* the block's page */}</div>
      {/* A sibling of the @container wrapper, not a child of it. */}
      {active && (
        <InBlockModal labelledBy="modal-title" describedBy="modal-desc" onDismiss={close} dismissDisabled={saving}>
          {/* header with id="modal-title" / id="modal-desc"; give it right padding (pr-12) for the X */}
          {/* a scrolling body: min-h-0 flex-1 overflow-y-auto */}
        </InBlockModal>
      )}
    </>
  );
}
```

- **Outside the block's `@container` wrapper.** `@container` sets `container-type: inline-size`, which brings layout containment, and containment on an ancestor can capture `position: fixed` (it becomes the fixed box's containing block). Render the modal as a sibling of that wrapper, then put `@container` on the panel so everything inside it sizes by the panel. The overlay itself is fixed to the window, so its own padding may use `sm:`.
- **z-index 1000, not 50.** Anything from 801 up clears the bars; 1000 leaves room. It also keeps Softr's links out of reach while an edit is open.
- **Focus lives in the shadow root.** Read the focused element from `panel.getRootNode().activeElement`; `document.activeElement` is only the block's host. The opener is captured on open, and focus goes back to it on close if it is still on the page.
- **Saving.** Disable the X while a save runs, and make the dismiss handler return early while saving, because Escape and the backdrop call the same handler. In the shipped block that handler also asks before discarding unsaved edits.
- **Scroll lock on `<html>`**, not `body`: the page scroller is the document. Restore both properties exactly as they were.
- The shipped component also has `animate-in fade-in-0 zoom-in-95` on the panel and `backdrop-blur-[2px]` on the backdrop.

**Status (2026-10-06).** Verified live, harness: the shipped component's exact source was bundled with `deno bundle` and mounted into a shadow root under `#main-content` on the live preview page, rendered with Softr's own React 18.2 (`window.__softr_React` / `window.__softr_ReactDOM`), 1440×900 window with top bar and sidebar. Passed: opens with focus on the panel; covers the top bar and the sidebar; the panel centres at 896px; Tab and Shift+Tab wrap both ways and skip hidden controls; Escape and the X do nothing while saving; Escape, the backdrop and the X close it; `overflow` and `scrollbar-gutter` are restored; focus returns to the opener. **Not yet seen:** the full review block opening the modal with real data — there was no Social Media Manager member to preview as. The trimmed version above was not run on its own. Phones (tab bar) untested.

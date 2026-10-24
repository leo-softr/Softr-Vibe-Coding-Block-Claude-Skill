# Common Patterns

Small reusable patterns that come up across Vibe Coding blocks but don't warrant their own reference file. Each is a copy-pasteable snippet. The first three snippets use legacy var-style (`var`, `function() {}`), which remains valid; the newer patterns use modern TS — both compile (see SKILL.md Style Conventions).

**Browser environment note.** Vibe blocks render in a shadow root in the MAIN document — not an iframe (except on a page Softr opens in a Modal, which loads in a same-origin iframe (read from Softr's bundles 2026-10-09, not yet run live): [modal-pages.md](modal-pages.md)<!-- LIVE-CHECK: the iframe claim is read from Softr's bundles 2026-10-09; resolve with the modal-pages.md live check -->) — so window-level APIs behave normally from block code: `window.scrollY` reflects the real page scroll, window-level events (scroll, resize, keydown) fire, `localStorage`/`navigator.clipboard`/`window.history` all work. Standard `useEffect` add/remove-listener with cleanup is the right shape for event-driven UI; use `{ passive: true }` for scroll/touch listeners. (SKILL.md Hard Constraint 17's `setTimeout` rule applies to ISSUING programmatic scrolls only, not to listening.)

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
- [Inline confirm in place of a button](#inline-confirm-in-place-of-a-button)
- [Signatures: draw in a popup, upload a PNG](#signatures-draw-in-a-popup-upload-a-png)
- [A form open while its record changes](#a-form-open-while-its-record-changes)
- [Drafts that survive a reload](#drafts-that-survive-a-reload)
- [CSV export](#csv-export)

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

### A search in the URL

Keep a list's search in the URL (`?q=`) so Back and a reload bring it back. Write it with `replaceState` inside try/catch, and pass the current state through:

```jsx
try { window.history.replaceState(window.history.state, "", url); } catch (e) {}
```

Softr's page renderer wraps `pushState` and `replaceState` (read from the renderer's source): it throws on a state that is not an object, and it stamps its own `__histIdx` into the state. Passing `history.state` keeps that index; `null` loses it. With this, going back from a record returned to `?q=…` with the results showing, and a reload kept the search (QA pass, 2026-10-08).

Softr's link handling acts only when the click lands on the link element itself. A link in a block's shadow root that wraps other elements (a card, an icon beside text) therefore mostly causes a full page load instead of an in-app navigation, and Back then restores the URL the block last wrote with `replaceState`.

**What goes in the URL goes to Softr's server.** Every save request carries the page URL and its parameters (`context.pageURL`, `context.URLParameter`), so personal data in a parameter is a decision to record, not a side effect. A blocked save on a page with `?q=<surname>` carried the surname in both fields.

### A preference that follows the user

A preference that should follow the user across devices (a dashboard layout) lives in a table, one row per user per view. Keep a `localStorage` copy only to avoid a jump while the row loads. A `where` on the email is not access control: without a Source condition on `{USER:::EMAIL}`, any logged-in user can read every row, and whether that condition also stops updates to other users' rows is untested. One app shipped its layout table without the condition, and a QA pass found that any login could overwrite another user's row (2026-10-07).

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
- Softr's in-app prompt when the user clicks an internal Softr link or `<NavigationAction>`. It is a native `window.confirm`, not a styled Softr modal.
- Letting navigation through if the user confirms; cancelling if they decline.

**Measured live** (five form blocks switched to the hook, 2026-10-08):

- **The prompt is a native `window.confirm`**: "You have unsaved changes that will be lost if you navigate away from this page. Do you want to continue?" It fires on sidebar links, on the phone tab bar and on in-app Back and Forward. A reload shows the browser's own `beforeunload` prompt instead. A clean form prompts for nothing.
- **A form dialog hides the links.** A modal with a fixed full-screen backdrop (the in-block pattern in [A modal above Softr's bars](#a-modal-above-softrs-bars), `z-[1000]`) covers the sidebar and the phone tab bar, so while one is open the user cannot reach them. The blocker matters for forms that sit on the page itself, and for Back and Forward.
- **A link that calls `history.back()` itself** (a "Back to list" link) on a page opened by a full page load leaves the app's history, so the blocker may not catch it. Test such links separately.
- To test the prompt in a headless browser, see [browser-checks.md → Gotchas](browser-checks.md#gotchas): agent-browser answers this confirm and the reload prompt by itself, so a click that navigates proves nothing until you have recorded that the dialog appeared.

**Wire it yourself in every form block, and see it fire in the preview.** Don't count on Softr's bundler to add the blocker. A form block pushed through the MCP had none: after typing rows, a click on a sidebar link left the page with no prompt, and none of that app's 15 block sources called the hook (QA pass, 2026-10-08; observed from a source grep and one live block, so it is a report of what we saw, not a statement about the bundler). Test it: make the form dirty, click a sidebar link, expect the prompt. The hook was later wired into five form blocks of that app by hand and exercised live on 2026-10-08 (see "Measured live" above); see it fire in yours before relying on it. It matters most for:

- Multi-step forms where the dirty state spans several panels.
- Manual dirty tracking that doesn't go through standard form-state hooks.
- Blocks where you want to block on something other than form dirtiness (e.g., a pending background upload).

The blocker only asks. Rows the user chooses to throw away anyway are gone, so a long entry form also wants [a draft that survives a reload](#drafts-that-survive-a-reload).

**One dirty rule for both guards.** A dialog that asks "discard your changes?" on its own Cancel and a leave-page guard on the same form should read the same dirty check, so they never disagree: [ui-ux-guidelines.md §15](../ui-ux-guidelines.md#15-error-prevention-and-destructive-actions).

**Asking Softr to add the blocker:** the bundler did not add it to a block pushed through the MCP, so wire it yourself. In Studio's own editor, prompting "Block the navigation when the form is dirty" may write the import and the hook call for you (untested here, as no block went through that route). Check that it fires either way.

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

### New from a search with no results

A New button on a search that found nothing opens the form prefilled from the query: digits go to the phone, and both "Last, First" and "First Last" go to the name fields (that order is what made the search miss). Compare the form's unsaved-changes check against the prefilled draft, not against an empty one, or Cancel asks to discard text nobody typed. A duplicate check before the create says why each match matched and ranks strong reasons above a weak substring match: a household's second parent was not flagged as a duplicate until it matched on the other caregiver and the address (QA pass, 2026-10-08).

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
- **When JS must agree exactly with a CSS container breakpoint** (the page size of a table that turns into a stacked list at that breakpoint), don't redo the rem math in JS and don't read the window's width. Render a zero-size probe that carries the breakpoint's own classes under the same `@container`, and read whether it is displayed:

  ```tsx
  // Module scope. The probe shows exactly when the table shows, so JS and CSS cannot disagree.
  function useTableMode() {
    const [probe, setProbe] = useState<HTMLElement | null>(null);   // state, not a ref: see below
    const [tableMode, setTableMode] = useState(false);
    useLayoutEffect(() => {
      if (!probe || !probe.parentElement) return;
      const read = () => setTableMode(probe.getClientRects().length > 0);  // display: none has none
      read();
      const ro = new ResizeObserver(read);
      ro.observe(probe.parentElement);
      return () => ro.disconnect();
    }, [probe]);
    return { tableMode, probeRef: setProbe };
  }
  // In the JSX, inside the @container wrapper:
  // <span ref={probeRef} aria-hidden="true" className="pointer-events-none absolute hidden h-0 w-0 @min-[48rem]:block" />
  ```

  If the probe mounts only after loading, hold it as state (`ref={setProbe}`) and key the effect on it: a ref with `[]` deps never sees it, and a plain `useEffect` paints 50 rows first. In a harness the page size matched the CSS switch exactly at 767 and 768px (QA round 2, 2026-10-08). Key a table/stack switch on the content card's own `@container`, not on the block's width: a log table keyed on the block's 47rem still overflowed in its 650px card.
- The window `resize` listener is only the fallback for a browser without `ResizeObserver`. The observer also sees what a resize event never reports: the sidebar collapsing or being dragged while the window stays the same size.
- Thresholds one app uses: a chart labels every other month below a 640px block, and list and detail sit side by side from an 860px block.

## Clear Softr's sticky bars

On a page with Softr navigation, Softr's bars live in the main document, outside the block, and the page scrolls under them (measured live 2026-10-05):

| Bar | Shows at | Element | Height | Position |
|---|---|---|---|---|
| Top bar | a window of 768px and up, in an app that has one | `#topbar-root` | 56px | sticky, top 0, z-index 800 |
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
const TOP_BAR = 56; // Softr's sticky top bar, window 768px and up; 0 in an app with no top bar (see below)
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
  // behavior: "instant": the Softr page sets html { scroll-behavior: smooth }, see below.
  if (r.top < top) window.scrollBy({ top: r.top - top, behavior: "instant" });
  else if (r.bottom > bottom) window.scrollBy({ top: r.bottom - bottom, behavior: "instant" });
}

// It issues a window scroll, so call it as setTimeout(() => keepInView(el), 0) (Hard Constraint 17).
```

**An app with no top bar.** When the menu lives in the sidebar and Softr shows no top bar on desktop, `--nav-height` is `0px` and `TOP_BAR` is 0, or every scripted scroll holds content 56px lower than it needs to. Set the constant per app, or test the main document for the bar: `document.querySelector(".softr-topbar") ? 56 : 0` (the selector is the one the header CSS scopes on; reading it from block code is untested). Why that layout has no bar: [native-chrome-styling.md → Caveats](native-chrome-styling.md#caveats).

**Scroll with `behavior: "instant"`.** Softr sets `html { scroll-behavior: smooth }` in the preview (and the published app's login page), so a plain `scrollBy` animates. A second scroll issued before the first lands replaces its target, and a measure right after the call reads a position mid-scroll: in one check, repeated `scrollBy` calls netted +26px instead of +135. `keepInView` calls once, so the risk is in code that scrolls again or measures straight after it. A test harness without that CSS rule passes the broken code, so copy the app's `scroll-behavior` into the harness (QA pass, 2026-10-08). Outside a dialog, prefer `keepInView` to bring a Retry button into view. If you do call `scrollIntoView` on it, pass `block: "center"` and `behavior: "instant"`, because `"nearest"` leaves it at the bottom edge, under a toast or the phone tab bar. Inside a dialog, set the body's `scrollTop` instead, or call `scrollBy({ top, behavior: "instant" })` if the box itself has smooth scrolling ([Failures, focus and Escape](#failures-focus-and-escape)).

The project this comes from hard-coded 72px (a bar plus 16px) at the top, and at the bottom wherever a tab bar could be. That number is a project choice; subtracting the bars is the rule. `visibleStrip` generalises it and is untested as written. A confirm strip that opens below a row, or a drop-up test, uses the same strip in place of `0` and `window.innerHeight`. For the dropdown, see [searchable-dropdown.md → rule 2](searchable-dropdown.md#the-four-things-that-will-bite-you).

**Read the host variables only inside CSS `calc()`.** They are unregistered custom properties, so in JS `getComputedStyle(el).getPropertyValue(...)` returns the token that was set, not a length. `--nav-height` reads `56px` on desktop, but `--bottombar-height` reads `calc(0px + 55px)` on phones (both measured live 2026-10-05). `parseFloat` turns that into `NaN` (inferred, not run in a block), and a `|| 0` fallback would then scroll content under the tab bar without a sound. In CSS both forms work. In JS, use the bar heights above.

**Fragment jumps are offset; inner scrolls are not.** Softr's page CSS gives every block's outer wrapper (`div[data-block]`, with a page-assigned id such as `ai1`; the Vibe host sits two levels inside it) `#main-content [data-block] { scroll-margin-top: var(--sticky-nav-height, 0px) }` (the rule was read from Softr's live page CSS on 2026-10-05; the jump itself is untested), so a URL fragment that targets that wrapper lands below the top bar. Nothing offsets a scroll to an element *inside* the block: `scrollIntoView` on a row or a section can put it at the window's top edge, under the bar. Give the target `scroll-margin-top: calc(var(--nav-height, 0px) + 16px)`, which `scrollIntoView` honours (untested in a block), or scroll the window with `keepInView`. A fragment can't reach inside the shadow root in the first place; see [static-blocks.md → Section anchors](static-blocks.md#section-anchors-on-landing-pages).

## A modal above Softr's bars

**This modal opens from the block's own UI** (a button, a row, an event the block listens for). To open a block from Softr's navigation, give the block a page of its own and open that page in a Softr Modal instead: Studio's Open page picker lists pages only (seen in Studio 2026-10-09), so an Open page item cannot point at a hash or an in-block popup (whether Studio's Open URL field takes a relative `/page#hash` was not tried; over MCP, `application_navigation_set_items` takes one per its description, and whether it then opens the popup was not tried). The MCP's Open page item takes a page id, so it cannot carry a hash either. See [modal-pages.md](modal-pages.md).

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
function InBlockModal({ labelledBy, describedBy, onDismiss, dismissDisabled, returnFocusTo, returnFocusFallback, children }: {
  labelledBy: string; describedBy?: string; onDismiss: () => void; dismissDisabled?: boolean;
  returnFocusTo?: HTMLElement | null; returnFocusFallback?: string; children: React.ReactNode;
}) {
  const panelRef = useRef<HTMLDivElement | null>(null);
  const dismissRef = useRef(onDismiss); // the latest handler; the listener is attached once per opening
  dismissRef.current = onDismiss;

  useEffect(() => {
    const panel = panelRef.current;
    // Inside a shadow root document.activeElement is the block's host; the root knows the real element.
    const root: any = panel ? panel.getRootNode() : document;
    // The opener is handed in by the caller (the clicked button, kept in a ref at click): Safari and macOS
    // Firefox do not focus a clicked button, so root.activeElement can be anything when the dialog opens.
    const opener = returnFocusTo || (root.activeElement as HTMLElement | null) || null;

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
      // The opener, or (a dialog restored at page load has none; the opener left the list) a stable
      // tabIndex={-1} target found by selector in the root captured at open: the panel is gone by now.
      const target = opener && opener !== panel && opener.isConnected
        ? opener
        : (returnFocusFallback ? root.querySelector?.(returnFocusFallback) as HTMLElement | null : null);
      target?.focus({ preventScroll: true });
    };
  }, []);

  return (
    // z-[1000]: above Softr's top bar, sidebar and phone tab bar (all z-index 800 or below).
    <div className="fixed inset-0 z-[1000] flex items-center justify-center p-2 sm:p-6">
      {/* preventDefault on pointerdown: pressing the backdrop would move focus to <body> before the click lands. */}
      <div aria-hidden="true" className="absolute inset-0 bg-gray-950/50" onPointerDown={(e) => e.preventDefault()} onClick={() => dismissRef.current()} />
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
  // ... state, `active` record, `saving`, the opener (event.currentTarget kept in a ref at click),
  //     a `close` that returns early while saving ...
  return (
    <>
      <div className="@container">{/* the block's page */}</div>
      {/* A sibling of the @container wrapper, not a child of it. */}
      {active && (
        <InBlockModal labelledBy="modal-title" describedBy="modal-desc" onDismiss={close} dismissDisabled={saving} returnFocusTo={openerRef.current} returnFocusFallback="#page-title">
          {/* header with id="modal-title" / id="modal-desc"; give it right padding (`pl-* pr-14`) for the X */}
          {/* a scrolling body: min-h-0 flex-1 overflow-y-auto */}
        </InBlockModal>
      )}
    </>
  );
}
```

- **Outside the block's `@container` wrapper.** `@container` sets `container-type: inline-size`, which brings layout containment, and containment on an ancestor can capture `position: fixed` (it becomes the fixed box's containing block). Render the modal as a sibling of that wrapper, then put `@container` on the panel so everything inside it sizes by the panel. The overlay itself is fixed to the window, so its own padding may use `sm:`.
- **z-index 1000, not 50.** Anything from 801 up clears the bars; 1000 leaves room. It also keeps Softr's links out of reach while an edit is open.
- **Focus lives in the shadow root.** Read the focused element from `panel.getRootNode().activeElement`; `document.activeElement` is only the block's host. Focus goes back to the opener on close if it is still on the page. The caller hands the opener in as `returnFocusTo` (the clicked button, kept in a ref at click) and the component falls back to the root's `activeElement` at open, because Safari and macOS Firefox do not focus a clicked button. When there may be no opener, see [Failures, focus and Escape](#failures-focus-and-escape).
- **Saving.** Disable the X while a save runs, and make the dismiss handler return early while saving, because Escape and the backdrop call the same handler. In the shipped block that handler also asks before discarding unsaved edits.
- **Scroll lock on `<html>`**, not `body`: the page scroller is the document. Restore both properties exactly as they were.
- The shipped component also has `animate-in fade-in-0 zoom-in-95` on the panel and `backdrop-blur-[2px]` on the backdrop.

**Status (2026-10-06).** Verified live, harness: the shipped component's exact source was bundled with `deno bundle` and mounted into a shadow root under `#main-content` on the live preview page, rendered with Softr's own React 18.2 (`window.__softr_React` / `window.__softr_ReactDOM`), 1440×900 window with top bar and sidebar. Passed: opens with focus on the panel; covers the top bar and the sidebar; the panel centres at 896px; Tab and Shift+Tab wrap both ways and skip hidden controls; Escape and the X do nothing while saving; Escape, the backdrop and the X close it; `overflow` and `scrollbar-gutter` are restored; focus returns to the opener. **Not yet seen:** the full review block opening the modal with real data — there was no Social Media Manager member to preview as. The trimmed version above was not run on its own. Phones (tab bar) untested.

### Failures, focus and Escape

What a QA pass of 15 app blocks found in dialogs like this one (2026-10-08): dialogs that could not be closed after a failed save, errors hidden below the fold (21px under it at 1280×800), focus lost to `<body>`, and a page that scrolled from 345 to 880px behind an open dialog.

- **Pass the opener in explicitly** (`returnFocusTo` above). Safari and macOS Firefox don't focus a clicked button, so `root.activeElement` at open is not the opener, and focus was lost on close in Firefox until the caller handed the button over.
- **Give it a fallback target when there may be no opener.** A dialog restored at page load (a draft) mounts with nothing focused, and an opener that can leave the list (a row that drops out after the save) is gone at close. Pass a selector for a stable `tabIndex={-1}` element (`returnFocusFallback` above) and look it up in the root captured at open: after cleanup, `getRootNode()` no longer finds it.
- **`preventDefault` on the backdrop's `pointerdown`.** Pressing the mouse on a backdrop moves focus to `<body>` before the click lands, and every close path after that loses focus.
- **Lock only while a request is in flight.** After a failure Close works again and keeps what was typed. A dialog the user cannot leave is a trap; the same applies to a form locked after a failed step (see [writing.md → Sequential Multi-Row Writes](../datasources/writing.md#sequential-multi-row-writes-mutateasync)).
- **Put the error in a `role="alert"` well and reveal it by setting the body's `scrollTop`**, re-run whenever the error list changes. Not `scrollIntoView`: it also scrolls the locked page. A harness check "the error is inside the dialog" passed while the error sat below the fold, so compare the error's rect with the scroller's edges.
- **Page-level scroll and focus effects skip while an `[aria-modal]` dialog is open.** An effect that scrolls or focuses on an async failure otherwise moves the page behind the dialog and lets `focus()` out of the trap.
- **After a failure, return focus to the action button** unless focus is already in a field. A submit button disabled while saving drops focus to `<body>`. If the clicked control was removed (Retry, Start over), focus the first `:not(:disabled)` control after `setTimeout(…, 0)`, so a fieldset unlocked in the same click is already enabled, from a root captured at open.
- **A Retry leaves the page when the retry starts, not only when it succeeds.** A Retry inside `{failed && …}` unmounts as soon as the retry begins, and focus falls to `<body>` while the request runs. Give focus a landing place that stays mounted (the main action button), and when the retry fails again, move focus back to the Retry that reappears. If the landing place is disabled at that moment, see the next point.
- **A target that is natively `disabled` cannot take focus, so `focus()` in the click handler does nothing.** It happens when the main action is disabled while the failure hint shows and the control the user presses is the Retry beside it. Two ways out. Set a flag (a ref) in the handler and move focus from an effect keyed on the busy state, which runs after the render that made the target focusable. Or render the target `aria-disabled` instead of `disabled`: it stays focusable, takes its dimmed look from `aria-disabled:` classes, and its handler must return early while busy, because `aria-disabled` does not stop a click. `aria-disabled` cannot help a Retry that unmounts: that one needs the landing place above.
- **In review, list every `disabled=` that is still tied to a busy or failed state** (a main action, a Try again in an error well, a Discard on a restored-draft note) and put each in the focus test: press it, then [record where focus goes over time](browser-checks.md#4-measuring-with-eval) instead of reading it once.
- **A control that unmounts on its own success drops focus to `<body>`.** Discard on a restored-draft note, Set active on an Inactive banner, a paging button on the last page: move focus to a stable, always-mounted target first. For a dismissed note, reuse the form's focus-first-control call (`setTimeout(…, 0)`, through a ref in the shadow root, not `document.getElementById`). For a paging button, keep the footer and make it a `tabIndex={-1}` paragraph ("All N shown") that takes the focus.
- **Escape closes only the innermost layer**: an open list, a calendar, an inline question, then the dialog. Each inner layer calls `preventDefault` + `stopPropagation`; the modal's listener returns on `defaultPrevented`.
- **Inside a shadcn/Radix `Dialog` that rule needs one more guard.** (The in-block modal is the default on pages with Softr's navigation, see [A modal above Softr's bars](#a-modal-above-softrs-bars); this is for a block that does use shadcn's `Dialog`.) Radix hears Escape on `document` in the capture phase, before any handler inside the dialog runs (its escape hook adds the keydown listener with `{ capture: true }`, read from `@radix-ui/react-use-escape-keydown` 1.x, 2026-10-16), so a Combo's or calendar's own `preventDefault` + `stopPropagation` cannot stop it: Escape with a list open closed the whole dialog and lost what was typed. Keep a registry of the open panels (a module-scope Set that the Combo adds itself to on open and leaves on close) and give `DialogContent` an `onEscapeKeyDown` that calls `event.preventDefault()` while the registry is not empty. One Escape then closes the newest panel, and the next closes the dialog. Seen failing, then fixed, on a report form with 8 pickers: 14 checks in its New and Edit dialogs passed after the guard (QA pass, 2026-10-08). The same guard added to a second dialog was checked in code only (2026-10-16).
- **A shadcn `Dialog` opened from a button in a block cannot give focus back by itself.** It has no `DialogTrigger`, so on close Radix focuses the element that was active when it opened (`document.activeElement`, read from `@radix-ui/react-focus-scope` 1.x); inside a shadow root that is the block's host element, which cannot take focus, and focus lands on `<body>`. Remember the opener when the dialog opens (a ref set in the click handler) and pass `onCloseAutoFocus={(event) => { event.preventDefault(); openerRef.current?.focus(); }}` to `DialogContent`. When the opener was a menu item that closes with its menu, hand over the menu's button. Seen live on a project header's dialogs (QA pass, 2026-10-16): Escape on Rename and Escape or Cancel on Add item returned focus to the control that opened them; Archive uses the same code and was not run.
- **Don't render the dialog as `open && !loadError`.** A background read that fails while it is open would unmount it. Keep an open dialog mounted whatever a read does.
- **Room for the X at every breakpoint**: set the header's sides separately (`pl-* pr-14`), because `px-*` at a breakpoint overrides `pr-*` ([anti-patterns.md](anti-patterns.md#layout--styling)).

The opener and focus-return changes were checked in a harness in Chromium and in Firefox (27 checks passing in both). The sketch's `returnFocusFallback` writes out what the app did with an element id, and was not run as written; nor has the full set of rules above been run together in one trimmed component. The retry rules (the landing place, and the flag-and-effect fix for a natively `disabled` target) were checked by rendering a block's own code in jsdom, before and after the fix (2026-10-15), not in a live browser: before the fix, focus fell to `<body>` during the retry and after a retry that succeeded; after it, focus sat on the main action, went back to the Retry on a new failure and stayed on the main action after a success. The `aria-disabled` route was not run in jsdom.

## Inline confirm in place of a button

When a click needs one more question ("Log anyway?", "Set inactive?"), the question can take the place of the button under the pointer instead of opening a second dialog. It is quick, and it is one click from a write, so it needs guards. These came out of a QA pass over 15 blocks (2026-10-08):

- **Ignore taps for about 400ms after it appears.** A double click on Save otherwise lands on the question and answers it unread. With the guard, a double click 12ms apart sent no write.
- **Remount it for each question** (`key={text}`), and make `text` carry the values it asked about, so changing a field asks again. Without the remount, a double click on the confirm button answered the next question unread.
- **Move focus to the safe answer with refs.** React reuses the focused button's DOM node, so focus lands on the new action. Check the shadow root's `activeElement` (`panel.getRootNode().activeElement`) after Enter, not after a mouse click (a click moves focus to the button it hit in Chromium).
- **Escape closes only the question** and returns focus to the footer. Inside a dialog it must not go on to the "discard your changes?" question ([Failures, focus and Escape](#failures-focus-and-escape)).
- **The action behind it returns its error** instead of toasting it, so the question can show it in place. It is not dropped by a "one at a time" guard (another row's save in flight silently dropped a confirmed Set inactive), and it swallows a failed re-read after a good write, or a retry writes a second change-log row ([anti-patterns.md](anti-patterns.md#mutations)).
- **A handler wired as `onClick={fn}` with an optional "confirmed" flag** gets the click event as that flag ([anti-patterns.md](anti-patterns.md#hooks--react)).
- **Ask only in the direction that takes something away.** Set inactive asks; Set active acts at once ([ui-ux-guidelines.md §15](../ui-ux-guidelines.md#15-error-prevention-and-destructive-actions)).

The arming guard, as a sketch of the mechanism (not a copy of a shipped component):

```tsx
// Module scope. Mount it as <ConfirmStrip key={text} … />, so each question is a fresh instance.
function ConfirmStrip({ text, safeLabel, actionLabel, onSafe, onAction }: {
  text: string; safeLabel: string; actionLabel: string; onSafe: () => void; onAction: () => void;
}) {
  const mountedAt = useRef(Date.now());
  const safeRef = useRef<HTMLButtonElement | null>(null);
  useEffect(() => { safeRef.current?.focus({ preventScroll: true }); }, []);   // the safe answer, by ref
  const armed = () => Date.now() - mountedAt.current > 400;                   // a double click lands inside this
  return (
    <div role="alert">
      <p>{text}</p>
      <button type="button" ref={safeRef} onClick={() => armed() && onSafe()}>{safeLabel}</button>
      <button type="button" onClick={() => armed() && onAction()}>{actionLabel}</button>
    </div>
  );
}
```

## Signatures: draw in a popup, upload a PNG

The default way to ask a person for a signature in a block [house]. An **Add signature** button opens a popup with a drawing box. The person signs with a finger, a stylus or the mouse, and the form keeps the drawing as a preview. On Send the block saves the drawing twice: as plain text (the path) and as a PNG in an ATTACHMENT field, uploaded with `useUpload`. A typed name is the fallback for people who cannot draw, not the main way.

Use it for anything a person signs in a block: an application, an agreement, a waiver, a report, a delivery receipt. A tick box that says "I agree" is not a signature and needs none of this. Whether a drawing or a typed name is enough for a given document is the form owner's call, not the pattern's.

**Status.** The upload facts below were measured live on 2026-10-23. The popup, the preview and the send were built to this list and run the same day in a draft preview in Chromium, with a mouse and the keyboard: no failed checks; one minor (the note sat under the Type the name instead link) was fixed in a later push. Touch and stylus input, backdrop presses on the popup, Firefox and WebKit were not run. The code at the end is a trimmed, generic version of that block. Run in node on 2026-10-24, its path functions gave the same results as the shipped ones on 20,000 generated drawings and 200,000 malformed strings, and the whole skeleton passed an esbuild syntax check. The picture function, the pad, the popup and the field were not run as written: there was no canvas or browser in that check.

If a second block shows or prints the signature (a staff inbox, a printout), keep the path functions in a shared kit between marker lines, so the block that writes the path and the block that reads it cannot disagree: [date-picker.md → The kit between markers](date-picker.md#the-kit-between-markers).

### What the person sees

- **Add signature is the main control.** A full-width button, 44px tall, with a pen icon. The shipped form drew it outlined (its secondary style), which keeps Send the one filled button on the page. A note under it, "Press Add signature, then sign with your finger, a stylus or the mouse.", shows only while nothing is saved. Put the note directly under the button and above the next control; a note slot that sat below the "Type the name instead" link read as the link's note. Link each note to its control with `aria-describedby`, and the error too.
- **"Type the name instead" is a small link under it,** for anyone who cannot draw. A pad takes a pointer, so keyboard and screen-reader users need this way. The note under the name box says what a typed name counts as ("A typed name counts as a signature." was the shipped line; the owner decides whether that is true for the document). A link back reads "Draw the signature instead". Keep both halves when the person switches way and send only the half that is showing. After the swap, put focus on the name box or on the link back, because the control that had it is gone.
- **The popup is the in-block modal** of [A modal above Softr's bars](#a-modal-above-softrs-bars), never shadcn's `Dialog`: `fixed inset-0 z-[1000]`, a sibling of the block's `@container` wrapper, with its own focus trap, scroll lock, Escape and focus return to the opener. Inside it:
  - **A title, the box and three buttons:** **Clear**, **Cancel** and **Save signature**. Save signature is disabled until there is ink.
  - **Strokes stay local until Save signature.** The draft lives in a hook above the form, so Cancel leaves the answers as they were and nothing is uploaded.
  - **Unsaved ink asks first.** When the draft differs from the saved drawing, Cancel, Escape and the backdrop swap the buttons for an inline question, "Discard this drawing?", with **Keep drawing** (the safe answer, which takes focus) and **Discard** ([Inline confirm in place of a button](#inline-confirm-in-place-of-a-button)). While it shows, Escape gives the safe answer. When it closes, send focus to Cancel, or it falls to `<body>`. A draft with no unsaved ink closes at once.
  - **A backdrop press closes the popup only if the press began on the backdrop.** Otherwise a stroke that starts in the box and runs off its edge ends on the backdrop and throws the drawing away. Record `pointerdown` on the backdrop in a ref and reset it from `onPointerDownCapture` on the panel.
  - **The box** is an SVG with `viewBox="0 0 600 200"` (3:1), full width up to 600px. It uses pointer events with `setPointerCapture`, and `touch-action: none` on the box only, so drawing never scrolls the page. A pointer position becomes a point through the box's own `getBoundingClientRect`, so the picture scales with the block. It reads `getCoalescedEvents()` where the browser has it. One stroke at a time: a second pointer (a palm beside a pen) never takes over a live stroke. A tap draws a dot. "Sign here" and a baseline show while the box is empty, and `role="img"` carries a label that says whether it is empty or signed. When the checked path holds 1,999 points or more (it can stop one short, because a dot takes two) the box says "The box is full. Press Clear to start again."
  - **A narrow block fills the width.** The popup is outside the `@container` wrapper, so a container query cannot see the block's width: [measure it](#measure-the-block-not-the-window). Below 480px the popup fills the width with a 16px gutter and a line under the box says "Tip: turn your phone sideways for more room." Keep Clear, Cancel and Save signature as the same three DOM nodes in the narrow and the wide layout (put the layout classes on the buttons, not on extra wrappers), so focus on them survives a phone being turned sideways.
  - **Focus goes back to the opener.** Save signature replaces Add signature with the preview, so the opener is gone by then. Give Add signature and Change the same `id` and pass `#id` as `returnFocusFallback`.
- **A saved drawing shows as a preview with Change and Remove.** A bordered box holding an SVG drawn from the checked path (never the raw stored text). **Change** reopens the popup with the saved drawing as the draft. **Remove** asks "Remove the signature?" with an inline confirm (Keep, Remove) and sends focus to Add signature afterwards. A saved drawing, a typed name and an open popup with unsaved ink all count as dirty for `useNavigationBlocker`.
- **Required, and not too short.** A drawing needs at least 8 points and a box at least 24 units wide or tall: "The signature is too short. Please sign again." A typed name needs 2 or more characters. The message for no signature names the button: "Please press Add signature and sign, or choose Type the name instead." The error summary's jump link focuses the Add signature button (or Change), the control that carries the question's `id`.

### Saving it

- **Check the path first.** The pad hands up strokes (lists of `[x, y]` points in the 600 by 200 box). Clamp each point into the box, round it to a whole number, drop a point closer than 1.5 units to the one before it, and stop at 2,000 points. The result is path text with only `M` and `L`: `M12 140L14 138M50 100L51 101`. A stroke of one point is written twice, so it draws a dot.
- **Upload on Send, never on Save signature.** A form that is never sent uploads nothing, and a person who redraws three times uploads once. A typed name uploads nothing.
- **Draw it again off screen.** Make the PNG from the checked path (read back through the tokenizer, not the raw string) on an off-screen 600 by 200 canvas: white background, the preview's stroke (3 wide, round caps and joins, a one-point stroke as a dot). `canvas.toBlob(cb, "image/png")` is asynchronous, so await it, and wrap the blob in a `File`. A hand-drawn signature came out at 6 to 8 KB.
- **`uploadAsync(file)` with a time limit.** The upload is app-level: no `from`. Race it against a 20 second timer. Only a result with `status === "completed"` and an `https://` url counts. Call it on the hook object (`upload.uploadAsync(file)`), never detached; [writing.md](../datasources/writing.md#actions-register-per-table-not-per-hook-or-connection) has the same rule for `mutateAsync`.
- **The create carries `{ filename, url }`** under the attachment field's alias, flat, like any [attachment write](../datasources/writing.md#attachment). Without a file there is no key at all.
- **A failed upload never stops the send.** No canvas, no `File`, `toBlob` giving nothing, a refused or failed result, a timeout, a throw: every one is a null, the create goes without the file, and the visitor sees no error. The drawing is in the text copy anyway. (A timed-out upload may still finish and leave a file nothing refers to; inferred, not seen.)
- **Keep the path as text in the same create,** in a text column or in the JSON column that holds the answers: `{"kind":"drawn","d":"M12 140L14 138…"}`, or `{"kind":"typed","name":"…"}`. Three reasons. The upload is a second request and can fail where the create does not. A printout, an export or another block can draw the path with no network wait, sharper, and it never expires (a link read from the row works for 2 hours; read the row again for a new one). And the drawing survives if the attachment field is not mapped. If an earlier version stored the typed name as a plain string, read a plain string as typed.
- **The button text says what is happening:** "Saving your signature…" while the picture is made and uploaded, then "Sending…". The double-submit guard (a ref set before the first `await`) covers the whole Send, upload included ([writing.md](../datasources/writing.md#sequential-multi-row-writes-mutateasync)).
- **Reuse the file when Send is pressed again.** Keep `{ path, file }` in a ref. If the create failed after the upload and the person presses Send again with the same drawing, send the file that is already uploaded instead of uploading twice. Forget it once the answers are wiped.
- **Map the file field, and read the action back.** The attachment field's alias must be in the create's `q.select`. `useUpload` adds no action of its own: the file rides on the block's ADD action. After a push, read that action back and check the file field is among its mapped fields (verified live 2026-10-23: the action read before the push, from the build without the field, did not map it; after the push of the build whose create select had it, the action mapped 20 fields, the file field among them). Every push resets actions (Hard Constraint 21).

### Reading it back safely

- **A stored path is text a crafted request could have written,** so read it with a **linear tokenizer**: one pass over the characters, no regex (nested quantifiers can hang). Accept only `M`, `L`, digits and spaces. Each command has exactly two numbers of 1 to 3 digits, every coordinate is inside the box (0 to 600 across, 0 to 200 down), and the path has at most 2,000 points and 24,000 characters. Anything else is `null`.
- **Render only from the parsed numbers.** As a React `<path d={…}>` where `d` is written out again from the parsed points, or as markup you build from those numbers (a printout, see [printing.md](printing.md)). Never put the stored string into markup, an attribute or `dangerouslySetInnerHTML`.
- **Showing the uploaded PNG in another block:** read the row each time, because the link is signed for a limited time (2 hours by default, see below) and must not be copied anywhere. Render an `<img>` only for an `https://` address, with `referrerPolicy="no-referrer"` and a real `alt`, because a public ADD action lets a crafted request write any link into the field (house rule, from that reasoning). If there is no link, or the image fails to load, draw the path instead. The shipped staff view showed the image on screen (the path when the image failed); the form's own printout drew the path. The read shape is in [fields.md → Attachment thumbnails](../datasources/fields.md#attachment-thumbnails).
- **A typed signature has no file.** Show the name and "(typed)".

### What the upload does (measured 2026-10-23)

Verified live on 2026-10-23 on a Softr Database table, from a draft preview (signed in, and logged out with no user switched in) and, for the logged-out case, from a brand-new browser session with no cookies on the published domain:

- **The request.** `uploadAsync(file)` sends one XHR, not a `fetch`: `POST /v1/applications/<appId>/upload?file_name=<name>.png_<uuid>`, with FormData whose only part is `file`. It answers 200 with a plain URL (not JSON) on Softr's file host: `app-files-v1.softr-files.com/applications/<appId>/uploads/<uuid>/<name>.png`.
- **The create** then carries `{ filename, url }`.
- **Softr copies the file** into the table's own storage on create. Read back with `database_get_record`, the stored value is `{ id, url, filename, type: "image/png", size, thumbnails }`. The `id` looks like `attachments/<databaseId>/<tableId>/<recordId>/<fieldId>/<uuid>/<uuid>`. The `url` is not the one the block wrote: it is a signed S3 link that expires after **2 hours** (the field's link-expiry setting, 2 hours by default; [softr-mcp.md](softr-mcp.md#putting-files-into-attachment-fields)), and the thumbnails (small, medium, large) sit on CloudFront.
- **Logged out works.** Softr's docs do not say whether `useUpload` works for a visitor who is not signed in. It did: a drawn signature landed with its PNG signed in (6,295 B) and logged out (7,616 B) in the preview, and logged out from a fresh browser session on the published domain (7,711 B). In the preview the page saw no user and only the preview-version cookie.
- **It displays.** A reading block showed the stored image as an `<img>`, 600 by 200 natural size, loaded, with `referrerPolicy="no-referrer"`.
- **No action of its own.** The upload added nothing to the block's actions (see above).

### Testing it

- **A recorder for writes must wrap `XMLHttpRequest` as well as `fetch`.** The upload is an XHR and the create is a `fetch`. A recorder that wraps only `fetch` logs the create and misses the file. Install both before the first press, once per page load, and probe one call of each kind before trusting an empty log.
- **Block the upload path too.** The save guard in [browser-checks.md → Block saves before any click](browser-checks.md#6-block-saves-before-any-click-and-prove-it) routes `*records-trigger*` only. The upload goes to `/upload`, so a Send press that stops at the create can still put a file in Softr's storage. Block that path as well, and probe it.
- **Prove the logged-out case on your own app.** One marked test submission from a brand-new browser session with no cookies, on the published domain, then read the row back and compare `filename`, `type` and `size`. A preview with no user switched in is a cheap first check, but it may carry a Studio cookie the page cannot see, so it is not the same test.

### Skeleton

A trimmed, generic version of the shipped code. It builds on `InBlockModal` and `ConfirmStrip` from the two sections above and on `useElementWidth` from [Measure the block, not the window](#measure-the-block-not-the-window). Give `ConfirmStrip` the Escape handler its rules ask for (the sketch above leaves it out): `onKeyDown={(e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); onSafe(); } }}` on its wrapper, so the "Remove the signature?" question on the form has an Escape way out. First the path functions and the picture:

```tsx
import { useEffect, useRef, useState } from "react";
import { Pen } from "lucide-react";
import { datasource, q, useRecordCreate, useUpload } from "@/lib/datasource";

// ---- 1. The box, the path and the picture (module scope, plain functions) ----
const SIG_W = 600; // every drawing lives in one box, 600 by 200 units
const SIG_H = 200;
const SIG_MAX_POINTS = 2000;
const SIG_MAX_CHARS = 24000;
const SIG_THIN = 1.5; // a point closer than this to the one before it is dropped
const SIG_MIN_POINTS = 8; // fewer points, or under SIG_MIN_SPAN both ways, is "too short"
const SIG_MIN_SPAN = 24;
type Stroke = [number, number][];
type SigPad = { mode: "draw" | "type"; strokes: Stroke[]; name: string }; // the answer while the form is open

// Strokes as path text, no checks: "M12 140L14 138M50 100L51 101". A one-point stroke is written twice: a dot.
function sigWrite(strokes: Stroke[]): string {
  let d = "";
  for (const pts of strokes) (pts.length === 1 ? [pts[0], pts[0]] : pts).forEach((p, i) => (d += (i === 0 ? "M" : "L") + p[0] + " " + p[1]));
  return d;
}

// What the pad collected as path text: clamped into the box, rounded, thinned, capped. "" for nothing.
function sigPath(strokes: unknown): string {
  if (!Array.isArray(strokes)) return "";
  const kept: Stroke[] = [];
  let room = SIG_MAX_POINTS;
  for (let s = 0; s < strokes.length && room >= 2; s++) {
    if (!Array.isArray(strokes[s])) continue;
    const pts: Stroke = [];
    for (const p of strokes[s]) {
      if (!Array.isArray(p) || !Number.isFinite(p[0]) || !Number.isFinite(p[1])) continue;
      const x = Math.round(Math.min(SIG_W, Math.max(0, p[0])));
      const y = Math.round(Math.min(SIG_H, Math.max(0, p[1])));
      const last = pts[pts.length - 1];
      if (last && Math.hypot(x - last[0], y - last[1]) < SIG_THIN) continue;
      pts.push([x, y]);
      if (pts.length >= room) break;
    }
    if (pts.length === 0) continue;
    room -= pts.length === 1 ? 2 : pts.length;
    kept.push(pts);
  }
  return sigWrite(kept);
}

// Path text read back as { strokes, points, minX, minY, maxX, maxY }, or null when it is not a signature path. One pass over
// the characters, no regex. Only M, L, digits and spaces; each command has exactly two numbers of 1 to 3 digits, inside the box.
function sigParse(d: unknown) {
  if (typeof d !== "string" || d.length === 0 || d.length > SIG_MAX_CHARS || d.charAt(0) !== "M") return null;
  const strokes: Stroke[] = [];
  const nums: number[] = [];
  let cur: Stroke = [], cmd = "", tok = "", points = 0, minX = SIG_W, minY = SIG_H, maxX = 0, maxY = 0;
  for (let i = 0; i <= d.length; i++) {
    const ch = i < d.length ? d.charAt(i) : ""; // "" is the end: it closes the last command
    if (ch >= "0" && ch <= "9") { tok += ch; if (tok.length > 3) return null; continue; }
    if (tok !== "") { nums.push(Number(tok)); tok = ""; if (nums.length > 2) return null; }
    if (ch === " ") continue;
    if (cmd !== "") { // close the command before this one
      const [x, y] = nums;
      if (nums.length !== 2 || x > SIG_W || y > SIG_H || ++points > SIG_MAX_POINTS) return null;
      if (cmd === "M") strokes.push((cur = [[x, y]])); else cur.push([x, y]);
      minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y);
    }
    if (ch === "") break;
    if (ch !== "M" && ch !== "L") return null;
    cmd = ch;
    nums.length = 0;
  }
  for (const pts of strokes) if (pts.length === 1) { pts.push([pts[0][0], pts[0][1]]); points++; } // a one-point stroke comes back as two: a dot
  return points > SIG_MAX_POINTS ? null : { strokes, points, minX, minY, maxX, maxY };
}

// The path as the form keeps and shows it: parsed, then written out again from the numbers. "" when it does not parse.
function sigChecked(d: unknown): string {
  const info = sigParse(d);
  return info ? sigWrite(info.strokes) : "";
}

// null when the signature can be sent, else the sentence for under the question.
function sigProblem(pad: SigPad): string | null {
  if (pad.mode === "type") return pad.name.trim().length >= 2 ? null : "Type your full name.";
  const info = sigParse(sigPath(pad.strokes));
  if (!info) return "Please press Add signature and sign, or choose Type the name instead.";
  const wide = info.maxX - info.minX >= SIG_MIN_SPAN || info.maxY - info.minY >= SIG_MIN_SPAN;
  return info.points >= SIG_MIN_POINTS && wide ? null : "The signature is too short. Please sign again.";
}

// The picture: the checked path on an off-screen white canvas, as a PNG File. null when the browser cannot make one.
async function sigPngFile(d: string, fileName: string): Promise<File | null> {
  const info = sigParse(d); // from the checked numbers, never from the raw string
  if (!info || typeof File === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = SIG_W;
  canvas.height = SIG_H;
  const g = canvas.getContext("2d");
  if (!g) return null;
  g.fillStyle = "#ffffff";
  g.fillRect(0, 0, SIG_W, SIG_H);
  g.strokeStyle = "#1f2937"; // the preview's stroke: 3 wide, round
  g.fillStyle = "#1f2937";
  g.lineWidth = 3;
  g.lineCap = "round";
  g.lineJoin = "round";
  for (const pts of info.strokes) {
    g.beginPath();
    if (pts.length === 2 && pts[0][0] === pts[1][0] && pts[0][1] === pts[1][1]) { g.arc(pts[0][0], pts[0][1], 1.5, 0, Math.PI * 2); g.fill(); continue; } // a dot
    pts.forEach((p, i) => (i === 0 ? g.moveTo(p[0], p[1]) : g.lineTo(p[0], p[1])));
    g.stroke();
  }
  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/png"));
  return blob ? new File([blob], fileName, { type: "image/png" }) : null;
}
```

Three small changes to `InBlockModal`; everything else stays as in [its section](#a-modal-above-softrs-bars):

```tsx
// 1. Size comes from the caller: props `overlayClass` and `panelClass` replace the fixed "p-2 sm:p-6" and "max-w-4xl".
// 2. The X is optional: `showClose?: boolean`. Cancel is the way out of this popup.
// 3. A backdrop click counts only if its press began on the backdrop:
const downOnBackdrop = useRef(false);
//    backdrop:  onPointerDown={(e) => { e.preventDefault(); downOnBackdrop.current = true; }}
//               onClick={() => { if (!downOnBackdrop.current) return; downOnBackdrop.current = false; dismissRef.current(); }}
//    panel:     onPointerDownCapture={() => { downOnBackdrop.current = false; }}
```

The upload, and the draft that lives above the form:

```tsx
// ---- 2. The upload and the popup's state (module scope hooks) ----
const SIG_FILE = "signature.png";
const SIG_UPLOAD_MS = 20000; // the most Send waits for the picture to be made and uploaded
type Stored = { filename: string; url: string };

// Anything that goes wrong is a null, and the send goes on without the file.
function useSignatureUpload() {
  const upload = useUpload(); // app-level: no `from`
  const kept = useRef<{ d: string; file: Stored } | null>(null);
  async function store(d: string, busy: (on: boolean) => void): Promise<Stored | null> {
    if (kept.current && kept.current.d === d) return kept.current.file; // Send pressed again: reuse it
    busy(true);
    let timer = 0;
    try {
      const limit = new Promise<null>((resolve) => { timer = window.setTimeout(() => resolve(null), SIG_UPLOAD_MS); });
      const made = async (): Promise<any> => {
        try {
          const file = await sigPngFile(d, SIG_FILE);
          if (!file) return null;
          const out: any = await upload.uploadAsync(file); // on the hook object, never detached
          return Array.isArray(out) ? out[0] : out;
        } catch { return null; }
      };
      const res = await Promise.race([made(), limit]);
      if (!res || res.status !== "completed" || typeof res.url !== "string" || res.url.indexOf("https://") !== 0) return null;
      kept.current = { d, file: { filename: SIG_FILE, url: res.url } };
      return kept.current.file;
    } catch {
      return null;
    } finally {
      window.clearTimeout(timer);
      busy(false);
    }
  }
  return { store, forget: () => { kept.current = null; } };
}

// The draft lives here, above the form, so the answers change only on Save signature.
function useSigPopup(saved: Stroke[], onSave: (strokes: Stroke[]) => void) {
  const [open, setOpen] = useState<{ opener: HTMLElement | null } | null>(null);
  const [draft, setDraft] = useState<Stroke[]>([]);
  const dirty = open !== null && sigPath(draft) !== sigPath(saved); // also feeds useNavigationBlocker
  const close = () => { setOpen(null); setDraft([]); };
  return {
    open, draft, dirty, setDraft, close,
    openFor: (opener: HTMLElement | null) => { setDraft(saved); setOpen({ opener }); },
    save: () => { if (sigPath(draft) !== "") { onSave(draft); close(); } },
  };
}
```

The box and the popup:

```tsx
// ---- 3. The box and the popup ----
const BTN = "inline-flex min-h-11 items-center justify-center rounded-lg border px-4 text-sm font-medium disabled:opacity-40";
type PE = React.PointerEvent<SVGSVGElement>;

// Strokes are collected while a pointer is down and handed up once, when it lifts. (The shipped box also shows
// "The box is full. Press Clear to start again." when sigParse(d).points >= SIG_MAX_POINTS - 1, because a dot takes two points
// and a full path can stop one short; add it where `d` is computed.)
function SigSurface({ strokes, onChange }: { strokes: Stroke[]; onChange: (s: Stroke[]) => void }) {
  const [live, setLive] = useState<Stroke[] | null>(null); // the strokes while a pointer is down
  const liveRef = useRef<{ pointer: number; strokes: Stroke[] } | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const d = sigPath(live ?? strokes);

  // Pointer positions as points in the box: its own rectangle maps the screen to 600 by 200.
  function pointsOf(list: { clientX: number; clientY: number }[]): Stroke {
    const r = svgRef.current?.getBoundingClientRect();
    if (!r || !(r.width > 0) || !(r.height > 0)) return [];
    return list.map((e): [number, number] => [
      Math.min(SIG_W, Math.max(0, ((e.clientX - r.left) * SIG_W) / r.width)),
      Math.min(SIG_H, Math.max(0, ((e.clientY - r.top) * SIG_H) / r.height)),
    ]);
  }
  function down(e: PE) {
    if (liveRef.current || e.isPrimary === false || (e.pointerType === "mouse" && e.button !== 0)) return; // one stroke at a time
    const [p] = pointsOf([e.nativeEvent]);
    if (!p) return;
    e.preventDefault();
    try { e.currentTarget.setPointerCapture(e.pointerId); } catch { /* not every browser can capture */ }
    liveRef.current = { pointer: e.pointerId, strokes: [...strokes, [p]] };
    setLive(liveRef.current.strokes);
  }
  function move(e: PE) {
    const cur = liveRef.current;
    if (!cur || cur.pointer !== e.pointerId) return;
    let events: { clientX: number; clientY: number }[] = [e.nativeEvent];
    try { const more = e.nativeEvent.getCoalescedEvents?.() ?? []; if (more.length > 0) events = more; } catch { /* the one event is the point */ }
    const last = cur.strokes[cur.strokes.length - 1];
    const add: Stroke = [];
    for (const p of pointsOf(events)) {
      const prev = add[add.length - 1] ?? last[last.length - 1];
      if (Math.hypot(p[0] - prev[0], p[1] - prev[1]) >= SIG_THIN) add.push(p); // thinned the way sigPath thins
    }
    const total = cur.strokes.reduce((n, s) => n + s.length, 0);
    if (add.length === 0 || total + add.length > SIG_MAX_POINTS * 2) return;
    liveRef.current = { pointer: cur.pointer, strokes: [...cur.strokes.slice(0, -1), [...last, ...add]] };
    setLive(liveRef.current.strokes);
  }
  function end(e: PE, keep: boolean) {
    const cur = liveRef.current;
    if (!cur || cur.pointer !== e.pointerId) return;
    liveRef.current = null;
    setLive(null);
    try { e.currentTarget.releasePointerCapture(e.pointerId); } catch { /* nothing was captured */ }
    if (keep) onChange(cur.strokes); // a cancelled pointer (a palm, or the browser taking the gesture over) keeps nothing
  }

  return (
    <div className="relative rounded-xl border bg-white" style={{ maxWidth: SIG_W }}>
      <svg ref={svgRef} viewBox={`0 0 ${SIG_W} ${SIG_H}`} role="img" aria-label={d === "" ? "Signature box, empty" : "Signature box, signed"}
        className="block h-auto w-full select-none" style={{ touchAction: "none", cursor: "crosshair" }} // touch-action: none on the box only
        onPointerDown={down} onPointerMove={move} onPointerUp={(e) => end(e, true)} onPointerLeave={(e) => end(e, true)}
        onPointerCancel={(e) => end(e, false)} onContextMenu={(e) => e.preventDefault()}>
        {d === "" ? <line x1="24" y1="150" x2="576" y2="150" stroke="#d1d5db" />
          : <path d={d} fill="none" stroke="#1f2937" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />}
      </svg>
      {d === "" ? <span aria-hidden="true" className="pointer-events-none absolute left-[4%] top-[55%] text-sm text-gray-400">Sign here</span> : null}
    </div>
  );
}

function SigDialog({ narrow, draft, saved, onDraft, onSave, onClose, opener, fallback }: {
  narrow: boolean; draft: Stroke[]; saved: Stroke[]; onDraft: (s: Stroke[]) => void;
  onSave: () => void; onClose: () => void; opener: HTMLElement | null; fallback: string;
}) {
  const [asking, setAsking] = useState(false); // "Discard this drawing?" in place of the buttons
  const [epoch, setEpoch] = useState(0); // Clear remounts the box, which drops a stroke that is still live
  const cancelRef = useRef<HTMLButtonElement | null>(null);
  const wasAsking = useRef(false);
  const ask = () => (sigPath(draft) !== sigPath(saved) ? setAsking(true) : onClose()); // Cancel: unsaved ink asks first
  const dismiss = () => (asking ? setAsking(false) : ask()); // Escape, the backdrop: while the question shows, its safe answer (the shipped form left it open on a backdrop press)
  useEffect(() => { // the buttons are back after "Keep drawing": focus goes to Cancel, not to <body>
    if (asking) wasAsking.current = true;
    else if (wasAsking.current) { wasAsking.current = false; cancelRef.current?.focus({ preventScroll: true }); }
  }, [asking]);

  return (
    <InBlockModal labelledBy="sig-title" onDismiss={dismiss} returnFocusTo={opener} returnFocusFallback={fallback}
      overlayClass="p-4" panelClass={narrow ? "" : "max-w-[640px]"} showClose={false}>
      <div className={`min-h-0 flex-1 overflow-y-auto ${narrow ? "p-4" : "p-6"}`}>
        <h2 id="sig-title" className="text-lg font-semibold">Draw your signature</h2>
        <div className="mt-3"><SigSurface key={epoch} strokes={draft} onChange={onDraft} /></div>
        {narrow ? <p className="mt-2 text-sm text-gray-500">Tip: turn your phone sideways for more room.</p> : null}
        <div className="mt-4">
          {asking ? (
            <ConfirmStrip key="discard" text="Discard this drawing?" safeLabel="Keep drawing" actionLabel="Discard" onSafe={() => setAsking(false)} onAction={onClose} />
          ) : (
            // the same three nodes in both layouts: the layout classes sit on the buttons, not on wrappers
            <div className={narrow ? "grid grid-cols-2 gap-3" : "flex flex-wrap items-center gap-3"}>
              <button type="button" className={BTN} onClick={() => { setEpoch((n) => n + 1); onDraft([]); }}>Clear</button>
              <button type="button" ref={cancelRef} className={`${BTN} ${narrow ? "" : "ml-auto"}`} onClick={ask}>Cancel</button>
              <button type="button" className={`${BTN} ${narrow ? "col-span-2" : ""}`} onClick={onSave} disabled={sigPath(draft) === ""}>Save signature</button>
            </div>
          )}
        </div>
      </div>
    </InBlockModal>
  );
}
```

The question on the form, and the Send that ties it together:

```tsx
// ---- 4. The question on the form, and Send ----
// `id` is on Add signature, or on Change once there is a drawing, or on the name box: the error summary's jump link finds it.
function SignatureField({ id, pad, onChange, onOpen, error }: {
  id: string; pad: SigPad; onChange: (p: SigPad) => void; onOpen: (opener: HTMLElement) => void; error?: string;
}) {
  const d = sigChecked(sigPath(pad.strokes)); // the preview is drawn from the checked numbers
  const signed = d !== "";
  const typing = pad.mode === "type";
  const [asking, setAsking] = useState(false); // "Remove the signature?" in place of Remove
  const host = useRef<HTMLDivElement | null>(null);
  // Each note and the error get an id, and the control they belong to names them: a screen reader reads them with it.
  const describedBy = (withHint: boolean) => [withHint ? `${id}-hint` : "", error ? `${id}-err` : ""].filter(Boolean).join(" ") || undefined;
  const focusAfter = useRef(""); // a selector: the control that had focus is gone after these changes
  useEffect(() => {
    const sel = focusAfter.current;
    focusAfter.current = "";
    if (sel) host.current?.querySelector<HTMLElement>(sel)?.focus();
  }, [typing, signed, asking]);
  const swap = () => {
    focusAfter.current = typing ? `#${id}-mode` : `#${id}`;
    setAsking(false);
    onChange({ ...pad, mode: typing ? "draw" : "type" }); // both halves are kept; only the one showing is sent
  };

  return (
    <div ref={host} className="space-y-1">
      {error ? <p id={`${id}-err`} role="alert" className="text-sm text-red-600">{error}</p> : null}
      {typing ? (
        <>
          <input id={id} type="text" value={pad.name} maxLength={200} autoComplete="off" aria-invalid={error ? true : undefined}
            aria-describedby={describedBy(true)} onChange={(e) => onChange({ ...pad, name: e.target.value })} className="min-h-11 w-full rounded-lg border px-3" />
          <p id={`${id}-hint`} className="text-sm text-gray-500">A typed name counts as a signature.</p>
        </>
      ) : signed ? (
        <>
          <div className="rounded-xl border bg-white" style={{ maxWidth: SIG_W }}>
            <svg viewBox={`0 0 ${SIG_W} ${SIG_H}`} role="img" aria-label="Your signature" className="block h-auto w-full">
              <path d={d} fill="none" stroke="#1f2937" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button id={id} type="button" aria-describedby={describedBy(false)} className={BTN} onClick={(e) => onOpen(e.currentTarget)}>Change</button>
            {asking ? (
              <ConfirmStrip key="remove" text="Remove the signature?" safeLabel="Keep" actionLabel="Remove"
                onSafe={() => { focusAfter.current = `#${id}-remove`; setAsking(false); }}
                onAction={() => { focusAfter.current = `#${id}`; setAsking(false); onChange({ ...pad, strokes: [] }); }} />
            ) : (
              <button id={`${id}-remove`} type="button" className={BTN} onClick={() => setAsking(true)}>Remove</button>
            )}
          </div>
        </>
      ) : (
        <>
          <button id={id} type="button" aria-describedby={describedBy(true)} className={`${BTN} w-full`} onClick={(e) => onOpen(e.currentTarget)}>
            <Pen className="mr-2 h-4 w-4" aria-hidden="true" />Add signature
          </button>
          <p id={`${id}-hint`} className="text-sm text-gray-500">Press Add signature, then sign with your finger, a stylus or the mouse.</p>
        </>
      )}
      <button id={`${id}-mode`} type="button" onClick={swap} className="min-h-11 text-sm font-medium underline underline-offset-2">
        {typing ? "Draw the signature instead" : "Type the name instead"}
      </button>
    </div>
  );
}

// Placeholders: your own data source id (a string literal, see multi-datasource.md) and your own field ids (from database_list_fields).
const ds = datasource.define({ rows: "DATASOURCE_UUID" });
const createSelect = q.select({ signature: "TEXT_FIELD_ID", signatureFile: "ATTACHMENT_FIELD_ID" }); // the text copy, and the ATTACHMENT field

export default function Block() {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const narrow = useElementWidth(rootRef) < 480; // the popup is outside the @container, so measure the block
  const [pad, setPad] = useState<SigPad>({ mode: "draw", strokes: [], name: "" });
  const popup = useSigPopup(pad.strokes, (strokes) => setPad((p) => ({ ...p, strokes })));
  const SU = useSignatureUpload();
  const [packing, setPacking] = useState(false); // the picture is being made and uploaded
  const [sending, setSending] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const sendingRef = useRef(false); // the double-send guard, set before the first await
  // ds and createSelect are the placeholders above: `signature` is the text column, `signatureFile` the ATTACHMENT field.
  const create = useRecordCreate({ from: ds.rows, fields: createSelect });
  // useNavigationBlocker(popup.dirty || the form's own dirty rule): see Navigation Blocker for Unsaved Changes.

  async function send() {
    if (sendingRef.current) return;
    sendingRef.current = true;
    try {
      const bad = sigProblem(pad);
      setProblem(bad);
      if (bad) return;
      if (!create.enabled) { // nothing is uploaded when the create cannot run
        // ... the "not available" error ...
        return;
      }
      setSending(true); // only now: "Sending…" does not flash on a form that fails its checks
      const drawn = pad.mode === "draw" ? sigChecked(sigPath(pad.strokes)) : ""; // a typed name uploads nothing
      const value = drawn ? { kind: "drawn", d: drawn } : { kind: "typed", name: pad.name.trim() };
      const file = drawn ? await SU.store(drawn, setPacking) : null; // a null never stops the send
      const row: Record<string, unknown> = { signature: JSON.stringify(value) }; // the text copy, always
      if (file) row.signatureFile = { filename: file.filename, url: file.url }; // no key at all without a file
      await create.mutateAsync(row);
      SU.forget();
      // ... wipe the answers, show the thank-you screen ...
    } catch {
      // ... the one send error ...
    } finally {
      sendingRef.current = false;
      setSending(false);
    }
  }

  return (
    <>
      <div ref={rootRef} className="@container">
        <SignatureField id="field-signature" pad={pad} onChange={setPad} onOpen={popup.openFor} error={problem ?? undefined} />
        <button type="button" disabled={sending} onClick={() => void send()}>
          {packing ? "Saving your signature…" : sending ? "Sending…" : "Send"}
        </button>
      </div>
      {/* A sibling of the @container wrapper, not a child of it. */}
      {popup.open ? (
        <SigDialog narrow={narrow} draft={popup.draft} saved={pad.strokes} onDraft={popup.setDraft} onSave={popup.save}
          onClose={popup.close} opener={popup.open.opener} fallback="#field-signature" />
      ) : null}
    </>
  );
}
```

## A form open while its record changes

A form filled from a record once (on first load, after its own save, after Discard) goes stale when the record changes under it: a colleague saves the same record, or the window-focus refetch ([reading.md](../datasources/reading.md#userecords----fetch-a-paginated-list)) brings back what someone else wrote. The form keeps its old values while "dirty" is measured against the new record, so the card says "Unsaved changes" that nobody made, and the next Save writes the whole stale form back over the colleague's change. Last write wins, and nothing says so.

Keep a **baseline** beside the form: the form as it was last filled from the record.

- **Hold the baseline in a ref** and set it whenever the form is filled from the record (first load, the person's own save, Discard, a link, unlink or create action that re-fills the form) and nowhere else.
- **Dirty is the form against the baseline, key by key** ([ui-ux-guidelines.md](../ui-ux-guidelines.md#15-error-prevention-and-destructive-actions)), not the form against the record.
- **Save sends only the keys that differ from the baseline** ([writing.md → Send only what changed](../datasources/writing.md#critical-the-userecordupdate-payload-shape-and-the-retired-mutate-only-rule)), and on success moves the baseline to what it saved before the re-read lands.
- **When the record changes under an open form, merge.** For each key, a field still equal to the baseline takes the record's new value (the colleague's change appears and "Unsaved changes" stays off); a field the person edited keeps their value; then the baseline becomes the new record's form. A key both people changed keeps the person's edit, and their Save overwrites the colleague's on purpose: say so in a note or a confirmation if that matters.

Refilling the whole form whenever the data changes is not the answer: it wipes what the person is typing. The counter fix in [anti-patterns.md → Hooks & React](anti-patterns.md#hooks--react) (bump a counter the fill effect depends on) has the same problem here.

Seen on an item card with 33 fields (QA pass, 2026-10-16): with a colleague's ETA change simulated through a mocked read while notes had been typed, the untouched ETA box took the new value, the typed notes stayed, and the Save body carried only the notes. The overwrite before the fix is read from the code, not captured: it takes two sessions on one record.

## Drafts that survive a reload

A long entry form (a multi-row hours or distribution entry) loses everything on a reload or an in-app link. [`useNavigationBlocker`](#navigation-blocker-for-unsaved-changes) asks first; a draft in `sessionStorage` is what survives when the user goes anyway (QA pass, 2026-10-08: after a failed save, a sidebar link and then Back showed "Restored 1 unsaved row" with its people, hours and error text intact).

- **Wrap every storage read and write in try/catch**, and make the form work without it (it can throw in a private window).
- **Store the signed-in user's email with the draft and drop a mismatch.** `sessionStorage` outlives a Softr sign-out in the same tab, so a draft keyed by record alone would restore one staff member's quantities for the next. Key by record too.
- **Until the email is known, neither restore the draft nor remove it; restore it when the email resolves.** Don't accept a draft while the user is unknown: on a shared computer that shows the previous person's rows. Whether the email is there at the first render was not proven live, so write the restore to work either way.
- **Run the restore from an effect keyed on the email, and gate it on nothing else that resolves late** (write access, a mutation's `enabled`, the product list). A restore gated on something late is skipped, and the effect that removes empty drafts then deletes the draft on mount. Measure "dirty" from the form's own state, not from a list that is still loading.
- **Remove a draft only after the dialog has been open in this mount** (a `seen` ref), never at mount. An effect that saves the empty form on mount wipes the draft it should have read, and so does one that clears storage before the restore has run.
- **Persist only while no save is running.** A row that was mid-save comes back as failed, with a "may have been saved" note, never as a draft: restoring it as a draft would send the same row twice. Never restore a confirm or review step, which is one click from a write.
- **A save queue stops when the block unmounts** (a ref the loop checks), or it keeps writing for a page the user has left.
- **Discard removes only the restored rows**, not the rows typed since. Discard removes its own note, so move focus to a stable control first, and give a dialog restored at load a fallback return-focus target, as it has no opener ([Failures, focus and Escape](#failures-focus-and-escape)).

```tsx
// Module scope. A sketch of the keying, not a copy of a shipped block.
const DRAFT_KEY = "softr_myapp_hours_draft";   // namespaced, as in the localStorage section above

function loadDraft(email: string, recordId: string) {
  if (!email) return null;   // user not resolved yet: no restore, and the caller must not remove the draft either
  try {
    const d = JSON.parse(sessionStorage.getItem(DRAFT_KEY) || "null");
    return d && d.email === email && d.recordId === recordId ? d.rows : null;
  } catch { return null; }
}

function saveDraft(email: string, recordId: string, rows: unknown[]) {
  try { sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ email, recordId, rows })); } catch {}
}

// In Block(): restore when the email becomes known, once. The save/remove effect returns early until then.
//   const restored = useRef(false);
//   useEffect(() => {
//     if (!email || restored.current) return;
//     restored.current = true;
//     const rows = loadDraft(email, recordId);
//     if (rows) setRows(rows);
//   }, [email, recordId]);
```

## CSV export

A CSV export is a small feature with six ways to go wrong (QA pass, 2026-10-08):

- **Name the file for the period shown** (`volunteer-hours-2026-10.csv`), not the export day.
- **Put a "Generated" line in local time with its UTC offset**: `format(new Date(), "yyyy-MM-dd HH:mm xxx")` gives `2026-10-07 22:49 -07:00`. A UTC stamp read as the next day after 5 pm Pacific.
- **Prepend a UTF-8 BOM** so spreadsheet apps read accents, built from a code point, with no invisible character in the source and no `\uFEFF` escape ([escapes in pushed source arrive decoded](softr-mcp.md#unicode-escapes-come-back-decoded)).
- **Give a unit with every figure**, and list an item in a different unit once, apart from the others (wipes counted in packs showed twice, in the size table and again in the CSV).
- **Prefix free-text cells that start with `=`, `+`, `-` or `@` with an apostrophe**, because a spreadsheet runs them as formulas. Apply it to text, never to numbers. A precaution: no formula ran.
- **Disable the button until the data it exports has fully loaded**: every page fetched, no read in error.

```tsx
const CSV_BOM = String.fromCharCode(0xfeff);   // prepend to the file text

function csvCell(v: unknown): string {
  if (typeof v === "number") return String(v);
  let t = v == null ? "" : String(v);
  if (/^[=+\-@]/.test(t)) t = "'" + t;           // text only: a spreadsheet would run it as a formula
  return /[",\r\n]/.test(t) ? '"' + t.replace(/"/g, '""') + '"' : t;
}

// new Blob([CSV_BOM + lines.join("\r\n")], { type: "text/csv;charset=utf-8" })
```

To read what an export contains without downloading it (and to see the BOM, which `Blob.text()` hides), see the Exports and printouts section of [browser-checks.md](browser-checks.md).

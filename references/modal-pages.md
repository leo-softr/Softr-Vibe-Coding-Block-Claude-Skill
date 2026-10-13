# Blocks on a page opened in a modal

Softr's navigation can open a page, a URL or a section. It cannot open a block. A block that has to
open from the nav (or from any Softr link or action) as an overlay therefore gets **a page of its
own**, and that page opens in Softr's **Modal**. This file covers what Softr renders for that, what
it changes for the code of a block on such a page, how to close the modal from inside, and a
page-mode recipe.

**How sure each fact is.** The runtime facts below come from Softr's public bundles: the page
renderer (`softr-page-renderer.js`), `OpenPageDialog.mjs` and the navigation block 5.0.7 (built
2026-10-09T11:50Z), all fetched and read on 2026-10-09.
Nothing here had been run in a live app when it was written.
<!-- LIVE-CHECK: after the live check in Softr <> HubSpot Demo, replace the sentence "Nothing here had been run in a live app when it was written" with the result, and mark each fact below as tested live or refuted (the probes are in the comments that follow). -->
The marks used:

- **documented**: in Softr's docs or said by Softr staff.
- **read from code**: seen in those bundles (the research behind this file called these "proven").
- **inferred**: follows from the code but is not written in it (called "likely").
- **unverified**: the code does not settle it (called "guess" or listed as an unknown).

## Contents

- [When to use it](#when-to-use-it)
- [What Softr renders](#what-softr-renders)
- [What changes for block code inside it](#what-changes-for-block-code-inside-it)
- [Closing from inside](#closing-from-inside)
- [A page-mode recipe](#a-page-mode-recipe)
- [Pitfalls](#pitfalls)
- [Worked case](#worked-case)

## When to use it

**The problem** (seen in Studio on 2026-10-09, Softr <> HubSpot Demo). A top-bar **button** offers
Action **Open page**, with a Page picker that lists **pages only**, and **Open in**: Same tab, New
tab or Modal. A block that opens an in-block popup from a hash (`/dashboard#create-activity`) or an
event cannot be the target of an Open page item: a picker of pages cannot produce a hash. (Whether a `?open=…`
query can be added to the destination was not seen. Open URL is a second action; see
[Opening a block from the navigation](native-chrome-styling.md#opening-a-block-from-the-navigation)
for what it accepts.)

**The fix.** Give the block a page of its own, for example `/new-activity`, and point the nav
button at that page with Open in **Modal**. In Studio:

1. Navigation, the top bar, **Buttons**, then the button.
2. Action **Open page**, Page **the block's page**, Open in **Modal**.
3. Size (SM, MD, LG or XL) and type (Centered or Sliding). Softr documents both pickers for the
   modal of an item action; whether a nav **button** shows them was not seen. The navigation
   block's defaults are MD and POPUP (read from code), so with no pickers the modal is size M,
   centred.
   <!-- LIVE-CHECK: open Studio, Navigation, a top-bar button, Open in Modal: are size and type shown? Note the labels and defaults here. -->
4. The button's own visibility: the group that may use it. Narrow the page's VIEW permission to the
   same group (see [Pitfalls](#pitfalls)).

A block's own `<NavigationAction>` or `navigate()` with `openIn: "MODAL"` also opens the page in a
modal, with the builder's `modalSize` and `modalType` (documented). That it is this same dialog is
unverified. Given a `recordId` and `datasourceId`, it adds `?recordId=<id>` to the destination
(documented), which a nav button never does. How those sizes map for a block setting, as against
the nav's mapping below, is unverified.

**When not to.** A block that opens from its own button on the page needs no page of its own: use
the in-block modal in [common-patterns.md](common-patterns.md#a-modal-above-softrs-bars).

## What Softr renders

- **A dialog with an iframe in it** (read from code). "Open in: Modal" renders a Radix dialog,
  `[data-softr-dialog-type="OPEN_PAGE"]` (content id `softr-page-dialog`), at z-index 900. It holds
  `<iframe title="Embedded page" allow="clipboard-write">` with **no `sandbox`** attribute. The
  page's blocks do **not** render in the opener's document. The renderer loads the dialog lazily
  from `OpenPageDialog.mjs`. Softr staff said in February 2025 that they would later drop iframe
  modals (documented); the bundles of 2026-10-09 still use one.
- **The iframe's URL is `/<slug>?viewMode=modal`** (read from code). It is same-origin. The first
  load is a full server-rendered page load into a blank iframe. The opener's own query is not
  copied to it.
- **The opener's URL changes** (read from code). It keeps its path and gets
  `?modal=%2F<slug>&modalSize=M&modalPlacement=center` pushed on with `pushState` (navigation 5.0.6 and 5.0.7; see Version differences). The state lives
  in that query, so a URL that already carries it reopens the modal (a deep link), and
  Cmd/Ctrl/middle-click on the button opens the current page in a new tab with the modal already
  open. **Browser Back closes the modal** on navigation 5.0.6 and 5.0.7 (Softr staff released Back
  support on 2026-05-27, documented).
- **Sizes** (read from code for the heights, inferred for the widths). The nav maps Studio's SM and
  MD to **M** (dialog 832px wide, iframe **624px** tall), LG to **L** (968px, **720px**) and XL to
  **FULL** (the window less 32px, iframe 100% tall). Studio's SM therefore cannot reach the small
  size (560 × 472). The iframe height is fixed, so the block has to fill it and scroll inside it.
  The widths come from the stylesheet and are matched to the sizes by their order.
- **Sliding** (read from code). Type Sliding maps to placement `end`: a panel on the right that the
  user can resize between 400px and 80vw, with the width kept per browser in `localStorage` key
  `openPageDialogPanelWidthPx` (read from code; Softr staff announced the resize on 2026-06-10,
  documented).
- **Phones** (read from code). Below a 768px window every modal is a **vaul bottom drawer** with a
  maximum height of 85svh, whatever size or type is set.
  <!-- LIVE-CHECK: at 390px, is document.querySelector('[data-vaul-drawer]') present, and how does the fixed 624px iframe sit inside the 85svh drawer? Where do top-bar buttons appear on a phone (More sheet, overflow menu, tab bar, nowhere)? -->
- **The nav button is a link, not a `<button>`** (read from code). It is
  `<a class="softr-nav-button">`. On navigation 5.0.5 and later its `href` is the **current page's absolute URL** (host, query and
  hash kept) with the three modal parameters added, not `/<slug>`, so it contains the slug after an
  encoded slash: `…&modal=%2Fnew-activity&…`. A React `onClick` calls `preventDefault` and opens the
  modal; a Cmd/Ctrl/middle click follows the `href`. Of the action items, only Sign out is a
  `<button>`.
- **It carries no record** (read from code). A nav button builds its link with no record, so the
  page gets no `?recordId=`.
- **Version differences** (read from code). Navigation 5.0.5, 5.0.6 and 5.0.7 behave as above
  (5.0.5 keeps its own copy of the open call and uses `replaceState`, so Back does not close the
  modal: it leaves the opener page for the entry before it). 5.0.3 has its own dialog with the same
  iframe, a fixed size M and centre placement, keeps no URL state, and gives the button the bare
  `/<slug>` as its `href`. 5.0.0 could not be read. The MCP does not show which version an app
  serves (`application_page_get_block` returns the navigation block without one); whether Studio
  shows it was not checked. The probe below reads it.
  <!-- LIVE-CHECK: on any staff page in the preview, run performance.getEntriesByType('resource').map(r=>r.name).filter(n=>n.includes('/blocks/navigation/')) and [...document.querySelectorAll('.softr-topbar a.softr-nav-button')].map(a=>[a.textContent.trim(),a.getAttribute('href'),a.getAttribute('aria-haspopup')]). Record the nav version and the href shape here. -->
- **The app's custom code runs in the page** (read from code). The app's header and footer custom
  code reach the modal page: the renderer injects them with no check for modal mode, and the server
  HTML of `/login?viewMode=modal` carried the same app header code as `/login` (a fetch on
  2026-10-09). Page-level header code is injected only when SPA mode is off.
- **The navigation block is stripped from page fetches in modal mode** (read from code). The renderer
  removes the `navigation` block when it fetches a page definition with `viewMode=modal` in the
  URL. The modal's first load is server-rendered, and whether the server also leaves the nav out is
  unverified. The community reports of "no nav in the modal" date from the older modal.
  <!-- LIVE-CHECK: after one click on the button, run f=document.querySelector('[data-softr-dialog-type="OPEN_PAGE"] iframe'); [f.contentWindow.location.href, !!f.contentDocument.querySelector('.softr-topbar,.softr-sidebar,.softr-bottombar'), f.contentWindow.location.pathname]. A false second value means the nav is out; a /401 pathname means the page's Visibility is wrong. -->
- **No "modal page" type** (none in Softr's docs, read 2026-10-09). Softr documents that a page
  shows in the navigation only if the builder adds it there, and its docs list no
  hide-from-navigation flag. Per page you can turn the navigation off, set
  Visibility (others go to the 401 page), make it a draft and turn off indexing.

## What changes for block code inside it

The block runs in the iframe's own window and document. "The opener" below means the page behind
the modal, which the block reaches as `window.parent` (not `window.opener`).

- **`window`, `document`, `vh` and `position: fixed` are the iframe's** (inferred from the code).
  Viewport units resolve against the modal box. A fixed overlay covers the iframe and nothing else,
  so an in-block modal here would only be a box inside a box: let Softr's dialog be the frame. The
  block is still a shadow root, but the "main document" it sits in is the iframe's, not the
  opener's.
- **`window.parent` is the opener** (read from code: same-origin, no sandbox). Wrap **every** parent
  access in `try/catch`: in the Studio canvas the parent may be cross-origin (unverified), and on a
  direct visit `window.parent === window`.
  <!-- LIVE-CHECK: in the Studio canvas, does window.parent.location.search throw? -->
- **The opener's URL is the context** (read from code). The iframe's URL holds only
  `?viewMode=modal`, so anything that used to be read from `window.location` (a record in
  `?recordId=`, a filter) is now read from `window.parent.location`. Softr's own modal code reads
  the parent's location the same way. Opened from a block's `NavigationAction` given a `recordId`,
  the destination carries `?recordId=` (documented), and the runtime reads the record from the modal
  page's own URL (inferred from Softr's shared chunk), so `useCurrentRecordId()` should return it there (not run).
  Opened from the nav it returns null: the nav passes no record (read from code).
- **Events go to `window.parent`** (inferred; Softr does the same). A listener on the opener's
  window does not hear an event dispatched on the iframe's window. Softr's modal page dispatches
  `modal-current-record` on `window.parent`, and Softr's docs show
  `window.parent.dispatchEvent(new CustomEvent('reload-block-<hrid>'))` from a details page opened
  in a modal (documented). An event built in the iframe belongs to the iframe's realm: a listener
  in the opener should use `Array.isArray`, which works across realms, not `instanceof Array`.
  <!-- LIVE-CHECK: in the parent run addEventListener('app:probe',e=>window.__got=e.detail); from the iframe run window.parent.dispatchEvent(new CustomEvent('app:probe',{detail:{x:[1]}})); read window.__got from the parent. -->
- **Toasts do not survive** (inferred; the iframe's removal on close is read from code). A toast
  fired just before closing goes with the iframe, and a toast in the iframe is confined to the
  iframe. Whether a Toaster is mounted in the iframe page at all is unverified. Show the outcome
  **in the page**, as a success view, before the user closes it. A toast's "Open" action that calls
  `window.location.assign` would load the target inside the modal; send the opener instead (see
  the recipe).
- **Escape inside the iframe does not reach Softr's dialog** (inferred). Radix listens for Escape
  on the **parent** document, key events inside an iframe do not cross into it, and neither the
  renderer nor `OpenPageDialog.mjs` forwards Escape. Radix focuses the X first, so Escape works
  only until the user clicks into the page. A block that wants Escape to close the modal must
  handle an unhandled Escape itself.
  <!-- LIVE-CHECK: focus a field in the iframe, press Escape: is document.querySelector('[data-softr-dialog-type="OPEN_PAGE"]') still there? -->
- **Softr's own close guard** (read from code). The X, a press on the backdrop and Escape in the
  parent all run one handler. It dispatches a **cancelable `beforeunload` event on the iframe's
  window**; if a listener calls `preventDefault`, Softr asks
  `window.confirm("Are you sure you want to discard changes?")` before closing. `useNavigationBlocker`
  (see [Navigation Blocker](common-patterns.md#navigation-blocker-for-unsaved-changes)) registers
  a `beforeunload` listener that calls `preventDefault` while its flag is true (read from the
  renderer's hook; the mapping of the `@/lib/use-navigation-blocker` import to that hook was not
  inspected), so `useNavigationBlocker(dirty)` should give the modal this guard with no extra code.
  **Browser Back skips the guard** (inferred): the open state is the parent's query, Back changes
  it, the dialog closes as a prop change, and removing an iframe never prompts. Typed input is lost
  silently.
  <!-- LIVE-CHECK: in the parent set window.__c=[];window.confirm=m=>(window.__c.push(m),false); in the iframe addEventListener('beforeunload',e=>e.preventDefault()); click the X: the dialog should stay and __c should hold the message. Then press Back: expect it to close with no confirm. Also confirm a block using useNavigationBlocker(true) triggers the same. -->
- **Each open is a fresh iframe** (read from code). The full app shell loads and the block's reads
  run again every time. Load time is unmeasured.

## Closing from inside

- **Clean close: `window.parent.SoftrPageRenderer.setOpenPageModal(null)`** (read from code;
  undocumented and internal, so it can change). It runs in the opener's copy of the renderer, takes
  the close branch, restores the history index the modal opened at and skips the `beforeunload`
  guard. The close is asynchronous. It was read against navigation 5.0.6 and 5.0.7. On 5.0.5, whose own
  open call uses `replaceState` and records no history index, the same call takes its
  `replaceState` branch, so it should still close the modal, with no history restore (read from
  code, not run). On 5.0.3 the open state lives inside the nav block, where the call does not
  reach it. With no `modal=` in the opener's query, the call takes its pushState branch and adds a
  history entry instead of closing (read from code), so check for `modal=` first.
  <!-- LIVE-CHECK: from the iframe context call window.parent.SoftrPageRenderer.setOpenPageModal(null). After about 300 ms the dialog should be gone, new URLSearchParams(location.search).has('modal') false, and history.back() must not reopen it. -->
- **Not the iframe's own `window.SoftrPageRenderer.setOpenPageModal(null)`** (read from code). In
  the iframe the renderer knows it is in a modal and acts on `window.parent` with `pushState`,
  adding a history entry without the modal parameters. Back then returns to the entry that has
  `?modal=` and reopens the modal.
- **Not the `REDIRECT_PARENT` event to refresh the same page** (inferred). Dispatching
  `new CustomEvent('REDIRECT_PARENT', { detail: { destination } })` on `window.parent` closes the
  modal and sends the opener to `destination`, but when `destination` equals the opener's path it
  reloads `location.href` in the same tick. That `href` still carries `?modal=`, so the reload can
  reopen the modal or race the history traversal. The order of the calls is read from code; the
  race was not run.
- **Documented ways** that need no internals: a form's **"Close the modal"** ending (Add Record's
  "Close the modal", and the "Close modal" form ending released 2026-06-11), and a Workflow
  **End User Interactions** step with Navigation set to "close a modal". The second works only for
  an app-triggered Run Custom Workflow trigger, which a Vibe block can start through `navigate()`
  with a `TRIGGER_CUSTOM_WORKFLOW` setting. Neither route was run from a Vibe block inside a page
  modal.
- **A Same-tab link** from Softr's link code in the modal targets `_parent` (inferred from the
  navigation block's SELF branch; a block's `NavigationAction` was not read): it navigates the
  opener, which drops the modal parameters, so the modal closes. Softr support (2026-05-04) suggests an Open URL to the
  opener page, Same tab, as a close button; it also refreshes the page.

## A page-mode recipe

A block that is also used as an in-page popup elsewhere, or that must look right on a direct visit,
switches into "page mode" on the modal page. Module scope first (modern TS; nothing here has been
run as written):

```tsx
import { useEffect, useRef } from "react";
import { useBooleanSetting } from "@/lib/editable-settings";
import { useNavigationBlocker } from "@/lib/use-navigation-blocker";

const PAGE_PATH = /^\/new-activity\/?$/; // the page's own path: a fallback for the setting only

// Softr loads the page in an iframe as /<slug>?viewMode=modal. A direct visit has no iframe.
function inSoftrModal(): boolean {
  return /[?&]viewMode=modal(&|$)/.test(window.location.search) && window.parent !== window;
}

// The opener's URL, where the context lives (a nav button passes no record). Never throws.
function hostLocation(): { pathname: string; search: string } {
  if (inSoftrModal()) {
    try {
      return { pathname: window.parent.location.pathname, search: window.parent.location.search };
    } catch {
      /* a cross-origin parent (the Studio canvas): fall back to our own URL */
    }
  }
  return { pathname: window.location.pathname, search: window.location.search };
}

// The clean close. Returns false on a direct visit or when the call is not there, so the caller can
// keep the page usable.
function closeHostModal(): boolean {
  try {
    if (!inSoftrModal()) return false; // a direct visit: window.parent is this page's own renderer
    if (!new URLSearchParams(window.parent.location.search).has("modal")) return false; // no modal= in the opener (nav 5.0.3): the call would only pushState
    const renderer = (window.parent as any).SoftrPageRenderer;
    if (typeof renderer?.setOpenPageModal !== "function") return false;
    renderer.setOpenPageModal(null);
    return true;
  } catch {
    return false;
  }
}

// Tell the page behind the modal; its listeners sit on ITS window.
function tellHost(name: string, detail: unknown): void {
  window.dispatchEvent(new CustomEvent(name, { detail }));
  if (!inSoftrModal()) return;
  try {
    window.parent.dispatchEvent(new CustomEvent(name, { detail }));
  } catch {
    /* ignore */
  }
}
```

Detection, the guard and Escape, inside `Block()` with the other hooks:

```tsx
// The switch is a setting, so it also works where the URL is not the page's path (the Studio
// canvas). Never rename it: a rename resets the saved value.
const showAsPage = useBooleanSetting({
  name: "show-as-page",
  label: "Show the form on the page (for the modal page)",
  initialValue: false,
});
const pageMode = showAsPage || PAGE_PATH.test(window.location.pathname);
const inModal = pageMode && inSoftrModal();

// Softr's X, backdrop and Escape-in-the-parent dispatch a cancelable beforeunload on this window.
// Called on every render (hooks cannot be conditional); the callback form returns false off the page.
const guardRef = useRef(false);
guardRef.current = pageMode && dirty && !saved; // your own state names
useNavigationBlocker(() => guardRef.current);

// Escape in the iframe never reaches Softr's dialog. Bubble phase: an open list or calendar handles
// Escape first and calls preventDefault, so only the innermost layer closes.
const closeRef = useRef<() => void>(() => {});
closeRef.current = () => {
  if (dirty) return askToDiscard(); // your own discard question
  if (!closeHostModal()) resetForm(); // direct visit, or no close call: clear the form instead
};
useEffect(() => {
  if (!pageMode) return;
  const onKey = (e: KeyboardEvent) => {
    if (e.key !== "Escape" || e.defaultPrevented || e.isComposing) return;
    closeRef.current();
  };
  document.addEventListener("keydown", onKey);
  return () => document.removeEventListener("keydown", onKey);
}, [pageMode]);

// Focus the shell on mount so Escape works at once. Not a text field: on a phone it opens the keyboard.
const shellRef = useRef<HTMLDivElement>(null);
useEffect(() => {
  if (inModal) shellRef.current?.focus();
}, [inModal]);
```

The shell fills the iframe, which has a fixed height, and scrolls **inside** it (`h-dvh` assumes
the block is the page's only block and that the nav is absent from the modal; see the navigation
bullet under [What Softr renders](#what-softr-renders)):

```tsx
// In the modal: no overlay, backdrop, ×, scroll lock or Tab trap of our own. Softr's dialog is the frame.
<div ref={shellRef} tabIndex={-1} className="@container flex h-dvh flex-col bg-white outline-none">
  {/* pr-16: keep the top-right corner free, Softr's own X may sit over it */}
  <header className="shrink-0 pl-6 pr-16 pt-5 pb-3">
    <h1 className="text-lg font-semibold">Log an activity</h1>
  </header>
  <div className="min-h-0 flex-1 overflow-y-auto px-6">{/* the only scroll box */}</div>
  <footer className="shrink-0 border-t border-gray-200 bg-white px-6 py-3">{/* always visible */}</footer>
</div>
```

Outside the modal (a direct visit, or Studio) the same form sits in a centred card of natural height
(`mx-auto w-full max-w-[40rem] rounded-2xl border`), so it does not stretch across a full window.

<!-- LIVE-CHECK: does Softr's X overlap the iframe's top-right corner, and does shellRef.current.focus() inside the iframe really move keyboard focus there? Adjust pr-16 and the focus advice to what is seen. -->

After a save, show the result **in the page**, tell the page behind the modal, and let the user close:

```tsx
function onSaved(detail: { type: string }) {
  tellHost("app:record-created", detail); // the opener (a deal page, say) updates itself
  setSaved("Call logged"); // a success view in place of the body and footer, not a toast
}
// The success view: an h1 with tabIndex={-1} (focus it, announce it), where the record went, and
//   Done       -> closeHostModal()
//   Log another -> reset the form and re-read hostLocation() for the prefill
//   Open …     -> in the modal: try { window.parent.location.assign(target) } catch {}
//                 (a full load of the opener, which ends the modal); on a direct visit window.location
```

On a direct visit there is no Done; the primary button is Log another.

## Pitfalls

- **A link interceptor that matches part of an `href` will catch the nav button.** On navigation
  5.0.5 and later the button's `href` is the current URL plus `modal=%2F<slug>`, so it **contains
  the slug**. A listener, selector or marker such as `a[href*="create-activity"]` or
  `href.indexOf("create-activity") >= 0` matches it. A `window` capture-phase click listener runs
  before Softr's React handler on the root (standard DOM order, not run live), so one that calls
  `preventDefault` and `stopImmediatePropagation` keeps Softr's modal from ever opening. Match exact
  hashes and parameters (`#create-activity$`, `[?&]open=create-activity\b`) or pick a slug that
  cannot match. The slash is encoded in that `href` (`%2F`), so a match on `/new-activity` misses it
  while `new-activity` hits it (on 5.0.3 the `href` is the bare `/new-activity`, which both match).
  The same applies to a CSS rule such as `a[href*="…"]`: see
  [Opening a block from the navigation](native-chrome-styling.md#opening-a-block-from-the-navigation).
  <!-- LIVE-CHECK: on a page that still has a block with a substring interceptor, check whether the new nav <a> got the attribute the block stamps on matching links (for Create activity: aria-haspopup="dialog" and document.documentElement.dataset.hsdemoCreateActivity === 'ready'). With a slug free of the marker it must be absent. -->
- **A new page takes the app's default VIEW permission, and only Studio can change it.**
  `application_page_create` makes the page with the app's default VIEW (logged-in users in this app;
  seen 2026-10-05 and 2026-10-09). No MCP tool narrows it or adds
  the nav item ([softr-mcp.md](softr-mcp.md#application-management-tools)). Narrow the page's VIEW in
  Studio **and** keep the block's own Visibility on the same group: the page gate and the block gate
  are separate, and a viewer outside the page's Visibility lands on Softr's 401 page (documented),
  which inside a modal presumably renders in the iframe (unverified).
- **The page is also a real page.** A direct visit, a link opened in a new tab and a shared URL show
  it full-window. Decide what that shows; the recipe's centred card is one answer.
- **Do not put the block's own overlay on the modal page.** The iframe's `position: fixed` covers
  the iframe only, and Softr's dialog already dims the opener.

## Worked case

The Create activity block in Softr <> HubSpot Demo (2026-10-09). It first opened as an in-block
popup from `#create-activity`, `?open=create-activity` or a click on any link whose `href` contains
`create-activity`, on eight staff pages. A top-bar button cannot carry any of those, so the block got
a page, `/new-activity` ("Create activity"; the block's Visibility is the Account managers group,
and the page's VIEW is to be narrowed to it in Studio), to be opened from a top-bar button with Open
in Modal. The block's source gained a `show-as-page` setting and the page mode above; it had not
been pushed when this was written. The slug avoids the string that the eight popup instances
intercept. The research behind this file, and the build brief for the page, are in that project's
`research/` folder; the page mode was designed from the bundles and its live check was still to come
when this was written.
<!-- LIVE-CHECK: after the Create activity page-mode push and the live checks of the probes above, update this paragraph with what was seen (nav version, nav in the modal, Escape, close, guard, event delivery, phone drawer). -->

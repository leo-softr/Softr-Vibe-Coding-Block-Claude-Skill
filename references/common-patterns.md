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

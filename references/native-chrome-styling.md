# Styling Softr's Native Shell (Header · Footer · Page Background) via Custom Code

**This is NOT about Vibe Coding blocks.** Softr's top bar, navigation, dropdown menus, footer, and the page background are part of the *native app shell* — configured in Softr Studio and rendered in the **main document**, not inside a block's shadow DOM. You **cannot** build or replace the native chrome itself as a Vibe Coding block. To re-skin it, add **CSS to Settings → Custom Code → Code inside header** (the same place brand fonts/tokens live — house convention keeps that CSS in a `custom-code-header.html` file in the project folder and pastes it into the setting; you author it from the project's DESIGN.md tokens, since dembrandt supplies the palette and webfont URLs but generates no Softr-ready CSS — see [dembrandt.md](dembrandt.md#authoring-custom-code-headerhtml-from-designmd)). Pure CSS — no markup, no JS — and the native chrome stays in place, so Softr's auth-aware nav (account menu, sign-out, user-group gating) keeps working. (Separate pattern, different problem: a landing page with the native header **hidden** can carry a block-owned in-block header — see [Restyle vs. replace vs. block-owned header](#restyle-vs-replace-vs-block-owned-header).)

This doc covers the **header / nav / dropdowns**, the **footer**, the **floating "island" treatment** for both, and the **page background** — which is trickier than it looks, because Softr stacks the same fill on several layers.

> **Mirror of the block rule.** Global `custom-code-header.html` CSS reaches native chrome (main document) but **not** blocks (shadow DOM). Inside a block you apply brand styles inline; for native chrome you apply them with this global CSS. (See [anti-patterns.md](anti-patterns.md) for the block side.)

## Selector discipline — the #1 rule

Softr's rendered markup carries two kinds of classes:

- **Hashed build classes** like `f8f11e5_m9ntthp` — **NEVER target these.** Softr regenerates the hash on every deploy, so your rules silently die.
- **Stable hooks** — target these instead:

| Element | Stable selector |
|---|---|
| Sticky root wrapper | `#topbar-root` |
| The bar itself | `.softr-topbar` (also `[data-testid="topbar"]`) |
| Logo image | `.softr-nav-logo` |
| Nav links (Home, etc.) | `.softr-nav-link` |
| Nav buttons / dropdown triggers | `.softr-nav-button` |
| Overflow "…" trigger | `.softr-nav-category` |
| Active / current link | `.softr-nav-link[data-active="true"]` |
| Open dropdown trigger | `.softr-nav-button[aria-expanded="true"]` |

**Dropdown menus have NO `softr-*` class** — they're **Radix UI**, so target ARIA / Radix attributes (stable across deploys):

| Element | Stable selector |
|---|---|
| Menubar (the row of items) | `[role="menubar"]` |
| Open dropdown panel | `[role="menu"]` (+ `[data-state="open"]`, `[data-side="bottom"]`) |
| A menu item | `[role="menuitem"]` |
| Items group inside the panel | `[role="group"]` |
| Keyboard-highlighted item | `[role="menuitem"][data-highlighted]` |

Scope dropdown rules under `.softr-topbar` (Softr renders the header menu *inside* the nav) so they don't bleed into other Radix menus elsewhere in the app. Use `!important` + the `.softr-topbar` scope to beat Softr's own class rules.

## Recipe: restyle the top bar

```css
/* Bar surface */
.softr-topbar {
  background-color: #02006C !important;          /* your brand deep color */
  border-bottom: 1px solid #1E1666 !important;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25) !important;
}

/* Nav items: brand font, pill, your text color */
.softr-topbar .softr-nav-link,
.softr-topbar .softr-nav-button {
  font-family: var(--brand-font-display) !important;
  color: #FFFFFF !important;
  border-radius: 9999px !important;
}

/* Icons (currentColor SVGs) + labels carry their OWN color — force them to follow the link.
   Without this, labels render in Softr's default muted grey even after you set `color`. */
.softr-topbar .softr-nav-link *,
.softr-topbar .softr-nav-button * { color: inherit !important; }

/* Spacing — pills can end up touching; margin works regardless of the menubar's display type */
.softr-topbar [role="menubar"] .softr-nav-link,
.softr-topbar [role="menubar"] .softr-nav-button { margin: 0 4px !important; }

/* Single out ONE item as a CTA by its href (the only stable way to target one nav item) */
.softr-topbar .softr-nav-link[href*="your-form-host"] {
  background: #9B23D0 !important;
  color: #FFFFFF !important;
  box-shadow: var(--brand-shadow-cta-glow) !important;
}
```

### Gotchas (verified June 2026)

- **Nav font defaults to Inter.** Your brand `@font-face`/`<link>` loads globally, but the bar's `font-family` is set on Softr's classes — you must target `.softr-nav-link` / `.softr-nav-button` to change it.
- **Icon + label color** comes from Softr's classes, so a plain `color:` on the link often doesn't take — use the `* { color: inherit !important }` trick above (SVGs use `currentColor`, so they follow too).
- **Custom code renders on the PUBLISHED app only — not in the Studio editor.** The header looks unchanged in the builder; always verify on the live app.
- **Account avatar on a dark bar:** Softr's logged-in account button can blend into a dark bar — give it a contrasting ring if you darken the surface.

## Gotcha: dropdown panel has a tall blank gap below the items

Softr lays dropdown items in a **CSS grid** with `grid-auto-flow: column` and a **fixed set of pre-sized row tracks** (`grid-template-rows: 60px 60px 60px…`). With only 2–3 items the extra rows stay empty → a tall panel with dead space. **`height: auto` does NOT fix it** — the grid template defines those tracks. Override the flow instead:

```css
.softr-topbar [role="menu"],
.softr-topbar [role="menu"] > div,
.softr-topbar [role="menu"] [role="group"] {
  height: auto !important;
  min-height: 0 !important;
  grid-auto-flow: row !important;       /* one item per row */
  grid-template-rows: none !important;  /* drop the reserved empty tracks */
  grid-auto-rows: auto !important;
}
/* leave grid-template-columns alone — it sets the menu width */
```

Center each item's text and drop the empty description slot Softr reserves:

```css
.softr-topbar [role="menu"] [role="menuitem"] { display: flex !important; align-items: center !important; }
.softr-topbar [role="menu"] [role="menuitem"] div:empty { display: none !important; }
```

## Floating "island" header

To turn a full-bleed bar into a floating, rounded "island" (inset from the edges): make the sticky root + Softr's Studio wrappers transparent so only the bar paints, then constrain + round + shadow the bar itself.

```css
/* The sticky root and its Studio wrappers paint full-width — clear them so only the
   bar shows, floating over the page. */
#topbar-root,
#topbar-root > div,
#topbar-root > div > div { background: transparent !important; }

#topbar-root { padding: 24px 16px 0 !important; }   /* gap above + at the sides */

.softr-topbar {
  max-width: 1200px !important;
  margin: 0 auto !important;          /* center the island */
  border-radius: 22px !important;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28) !important;
}

/* Optional: group the nav cluster toward the right-of-center */
.softr-topbar [role="menubar"] { justify-content: flex-end !important; }
```

## Footer

**The native footer has NO `softr-*` class — only `f8f11e5_*` hashes.** Target the semantic **`<footer>`** element instead. Safe: Vibe Coding blocks are shadow-DOM isolated, so `footer { … }` reaches only Softr's native footer, never a block.

```css
footer {
  max-width: 1200px !important;
  margin: 24px auto !important;            /* inset → elevated "island" card */
  border-radius: 22px !important;
  background-color: #02006C !important;    /* e.g. navy, to match a navy header island */
  color: #FFFFFF !important;
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.18) !important;
}
footer * { color: inherit !important; }    /* recolor all footer text/links white in one shot */
```

**Footer contact column wraps the email mid-word.** Softr pins that column to a fixed `width: 160px` with `overflow-wrap: break-word`, so a long email splits across lines. Fix by no-wrapping the links (target by their stable `tel:` / `mailto:` href) and letting the column grow to content:

```css
footer a[href^="tel:"],
footer a[href^="mailto:"] { white-space: nowrap !important; }
footer [role="list"],
footer [role="list"] > div,
footer [role="list"] > div > div {
  width: auto !important;
  min-width: max-content !important;
  max-width: none !important;
}
```

## Page background

**The trickiest one — Softr paints the SAME fill on FOUR stacked layers:** `html`, `body`, `#page-content` (stable id; classes `content spr-content-root`), AND a deeper **class-less wrapper div** nested a few levels inside `#page-content`. Style any one layer and the ones above cover it — this is why setting `body` alone appears to "do nothing."

**Pattern: paint the backdrop on the bottom layer (`html`), then clear the duplicate fills off everything stacked above it.**

```css
/* 1. Paint the backdrop on the bottom layer. A layered "combo" reads premium:
      soft glow + faint dot-grid + base gradient. background-image order = top→bottom. */
html {
  background-color: #F0F3FC !important;   /* fallback base */
  background-image:
    radial-gradient(75rem 42rem at 50% -12%, rgba(155, 35, 208, 0.08), transparent 60%),  /* glow */
    radial-gradient(rgba(2, 0, 108, 0.045) 1px, transparent 1.6px),                        /* dot-grid */
    linear-gradient(180deg, #E7EAFB 0%, #F2F4FD 45%, #FAFBFF 100%) !important;             /* gradient */
  background-size: 100% 100%, 24px 24px, 100% 100% !important;
  background-repeat: no-repeat, repeat, no-repeat !important;
  background-attachment: fixed !important;   /* calm while content scrolls */
}

/* 2. Clear the duplicate fills stacked above <html> so the backdrop shows through —
      but EXCLUDE the header subtree (see gotcha). The inner content wrapper is
      class-less and nested deep, so clear ALL divs inside #page-content. */
body,
#page-content { background-color: transparent !important; background-image: none !important; }
#page-content div:not(.softr-topbar):not(.softr-topbar *) {
  background-color: transparent !important;
  background-image: none !important;
}
```

**Gotcha — don't clear the header into oblivion.** The header (`#topbar-root` → `.softr-topbar`, *including its dropdown panel*) renders **inside** `#page-content`, so a blanket `#page-content div { background: transparent }` flattens the dropdown's white panel too. And `#page-content`'s **id specificity (1,0,1) out-specifies** class/attr rules like `.softr-topbar [role="menu"]` (0,2,0) — so the clear wins silently and your earlier menu styling vanishes. Always exclude the header subtree: `:not(.softr-topbar):not(.softr-topbar *)`. (Cards are shadow-DOM blocks → their backgrounds are untouched; the footer is a `<footer>`, not a div → safe.)

## Finding the element to target

**Transient menus** (close on blur) — DevTools can't right-click them. Freeze: in the Console run `setTimeout(function () { debugger; }, 4000)`, open the menu within 4s, then — paused — element-pick the panel and read the **Computed** tab. Resume with the ▶ button. ("Emulate a focused page" in the Elements `:hov` menu is a lighter alternative.)

**Which element paints a background** — the element-picker keeps grabbing a *transparent* overlay sitting on top, so scan instead. Paste this in the Console; it lists `html`, `body`, and every large element with a real background color (tag / id / class / color / size), so you can spot the actual painter and its stable hook:

```js
(function () {
  var hits = [];
  var all = document.querySelectorAll('html, body, body *');
  for (var i = 0; i < all.length; i++) {
    var el = all[i], bg = getComputedStyle(el).backgroundColor, r = el.getBoundingClientRect();
    if (bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent' &&
        (el === document.documentElement || el === document.body || (r.width > 1200 && r.height > 400))) {
      hits.push({ tag: el.tagName.toLowerCase(), id: el.id || '',
        cls: (typeof el.className === 'string' ? el.className : ''),
        bg: bg, size: Math.round(r.width) + 'x' + Math.round(r.height) });
    }
  }
  console.table(hits);
})();
```

## Restyle vs. replace vs. block-owned header

**Restyle the native bar (recommended):** robust, global, keeps Softr's auth-aware nav (account menu, user-group-gated items) and stays editable in Studio.

**Replace it** (hide `#topbar-root`, inject a fully custom HTML/JS header globally): only if you need structure the native nav can't do — e.g. multi-column mega-menus with icon cards. It's **fragile**: you lose Softr's logged-in account menu + user-group gating, you must re-init the JS on every SPA route change (Softr swaps pages without a full reload), and the custom header won't render in the Studio editor. Steer users to restyle unless the structure genuinely requires replacement.

**Block-owned header (landing pages only):** on a marketing/landing page where the native header is **hidden in Studio**, a full-bleed hero block can render its own `<header>` with `position: fixed` — fixed elements inside a block's shadow root still anchor to the viewport, and window scroll listeners work from block code. Proven by Softr Studio AI's own hero output (2026-08-31), and the official user guide lists "a page header" as a supported static layout. How the replace-option caveats transfer: **per-page only** and **no auth-aware nav / user-group gating** carry over (same losses as replacing globally — it's for public landing pages, not logged-in app pages); **"won't render in the Studio editor" does NOT** (a Vibe-block header renders in Studio like any block); **"manual SPA re-init" does not apply** (React owns the block's lifecycle). Two caveats of its own: don't ship it on a page where the native `#topbar-root` is still visible (the z-index contest between the block's header and the native sticky bar is untested — hide one), and it exists only on pages containing the block. Full pattern, mobile-nav requirement, and caveat set: [static-blocks.md](static-blocks.md#block-owned-landing-page-header).

Decision order: restyle when the native structure suffices → block-owned header for landing pages that hide native chrome → global replacement only when a logged-in app needs structure the native nav can't do.

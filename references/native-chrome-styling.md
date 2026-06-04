# Styling Softr's Native Chrome (Header / Top Bar / Nav / Dropdowns)

**This is NOT about Vibe Coding blocks.** Softr's top bar, navigation, and its dropdown menus are *native chrome* — configured in Softr Studio and rendered in the **main document**, not inside a block's shadow DOM. You **cannot** build or replace the global header as a Vibe Coding block. To re-skin it, add **CSS to Settings → Custom Code → Code inside header** (the same place brand fonts/tokens live, i.e. the `custom-code-header.html` produced by `building-design-md`). Pure CSS — no markup, no JS — and the native bar stays in place, so Softr's auth-aware nav (account menu, sign-out, user-group gating) keeps working.

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

## Finding the element to target

DevTools can't right-click a menu that closes on blur. Freeze it: in the Console run `setTimeout(function () { debugger; }, 4000)`, open the menu within 4s, then — paused — element-pick the panel and read the **Computed** tab to see which element holds a fixed `height` / `grid-template-rows`. Resume with the ▶ button. ("Emulate a focused page" in the Elements `:hov` menu is a lighter alternative for blur-close menus.)

## Restyle vs. replace

**Restyle the native bar (recommended):** robust, global, keeps Softr's auth-aware nav (account menu, user-group-gated items) and stays editable in Studio.

**Replace it** (hide `#topbar-root`, inject a fully custom HTML/JS header globally): only if you need structure the native nav can't do — e.g. multi-column mega-menus with icon cards. It's **fragile**: you lose Softr's logged-in account menu + user-group gating, you must re-init the JS on every SPA route change (Softr swaps pages without a full reload), and the custom header won't render in the Studio editor. Steer users to restyle unless the structure genuinely requires replacement.

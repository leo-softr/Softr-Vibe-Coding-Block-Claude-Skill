# Styling Softr's Native Shell (Header · Sidebar · Footer · Page Background · App Frame) via Custom Code

**This is NOT about Vibe Coding blocks.** Softr's top bar, sidebar, phone tab bar, navigation, dropdown menus, footer, and the page background are part of the *native app shell* — configured in Softr Studio and rendered in the **main document**, not inside a block's shadow DOM. You **cannot** build or replace the native chrome itself as a Vibe Coding block. To re-skin it, add **CSS to Settings → Custom Code → Code inside header** (the same place brand fonts/tokens live — house convention keeps that CSS in a `custom-code-header.html` file in the project folder and pastes it into the setting; you author it from the project's DESIGN.md tokens, since dembrandt supplies the palette and webfont URLs but generates no Softr-ready CSS — see [dembrandt.md](dembrandt.md#authoring-custom-code-headerhtml-from-designmd)). Pure CSS — no markup, no JS — and the native chrome stays in place, so Softr's auth-aware nav (account menu, sign-out, user-group gating) keeps working. (Separate pattern, different problem: a landing page with the native header **hidden** can carry a block-owned in-block header — see [Restyle vs. replace vs. block-owned header](#restyle-vs-replace-vs-block-owned-header).)

This doc covers the **header / nav / dropdowns**, the **footer**, the **floating "island" treatment** for both, the **page background** — which is trickier than it looks, because Softr stacks the same fill on several layers — and the **app frame**: in an app with Softr's sidebar navigation, painting around the top bar and sidebar so the content reads as one sheet inside them ([App frame](#app-frame-navigation-layout)).

> **Mirror of the block rule.** Global `custom-code-header.html` CSS reaches native chrome (main document) but **not** blocks (shadow DOM). Inside a block you apply brand styles inline; for native chrome you apply them with this global CSS. (See [anti-patterns.md](anti-patterns.md) for the block side.) Of a Vibe block it reaches only the **host `<div>`**, which sits in the main document — that is how the app frame makes a block's background transparent — never anything inside the shadow root. Native Softr blocks render in the main document, so it reaches them whole.

## Selector discipline — the #1 rule

Softr's rendered markup carries two kinds of names:

- **Hashed build classes** like `f8f11e5_m9ntthp` — **NEVER target these.** Softr regenerates the hash on every deploy, so your rules silently die.
- **Hashed CSS variables** like `--_5f91d6c_vnohg20` — same rule: **never target them and never `var()` them.** Softr's theme colours reach the page through these (the sidebar fill, the theme background), so when you need a theme value, copy it by hand and keep it in your own token ([App frame](#app-frame-navigation-layout) does this). The prefix belongs to a **native block package**, not to the app: on 2026-10-05 the prefixes carried a leading underscore, `_5f91d6c_` on the navigation and 404 blocks and `_03ef538_` on the Account settings (user-accounts) block; the June 2026 notes recorded `f8f11e5_` without one. Don't hard-code a prefix either; it regenerates with the hash.
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
| Active-link underline | `.softr-nav-link::before` — a 2px bar 41px down the 56px bar (verified live 2026-10-05) |
| Open dropdown trigger | `.softr-nav-button[aria-expanded="true"]` |

**Navigation-layout shell** — apps whose Studio navigation puts a sidebar beside the content (seen in one such app's `featureFlags` as `navigationLayout: true`; whether the flag marks sidebar apps is untested, so test for `.softr-sidebar` instead). All verified live 2026-10-05:

| Element | Stable selector | Notes |
|---|---|---|
| Page grid | `#page-content` (classes `content spr-content-root`) | CSS grid: `grid-template-areas: "topbar topbar" "sidebar main" "bottombar bottombar"`, `grid-template-columns: auto minmax(0, 1fr)`. Children: the three roots below, the navigation placeholder and `#main-content` |
| Top bar root | `#topbar-root` | grid-area `topbar`; sticky, top 0, z-index 800; the bar is 56px tall |
| Sidebar root | `#sidebar-root` | sticky, top 56px, z-index 1 (static on phones). **Also present on phones, empty and 0px wide** — scope rules on `.softr-sidebar`, never on this id |
| Sidebar | `.softr-sidebar[data-testid="sidebar"]` | Paints the Studio theme colour. `[data-open="true"]` 280px by default; `[data-open="false"]` 57px, collapsed from the top-bar toggle |
| Sidebar resize handle | `.softr-sidebar > [role="separator"]` | Drag range 200–360px (`aria-valuemin` / `aria-valuemax`). Softr already keeps it at opacity 0 until hover — no CSS needed to hide it |
| Sidebar toggle | the top-bar `<button>` holding a visually hidden span "Toggle sidebar" | No `aria-label` and no `softr-*` class; find it by that text in scripts and tests |
| Phone tab bar root | `#bottombar-root` | sticky (not fixed), z-index 800. Also present on desktop, 0px tall |
| Phone tab bar | `ul.softr-bottombar[data-testid="bottombar"]` | Only below a 768px window. White; items are `a.softr-nav-link[data-active]`, plus buttons that open dialogs (`aria-haspopup="dialog"`) |
| Content column | `main#main-content` | grid-area `main`; `display: flex; flex-direction: column; min-height: 100dvh`; transparent. Every block's wrapper is a child of it |
| Navigation placeholder | `.spr-navigation-placeholder` | The nav block's own node, 0×0; its UI renders into the three roots, so there is nothing to style here |

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
- **Header custom code renders on the published app AND in Softr's preview — not in the Studio editor.** The preview half is verified live 2026-10-05: a fresh preview load, with nothing injected, applied the app-level header code (seen after a publish; whether the preview shows a pasted but unpublished change is untested — inject it instead, see [browser-checks.md](browser-checks.md#testing-custom-code-header-css)). The editor canvas is still not known to render it: the header looks unchanged in the builder, so check in preview or on the live app.
- **Confirm the code is live from the page source (verified live 2026-10-05).** The published page's HTML carries the app-level code as `appCustomHeaderCode: "…"` inside `SoftrPageRenderer.render({…})` — an unquoted key in an inline script, not a JSON key, so search for `appCustomHeaderCode:` without quotes around the key. `appCustomHeaderCode: ""` means nothing is published. Every page carries it, `/login` and a 404 page too, so a logged-out fetch of the published app is enough. `pageCustomHeaderCode` sits beside it: **page-level** header code also exists, so check it too when a page behaves differently from the rest. To test CSS before it is pasted, see [browser-checks.md](browser-checks.md#testing-custom-code-header-css).
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

## Relocating footer nodes, not just restyling them

CSS alone cannot move an element to a **different parent**. `order` only reorders siblings, so a
"put the Website / Terms links down on the copyright line" request — where the links and the copyright
live in different containers — needs a small JS relocation job in the same Custom Code block, not more
selectors.

The shape that works:

1. Build one flex row, insert it where the copyright currently sits.
2. Move the copyright node into it, then the link nodes after it.
3. Hide the container the links vacated **only if it is now genuinely empty** — check for remaining
   element children rather than assuming, or you will blank a container that still holds something.
4. Run it BEFORE any job that measures height (a footer-compacting pass, a sticky offset calculation);
   those must see the final arrangement or they measure the old one.

```js
/* relocate, then compact — order matters: compactFooter() measures height */
relocateFooterLinks();
compactFooter();
```

Two details worth copying:

- **Truncate rather than wrap.** A relocated row should ellipsise under width pressure
  (`min-width:0` on the flex children plus `text-overflow:ellipsis`), never stack — a footer row that
  reflows to two lines at an awkward width looks broken in a way a clipped label does not.
- **Scope hover underlines away from logos and icons.** An `::after` underline scaled from
  `transform-origin:50%` gives a centre-out grow; gate it with `:not(:has(svg)):not(:has(img))` so it
  never appears under the logo or the social glyphs, and use `currentColor` so the footer's own colour
  rules keep working untouched.

Same caveat as everything else here: **it does not render in the Studio editor.** The editor keeps
showing the old arrangement, which reads exactly like "the script did not run." Check on the published
app (Softr's preview applies header code too; verified for CSS after a publish on 2026-10-05, not for a script).

## Page background

**The trickiest one — Softr paints the SAME fill, the Studio theme background, on several stacked layers.** Measured live 2026-10-05:

| Layer | What paints it |
|---|---|
| `html`, `body` | the theme background |
| `#page-content` (stable id; classes `content spr-content-root`) | Softr's `.spr-content-root { background-color: … }` rule |
| every Vibe block host, `div[data-role="vibe-block-root"]` — it has no class: most likely the "class-less wrapper div" the June 2026 notes found (inferred; that app was not re-measured) | the block's compiled `@layer base { :host { background-color: var(--background) } }`, where `--background` maps to the theme background through a hashed variable. Not `!important`, so a main-document rule on the host wins |
| a native block's outer `<section>` | an inline hashed variable holding the theme background |

`main#main-content` itself is transparent. Style any one layer and the ones above cover it — this is why setting `body` alone appears to "do nothing", and why a block that sets no background still shows the theme white over a coloured `body`.

> **App with Softr's sidebar navigation? Use [App frame](#app-frame-navigation-layout), not this recipe.** The clear below hits every `div` inside `#page-content`. `.softr-sidebar` is one of them and paints the theme colour, so it would lose its fill too (inferred from the DOM and specificity, not injected). And native blocks' outer `<section>`s are not divs, so they keep painting the theme white.

**Pattern (top-bar apps): paint the backdrop on the bottom layer (`html`), then clear the duplicate fills off everything stacked above it.**

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
      but EXCLUDE the header subtree (see gotcha). The block hosts are class-less
      divs nested inside #page-content, so clear ALL divs inside it. */
body,
#page-content { background-color: transparent !important; background-image: none !important; }
#page-content div:not(.softr-topbar):not(.softr-topbar *) {
  background-color: transparent !important;
  background-image: none !important;
}
```

**Gotcha — don't clear the header into oblivion.** The header (`#topbar-root` → `.softr-topbar`, *including its dropdown panel*) renders **inside** `#page-content`, so a blanket `#page-content div { background: transparent }` flattens the dropdown's white panel too. And `#page-content`'s **id specificity (1,0,1) out-specifies** class/attr rules like `.softr-topbar [role="menu"]` (0,2,0) — so the clear wins silently and your earlier menu styling vanishes. Always exclude the header subtree: `:not(.softr-topbar):not(.softr-topbar *)`.

**What the div clear reaches.** Each Vibe block's **host** div — that is what removes the block's theme white — but nothing inside its shadow root, so a block's own cards and panels keep the fills the block sets. It never reaches native blocks' outer `<section>`s, which keep painting the theme background; the outer-section rule in [App frame](#app-frame-navigation-layout) is the fix (untested outside a sidebar app). The footer is a `<footer>`, not a div → safe.

## App frame (navigation layout)

**When:** the app uses Softr's **sidebar navigation** (top bar + sidebar from a 768px window, a tab bar below it) and should read as **one application**, not as blocks stacked on a white page. The bars' theme colour wraps the content as a frame, and the content becomes one paper **sheet** whose top-left corner curves in under the top bar and the sidebar.

**The method: the header CSS paints the frame and the sheet; blocks paint nothing.** Leave the top bar and sidebar exactly as the theme draws them. Nothing needs hiding: the top bar has no border or shadow, and the sidebar's inner border is transparent (verified live 2026-10-05). The CSS extends the bars' colour to `html`, `body` and `#page-content`, turns `#main-content` into the sheet, and makes block hosts transparent. Each block on such a page is full-bleed, sets no background of its own and lays out by its own width — the block side is in [SKILL.md](../SKILL.md#app-pages-beside-softr-navigation). The header CSS cannot reach inside a block, so a block's own cards and borders are still set in the block.

### DOM and variables (verified live 2026-10-05)

The shell selectors are in the [navigation-layout table](#selector-discipline--the-1-rule) above. Below `#main-content`:

- A Vibe block: `#main-content > div[data-block="vibe-coding-…"] > div[data-block-id] > div[data-role="vibe-block-root"]`. The last div is the **host**, with an open shadow root.
- A native block: `#main-content > div#<block id> > div > section` for the Account settings block; the 404 block is one level shallower (see the caveats).

Variables Softr sets on `:root`:

| Variable | Top bar + sidebar (window ≥ 768px) | Phone (window < 768px) |
|---|---|---|
| `--sticky-nav-height` | `56px` | empty |
| `--softr-sidebar-width` | `280px`; `57px` collapsed (drag handle range 200–360) | empty |
| `--softr-bottombar-height` | empty (blocks read 0px) | `calc(0px + 55px)` — the raw token, not a computed length |

Each Vibe host maps them for the block: `--nav-height: var(--sticky-nav-height, 0px)`, `--sidebar-width: var(--softr-sidebar-width, 0px)`, `--bottombar-height: var(--softr-bottombar-height, 0px)` (the block-side table: [quick-reference.md → Softr navigation variables](quick-reference.md#softr-navigation-variables)). Blocks use those inside CSS `calc()` ([common-patterns.md](common-patterns.md#clear-softrs-sticky-bars)). The variable says 55px for the tab bar; the rendered bar measured 57px tall.

**The layout switches on the window width, exactly at 768px:** 767px gives the phone tab bar, 768px gives the top bar and sidebar.

### The recipe

Paste into Settings → Custom Code → Code inside header (every page). That setting takes HTML, so the rules go inside a `<style>` element, as below. Rule order matters: keep it as written.

```html
<style>
/* App frame. Pages with Softr's navigation: the bars' colour becomes a frame around one content sheet.
   Pages without it (Log in, Sign up, 404) match none of these rules and keep Softr's own colours. */
:root {
  --app-frame: #A85935;   /* a COPY of the Studio theme colour of the top bar + sidebar (hashed vars can't be
                             referenced). Change it by hand whenever the theme colour changes in Studio. */
  --app-sheet: #FBF8F3;   /* the app's paper colour (e.g. the DESIGN.md surface) */
  --app-radius: 24px;     /* the corner where the sheet meets the frame */
}

/* 1. Any page with Softr navigation (sidebar OR phone tab bar): one paper surface. */
html:has(.softr-sidebar, .softr-bottombar),
html:has(.softr-sidebar, .softr-bottombar) body,
#page-content:has(.softr-sidebar, .softr-bottombar) {
  background-color: var(--app-sheet) !important;
}

/* ...and blocks stop painting the theme background on top of it:
   - Vibe block hosts: their compiled :host { background-color: var(--background) } is not !important.
     This scoped form is UNTESTED as written. The line verified live was the unscoped
     #main-content [data-role="vibe-block-root"], which also applies on pages without navigation.
   - Native blocks: the OUTER <section> only, so their nested cards, list items and form groups keep their
     fills. Nesting depth differs per native block; check yours (see the caveats). */
#page-content:has(.softr-sidebar, .softr-bottombar) [data-role="vibe-block-root"],
#page-content:has(.softr-sidebar, .softr-bottombar) #main-content > div > div > section {
  background-color: transparent !important;
}

/* 2. With the sidebar (window ≥ 768px): the frame colour behind everything.
   Same specificity as rule 1, so it MUST come after it; phones (tab bar only) keep the paper. */
html:has(.softr-sidebar),
html:has(.softr-sidebar) body,
#page-content:has(.softr-sidebar) {
  background-color: var(--app-frame) !important;
}

/* The content column becomes the sheet. Softr's own min-height: 100dvh fills short pages. */
#page-content:has(.softr-sidebar) > #main-content {
  background-color: var(--app-sheet) !important;
  border-top-left-radius: var(--app-radius);
}

/* 3. The pinned inverse corner. #main-content's own radius scrolls away with the page; this one rides
   the sticky #sidebar-root (its containing block), so it stays under the top bar while the content
   scrolls and follows the sidebar's width. Guarded by :has(.softr-sidebar) because #sidebar-root
   also exists on phones, empty and 0px wide. */
#sidebar-root:has(.softr-sidebar)::after {
  content: "";
  position: absolute;
  top: 0;
  left: 100%;
  width: var(--app-radius);
  height: var(--app-radius);
  background: radial-gradient(circle at 100% 100%,
    transparent calc(var(--app-radius) - 0.5px),   /* the -0.5px stop: anti-aliased edge, no seam */
    var(--app-frame) var(--app-radius));
  pointer-events: none;                             /* never blocks clicks on the sheet */
}
</style>
```

### Caveats

- **Decide where the menu lives first.** If the Studio menu items sit in the top bar, `.softr-sidebar` renders as an empty coloured column, and the frame reads as a blank strip (seen live 2026-10-05). For the full "app" look, put the menu in the sidebar in Studio; that variant was not built or seen, so check it.
- **The frame colour is a hand copy.** The bars paint the Studio theme colour (e.g. `#A85935`) through hashed variables, so `--app-frame` cannot reference it. Read it off the page, `getComputedStyle(document.querySelector('.softr-sidebar')).backgroundColor`, rather than taking the DESIGN.md primary: the two can differ, and in the verified app they did. If the theme colour changes in Studio and `--app-frame` does not, the frame and the bars split.
- **Rule order.** Rule 2 has the same specificity as rule 1. Put it first and sidebar pages lose the frame.
- **The Vibe-host rule's scope.** The live code used the unscoped `#main-content [data-role="vibe-block-root"]`, which applies on every page. That is harmless where the page behind the block is the same theme background (inferred; no page without navigation but with a Vibe block was tested). The recipe scopes it like every other rule; that exact form is untested.
- **Native blocks' outer section.** The child path `#main-content > div > div > section` matches the DOM measured on the Account settings block, but it was never re-injected in that form: the descendant form `#main-content section` was injected there and turned the section transparent. Nesting depth differs per native block: the 404 block's section sits one level shallower (`#main-content > div > section`), which does not matter there (no navigation). For each native block type on a navigation page, check the depth first; fall back to the descendant form only after checking the block holds no nested `<section>`s. **Side effect:** on navigation pages this overrides a background colour set on purpose in a native block's Style settings. A no-CSS alternative, setting the Studio theme background to the sheet colour, is untested.
- **Phones (window < 768px).** Softr renders no top bar and no sidebar, only the tab bar: white, with the active item in the theme colour. Only rule 1 matches, so the page is paper throughout with no frame and no corner (the guarded `::after` computes `content: none`); `#main-content` stays transparent and the paper is on `html`, `body` and `#page-content`. Without the guard the `::after` still renders on phones, where `#sidebar-root` is static, so it is placed against the page: likely off the right edge, adding sideways scroll (seen in a mock, not on Softr). Restyling the tab bar to match the frame is untested.
- **Tablets.** The bars appear from a 768px window. With the sidebar open, the content column there is only 488px wide (711px collapsed), so a block's window breakpoints fire for a column far narrower than the window. Blocks must size by their own width: [SKILL.md](../SKILL.md#app-pages-beside-softr-navigation), [common-patterns.md](common-patterns.md#measure-the-block-not-the-window).
- **Collapsed and resized sidebar.** The top-bar toggle collapses the sidebar to 57px (`data-open="false"`, `--softr-sidebar-width: 57px`), and the corner follows it (measured at left 280px open, 57px collapsed). Drag-resizing (200–360px) was not tested; that the corner follows is inferred from `left: 100%`. In one headless run the collapsed state carried over to later checks (seen once; it may persist per browser).
- **Stacking.** `#topbar-root` and `#bottombar-root` sit at z-index 800 and `#sidebar-root` at 1; block content scrolls under the top bar. A block's own sticky pane or header must clear the bars: [common-patterns.md](common-patterns.md#clear-softrs-sticky-bars). Softr already sets `#main-content [data-block] { scroll-margin-top: var(--sticky-nav-height, 0px) }`, so a fragment jump to a block's outer wrapper (`div[data-block]`, with a page-assigned id such as `ai1`; the host sits two levels inside it) clears the top bar (the rule is read from Softr's CSS; a jump was not tested). Softr's floating "Made with Softr" badge (`div.made-with-softr`, fixed, z-index 1, 296px from the left beside a 280px sidebar) floats over the bottom left of the content on desktop and phones (seen in the preview). It is controlled by the app's badge setting (`showMadeWithBadge` in the page source; `false` after a later publish of the same app), so turn it off there rather than with CSS.
- **`:has()` support.** Every scoped rule needs `:has()`: Safari 15.4+, Chrome 105+, Firefox 121+ (a reviewer's judgement, not tested on each browser). A browser without it drops those rules and shows Softr's default colours (inferred).

### How the frame was verified

Verified 2026-10-05 on a demo app with Softr's navigation layout. First by injecting the project's `<style>` (the recipe above, except that its Vibe-host rule was the unscoped form) into the preview and measuring computed backgrounds, the sheet's radius and the `::after` position at 1440, 1280, 1024, 900, 768, 767 and 390px windows, with the sidebar open and collapsed; the corner was cropped at rest and scrolled, with no seam. Then live, after the code was pasted into Code inside header and published:

- **Preview, fresh load, nothing injected.** At 1024px with the sidebar open: frame on `html`, `body` and `#page-content`; `#main-content` the sheet with a 24px corner; Vibe hosts transparent; the corner `::after` at left 280px. At 375px (after a mobile emulation and a reload): tab bar only, paper throughout, no corner. No sideways scroll at either width.
- **Published, logged out.** `/login` and a 404 page loaded the code and kept `html`, `body` and `#page-content` white, with no top bar, sidebar or tab bar. This is the real test of the `:has()` scoping.

How to run these checks: [browser-checks.md](browser-checks.md#testing-custom-code-header-css).

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

In an app with Softr's sidebar, lower the `1200`: the content column is the window minus the sidebar (1160px at a 1440px window), so block hosts and native sections drop out of the list otherwise.

## Restyle vs. replace vs. block-owned header

**Restyle the native bar (recommended):** robust, global, keeps Softr's auth-aware nav (account menu, user-group-gated items) and stays editable in Studio.

**Paint around the bars (apps with sidebar navigation):** leave the top bar and sidebar exactly as the Studio theme draws them, and extend their colour around a content sheet: `html`, `body` and `#page-content` take the bars' colour, `#main-content` becomes one paper sheet with a rounded corner tucked under both bars, and blocks paint nothing behind themselves. Choose it when the app uses Softr's top bar + sidebar and should read as one application rather than blocks on a white page. It keeps everything restyling keeps (auth-aware nav, Studio editing) and touches no nav markup. It can sit beside a restyle only if `--app-frame` matches the colour the restyled bars then paint (untested combination). Recipe, scoping and caveats: [App frame](#app-frame-navigation-layout).

**Replace it** (hide `#topbar-root`, inject a fully custom HTML/JS header globally): only if you need structure the native nav can't do — e.g. multi-column mega-menus with icon cards. It's **fragile**: you lose Softr's logged-in account menu + user-group gating, you must re-init the JS on every SPA route change (Softr swaps pages without a full reload), and the custom header won't render in the Studio editor. Steer users to restyle unless the structure genuinely requires replacement.

**Block-owned header (landing pages only):** on a marketing/landing page where the native header is **hidden in Studio**, a full-bleed hero block can render its own `<header>` with `position: fixed` — fixed elements inside a block's shadow root still anchor to the viewport, and window scroll listeners work from block code. Proven by Softr Studio AI's own hero output (2026-08-31), and the official user guide lists "a page header" as a supported static layout. How the replace-option caveats transfer: **per-page only** and **no auth-aware nav / user-group gating** carry over (same losses as replacing globally — it's for public landing pages, not logged-in app pages); **"won't render in the Studio editor" does NOT** (a Vibe-block header renders in Studio like any block); **"manual SPA re-init" does not apply** (React owns the block's lifecycle). Two caveats of its own: don't ship it on a page where the native `#topbar-root` is still visible (the z-index contest between the block's header and the native sticky bar is untested — hide one), and it exists only on pages containing the block. Full pattern, mobile-nav requirement, and caveat set: [static-blocks.md](static-blocks.md#block-owned-landing-page-header).

Decision order: restyle when the native structure suffices (or paint around the bars when a sidebar app should read as one application) → block-owned header for landing pages that hide native chrome → global replacement only when a logged-in app needs structure the native nav can't do.

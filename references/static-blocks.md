# Static Marketing Blocks — Heroes, Landing Sections, and the Editorial Lane

A **static block** is a Vibe Coding block with **zero datasources**: all content comes from editable settings, nothing loads, nothing mutates. Officially blessed — Softr's user guide lists "a static layout like a page header, pricing table, or content section" as a first-class use of the Vibe Coding block. Typical members: hero sections, landing-page headers, pricing tables, testimonial bands, logo walls, FAQ sections, footers, content/feature sections.

This archetype inverts most of the skill's data-block defaults, so read this file INSTEAD of the datasource guides when the requested block is static marketing content. (Verified against a Studio-AI-generated hero rendering live in Studio, 2026-08-31.)

## Contents

- [Workflow deltas](#workflow-deltas)
- [Editorial baseline (replaces the Premium Visual Baseline)](#editorial-baseline-replaces-the-premium-visual-baseline)
- [Full-bleed layout license](#full-bleed-layout-license)
- [Full-viewport hero sizing](#full-viewport-hero-sizing)
- [Block-owned landing-page header](#block-owned-landing-page-header)
- [Section anchors on landing pages](#section-anchors-on-landing-pages)
- [Harvesting Studio-AI marketing blocks](#harvesting-studio-ai-marketing-blocks)

## Workflow deltas

When the block is static marketing content:

- **SKIP data-source interrogation entirely** — no data source type question, no field IDs, no datasource guide loading. Step 1 (DESIGN.md brand detection) still runs unchanged.
- **Settings-first design is the default** — every user-visible string, image, and link becomes an editable setting; see the granularity doctrine in [editable-settings.md](editable-settings.md#granularity-doctrine-settings-first-static-blocks). This is what makes the block a reusable, client-editable template instead of frozen copy.
- **Self-validation deltas** — these Step 6 checklist items DON'T apply: loading/error/empty states (nothing loads), `getFieldValue()` wrapping (no records), mutation `enabled` gating, `fetchNextPage` rules, container/content wrappers (see full-bleed below). These DO apply, plus extras: hooks before conditional returns, module-scope sub-components, no hardcoded user-visible copy, media settings gated for the empty-src state, array rows keyed by index, `// BLOCK PLACEMENT:` comment present.
- **Ask-AI buttons still need a data source.** The one place a "static" block touches data: an `OPEN_CHAT` NavigationAction pulls AI context from the block that triggered it — with no data source connected, `chat/prepare` returns HTTP 500. Connect the block to whatever table the AI should read, even though the block renders none of it. See [anti-patterns.md](anti-patterns.md#layout--styling).

## Editorial baseline (replaces the Premium Visual Baseline)

SKILL.md's Premium Visual Baseline (gradient wrapper, icon-in-rounded-square header, card grids, skeletons, empty states) is an **app-UI** baseline — applying it to a hero produces a dashboard cosplaying as a landing page. For static marketing blocks, the baseline is editorial instead:

1. **Typographic hierarchy carries the design** — display-size headings, an eyebrow/tagline, generous line-height on body copy. Use the marketing display-type lane in ui-ux-guidelines.md §6.
2. **Brand-exact values over theme tokens** — arbitrary Tailwind values (`bg-[#FAF5EC]`, `text-[17px]`, `rounded-[6px]`) and inline-style brand hexes are the correct tool here (see §7's editorial lane in ui-ux-guidelines.md). Hoist repeated hexes to module-scope constants — see [anti-patterns.md](anti-patterns.md#layout--styling).
3. **Decorative layers, used deliberately** — background blobs/shapes, edge-fade image masks, art-directed responsive images. Recipes in [common-patterns.md](common-patterns.md).
4. **No loading/empty/error scaffolding** — there is nothing to load. The only "empty" state to handle is an un-uploaded media setting ([editable-settings.md](editable-settings.md#media-hooks-useimagesetting-and-usevideosetting)).
5. **Restraint still applies** — ui-ux-guidelines.md's AI-slop bans (purple-to-blue gradients, glassmorphism everywhere, gradient text) bind in this lane too. Editorial ≠ decorated.

## Full-bleed layout license

**`container`/`content` wrappers are optional platform behavior, not platform-enforced.** Per the official developer guide: "By default, block occupies full width of the page but special classes - `container` and `content` are **available** to constrain the width [of content to match app's max width settings]" (emphasis added). The wrappers remain the strong default for app/content blocks that sit next to native blocks (width consistency — that's their whole purpose). Static marketing blocks legitimately skip them so backgrounds, images, and decorative shapes run edge-to-edge.

When you go full-bleed:

- **Own your horizontal gutters** — the responsive padding ramp `px-6 md:px-12 lg:px-16` on the content container is the Studio-verified shape.
- **Own your inner max-widths** — constrain the copy column yourself (`lg:max-w-[46%]`, `max-w-[430px]` on body text).
- **`overflow-hidden` on the block root** if decorative shapes offset off-canvas (prevents horizontal scroll).
- **Record the choice** in the placement comment so future edits and reviews know it's deliberate:

  ```tsx
  // BLOCK PLACEMENT: full-bleed hero, native header hidden, owns all spacing
  // Spacing: no container/content; gutters px-6 md:px-12 lg:px-16
  ```

The standard spacing table (`py-3 px-8` wrappers) does not apply — a full-bleed block owns all of its spacing.

## Full-viewport hero sizing

The Studio-verified responsive shape:

```tsx
<div className="relative min-h-screen lg:min-h-0 lg:h-screen lg:flex lg:flex-col ...">
  <main className="lg:flex-1 lg:flex lg:items-center ...">
```

Natural height on mobile, locked viewport height on desktop, content vertically centered in the remaining space. Rules and gotchas:

- **vh/`h-screen` resolve against the real viewport** (blocks are shadow DOM in the main document — see [Block-owned landing-page header](#block-owned-landing-page-header)). So `h-screen` fills the window only when the native header is hidden on that page; with a native header above, a 100vh block overflows by the header height. Use `min-h-[calc(100vh-<headerHeight>px)]` when native chrome stays.
- **Hard `h-screen` + `overflow-hidden` + centered flex CLIPS settings-grown content — unrecoverably.** Every string in a settings-first hero is builder-lengthenable; on a short laptop viewport, two extra sentences in the description push the CTA row past the clip, and centered-flex overflow clips top AND bottom, so no scrolling reaches it. Prefer `lg:min-h-screen` (grow-with-content) unless the locked-viewport look is explicitly wanted; if locking, flag the tradeoff to the user and keep the copy settings short.
- **Mobile URL-bar resize**: consider `min-h-[100svh]`/`dvh` variants if the mobile jump matters; the `min-h-screen` mobile default is the safe baseline.

## Block-owned landing-page header

The scope rule stays true: Softr's **native** chrome (top bar, auth-aware account menu, user-group-gated nav) cannot be built or replaced as a block — restyling it is global Custom Code territory ([native-chrome-styling.md](native-chrome-styling.md)). But on a landing page where the native header is **hidden in Studio**, a hero block CAN render its own `<header>` — Softr's own Studio AI emits exactly this, and the official user guide lists "a page header" as a supported static layout. Mechanics (rendered live in Studio 2026-08-31; the positioning behavior is standard shadow-DOM/CSS — confirm in the published app):

- **`position: fixed` works from inside the block** and anchors to the viewport — blocks render in a shadow root in the MAIN document (not an iframe), and shadow roots don't create a containing block. The header escapes the block's visual bounds and overlays every other block on the page.
- **Window scroll listeners work normally** — `window.scrollY` reflects the real page. The scroll-condensing treatment (translucent bg + backdrop-blur + border after ~24px) is in [common-patterns.md](common-patterns.md#scroll-condensing-fixed-header-landing-page-hero).

The caveat set — state these in any block that ships its own header:

1. **Per-page only.** The header exists solely on pages containing this block. Every page of a multi-page site needs either this block or the native header, or navigation disappears.
2. **No auth-aware nav logic.** You forfeit Softr's account menu and user-group-gated items — nav items are plain `<NavigationAction>`s. Fine for public landing pages; wrong for logged-in app pages. For the login CTA, use the auth-aware swap (`useCurrentUser()` → "Sign in" vs "Dashboard") from [common-patterns.md](common-patterns.md#auth-aware-header-cta).
3. **Don't ship both headers on one page.** The z-index outcome against a visible native `#topbar-root` (sticky, main document) is untested — hide the native header on this page, or don't use the pattern.
4. **Keep transforms/filters off the header's ancestors.** `position: fixed` anchors to the viewport ONLY while no ancestor establishes a containing block — a `transform`, `filter`, `perspective`, or `will-change` on the block root (e.g. an entrance animation) silently converts the "fixed" header to absolute and lets `overflow-hidden` clip it. Leaf-element transforms (`hover:-translate-y-[1px]` on buttons) are fine. Verify in the **published app**, not just the Studio canvas.
5. **Mobile nav is mandatory.** `hidden md:flex` on the nav with no fallback means nav items simply don't exist on phones (Studio AI ships exactly this bug). Pair the pattern with a shadcn `Sheet`-based mobile menu (hamburger → drawer listing the same `navItems` array) — the component is on the platform roster.
6. **Landmark hygiene.** Shadow DOM does NOT hide landmarks from assistive tech, and Softr's native chrome uses semantic elements. On a page with native chrome visible, a block's own `<header>`/`<main>` creates duplicate banner/main landmarks — use plain `<div>`s there. Reserve `<header>`/`<main>` for pages where the native chrome is hidden and the block genuinely IS the page chrome.

The wider decision (restyle native vs replace globally vs block-owned) is laid out in [native-chrome-styling.md](native-chrome-styling.md#restyle-vs-replace-vs-block-owned-header).

## Section anchors on landing pages

Heroes pair with same-page sections via hash links (nav "Capabilities" → `#capabilities` further down).

- **Write anchor destinations RELATIVE**, per Hard Constraint 20: `/#capabilities` or `/page#section`. A Studio-generated hero shipped its CTA configured as the absolute self-domain form (`https://<app>.softr.app/#capabilities`, observed in the Settings pane 2026-08-31) — rewrite that form; hardcoded domains break on custom-domain publish and between staging/production.
- **A URL fragment cannot target an element inside a Vibe block's shadow root** — fragment lookup stops at the shadow boundary (same family as the documented `getElementById` anti-pattern). Anchors must target something in the main document: the block/section host. Softr has a native anchor-link mechanism targeting blocks — **verify live which fragment a Vibe Coding block answers to** before promising exact syntax to a user.
- **In-block scrolling** (scroll to a section inside the same block) uses refs + `scrollIntoView` with the `setTimeout(fn, 0)` rule (Hard Constraint 17), not fragments.

## Harvesting Studio-AI marketing blocks

Marketing blocks are where you'll most often mine Studio-AI output for platform truth (it surfaced `useLongTextSetting` and the `navigation` array-schema type before the official docs did). Mine capabilities, never copy verbatim — the standard defects to fix on adoption are listed in SKILL.md's "Platform truth sources" note and [softr-mcp.md](softr-mcp.md#adopting-studio-ai-generated-code) (React keys, hex drift, formatting, missing mobile nav, unconditional media renders).

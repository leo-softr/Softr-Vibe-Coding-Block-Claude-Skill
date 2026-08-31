# Editable Settings — Hook Catalog, Granularity Doctrine, Undocumented Hooks & Types

Editable settings are the hooks from `@/lib/editable-settings` that surface a block's content in Studio's **Content → Settings** pane, so builders (and clients) edit text, images, links, and lists **without re-prompting or touching code**. Softr's own pitch: "make simple text and image edits directly without re-prompting." This file is the deep-dive; SKILL.md keeps the compact signatures.

**Provenance discipline.** Every behavior below is tagged either **[official]** (in Softr's Vibe Coding Developer Guide, re-fetchable via the MCP's `get_vibe_coding_docs`) or **[verified-undocumented]** (absent from the official guide but proven working — source and date given). Keep the tags when editing this file: they're what stops a future docs-based review from false-positiving working code (the same failure class as the useRecord-via-Studio-binding incident), and what tells you which behaviors could silently change under you since Softr never promised them.

## Contents

- [Hook catalog](#hook-catalog)
- [Text hooks: useTextSetting and useLongTextSetting](#text-hooks-usetextsetting-and-uselongtextsetting)
- [Media hooks: useImageSetting and useVideoSetting](#media-hooks-useimagesetting-and-usevideosetting)
- [useVibeCodingBlockIconSetting](#usevibecodingblockiconsetting)
- [useNavigationSetting](#usenavigationsetting)
- [useBooleanSetting](#usebooleansetting)
- [useArraySetting](#usearraysetting)
- [Granularity doctrine: settings-first static blocks](#granularity-doctrine-settings-first-static-blocks)
- [Naming conventions and the rename-resets-value gotcha](#naming-conventions-and-the-rename-resets-value-gotcha)
- [Constraints recap](#constraints-recap)

## Hook catalog

| Hook | Returns | Status |
|---|---|---|
| `useTextSetting` | `string` | [official] |
| `useLongTextSetting` | `string` (multi-line textarea in the pane) | [verified-undocumented] Studio-AI output, 2026-08-31 |
| `useImageSetting` | `{ src, alt }` | [official] |
| `useVideoSetting` | `{ src }` | [official] |
| `useVibeCodingBlockIconSetting` | `{ icon }` (Lucide name) | [official] |
| `useNavigationSetting` | navigation object (see below) | [official] |
| `useBooleanSetting` | `boolean` | [official] |
| `useArraySetting` | array of schema-shaped items | [official] — plus one [verified-undocumented] schema type |

All hooks share the base options `{ name, label, initialValue }`; `useTextSetting` also takes `required` (optional, default false). `name` must be unique per block (Hard Constraint 5) and is the persistence key (see [the rename gotcha](#naming-conventions-and-the-rename-resets-value-gotcha)).

## Text hooks: useTextSetting and useLongTextSetting

```tsx
import { useTextSetting, useLongTextSetting } from "@/lib/editable-settings";

const title = useTextSetting({
  name: "title",
  label: "Title",
  initialValue: "Welcome",
  required: false,          // optional, default false
});
// Returns: string — single-line input in the Settings pane

const description = useLongTextSetting({
  name: "description",
  label: "Description",
  initialValue: "Formulation, manufacturing and packaging under one roof.",
});
// Returns: string — multi-line textarea with an expand control in the Settings pane
```

**Rule of thumb:** `useTextSetting` for single-line strings (labels, headings, CTA text, URLs); `useLongTextSetting` for paragraph-length copy (descriptions, testimonial bodies, bios).

**[verified-undocumented]** `useLongTextSetting` is absent from the official developer guide (checked 2026-08-31) but is emitted by Softr's own Studio AI and renders a working multi-line textarea in the Settings pane (screenshot-verified on a live Studio block). Same options shape as `useTextSetting`; return type `string` is inferred from usage, not a published signature.

**Newline gotcha — the one thing that makes it different in practice.** The pane's textarea lets builders enter line breaks, but HTML collapses `\n` to spaces. Render the value with `whitespace-pre-line` (or split on `\n` yourself) or the builder's paragraph breaks silently vanish:

```tsx
<p className="whitespace-pre-line text-muted-foreground">{description}</p>
```

Studio AI itself gets this wrong (renders the value in a plain `<p>`), so fix it when adopting Studio-generated code.

## Media hooks: useImageSetting and useVideoSetting

```tsx
import { useImageSetting, useVideoSetting } from "@/lib/editable-settings";

const image = useImageSetting({
  name: "hero-image",
  label: "Hero image",
  initialValue: { src: "https://...", alt: "A hero image" },
});
// Returns: { src: string, alt: string }

const video = useVideoSetting({
  name: "intro-video",
  label: "Intro video",
  initialValue: { src: "https://example.com/video.mp4" },
});
// Returns: { src: string }
```

**Empty-src gating.** Blocks routinely ship with `initialValue: { src: "" }` so the builder uploads the real asset in the pane — the official docs' own array example seeds `image: { src: "", alt: "" }`, so the empty state is platform-normal. Never render an unconditional `<img src={image.src}>` against a possibly-empty setting: an empty-string `src` triggers React's re-download warning and shows a broken/empty band at whatever fixed height you gave it. Gate it, or render a same-size placeholder so the layout holds pre-upload:

```tsx
{image.src ? (
  <img src={image.src} alt={image.alt} className="w-full h-[340px] object-cover" />
) : (
  <div className="w-full h-[340px] bg-muted" aria-hidden="true" />
)}
```

**One setting, several renders.** A settings hook returns a plain value, so one `useImageSetting` may safely feed two sibling `<img>` elements with opposite visibility classes (desktop art-directed crop + mobile full-bleed). The builder still edits ONE image in the pane. See ui-ux-guidelines.md §21 (art-directed responsive images).

## useVibeCodingBlockIconSetting

```tsx
import { useVibeCodingBlockIconSetting } from "@/lib/editable-settings";
import { DynamicIcon } from "@/components/dynamic-icon";

const { icon } = useVibeCodingBlockIconSetting({
  name: "feature-icon",
  label: "Feature icon",
  initialValue: { icon: "trending-up" },   // kebab-case lucide-react name
});

<DynamicIcon name={icon} className="w-6 h-6" />
```

Returns `{ icon: string }`. Always render through `<DynamicIcon>` — never a manual lookup table.

## useNavigationSetting

```tsx
import { useNavigationSetting } from "@/lib/editable-settings";
import { NavigationAction } from "@/components/navigation-action";
import { Button } from "@/components/ui/button";

const cta = useNavigationSetting({
  name: "primary-cta-link",
  label: "Primary CTA link",
  initialValue: { action: "OPEN_PAGE", destination: "/pricing", openIn: "SELF" },
});

<Button asChild>
  <NavigationAction navigation={cta}>Request your quote</NavigationAction>
</Button>
```

Value shapes per action type (full detail in SKILL.md's NavigationAction section; the official docs type `openIn` as `"SELF" | "TAB"` only — `"MODAL"` is validator-verified as a legal value per the error message quoted in [Constraints recap](#constraints-recap), and its restriction to `OPEN_PAGE` is inference from Studio behavior, not documented):

- `OPEN_PAGE` — `destination` (page path) + `openIn` (`"SELF"` | `"TAB"` | `"MODAL"`)
- `OPEN_URL` — `destination` (URL) + `openIn` (`"SELF"` | `"TAB"`)
- `OPEN_CHAT` — no destination (mind the data-source-context gotcha in [anti-patterns.md](anti-patterns.md))
- `TRIGGER_CUSTOM_WORKFLOW` — no destination; builder picks the workflow in Studio

**[verified-undocumented] `action` is accepted as optional.** Softr's setting validator accepts an initialValue with no `action` key — `{ destination: "/", openIn: "SELF" }` alone — and Studio's own AI emits exactly that shape (verified 2026-08-31: a Studio-generated block with three action-less `useNavigationSetting` initialValues, plus three more action-less link values inside an array setting, saved and rendered its Settings pane). Corroborating in-repo evidence that not every key is mandatory: the validator's own error message for `openIn` ends in *"if provided"* (see [anti-patterns.md](anti-patterns.md#editable-settings)). Two consequences:

1. **When generating, keep emitting an explicit `action`** — deterministic, self-documenting, and click-time resolution of action-less values is unverified (presumably defaults to `OPEN_PAGE` for in-app paths, but that's inference).
2. **When reviewing Studio-generated or existing blocks, do NOT flag a missing `action` as a defect.** It saves and renders fine.

## useBooleanSetting

```tsx
import { useBooleanSetting } from "@/lib/editable-settings";

const showHeader = useBooleanSetting({
  name: "toggle-header",
  label: "Toggle header",
  initialValue: false,      // official docs note the default is true when omitted
});
// Returns: boolean
```

Use for show/hide sections, layout variants, feature toggles.

## useArraySetting

```tsx
import { useArraySetting } from "@/lib/editable-settings";

const navItems = useArraySetting({
  name: "nav-items",
  label: "Navigation items",
  schema: {
    label: { type: "text", label: "Label", initialValue: "Item" },
    link: { type: "navigation", label: "Link", initialValue: { action: "OPEN_PAGE", destination: "/", openIn: "SELF" } },
  },
  initialValue: [
    { label: "Capabilities", link: { action: "OPEN_PAGE", destination: "/#capabilities", openIn: "SELF" } },
    { label: "Process", link: { action: "OPEN_PAGE", destination: "/#process", openIn: "SELF" } },
  ],
});
```

Returns an array of schema-shaped items, rendered in the Settings pane as **reorderable rows** with per-field editors and an "Add item" control. Use for nav menus, feature lists, testimonials, badges, footer link columns, FAQs.

### Schema field types

`"text"`, `"image"`, `"video"`, `"vibeCodingBlockIcon"` **[official]** — plus:

**[verified-undocumented] `"navigation"`.** A `{ type: "navigation" }` schema entry renders a per-item link picker (page picker / URL / openIn) inside each row, and item values carry the `useNavigationSetting` value shape — pass them straight to `<NavigationAction navigation={item.link}>`. Verified 2026-08-31 via a Studio-AI-generated block whose Settings pane showed nav items as reorderable rows with rendered per-item link pickers. This unlocks fully builder-editable nav menus, footer link lists, and CTA collections; without it you'd be stuck hardcoding links or spawning N separate `useNavigationSetting` hooks. (Click-through of array-item links follows from the value shape being identical to top-level navigation settings consumed by the same component, but wasn't independently click-tested.)

### Initial values: two layers

- **Top-level `initialValue` array** seeds the rows the block starts with.
- **Per-field `initialValue` inside the schema** is the default a field gets when the builder clicks **Add item**. It's optional [official — the docs' own example omits it on some fields], BUT:

**Give `navigation`-typed schema entries a per-field `initialValue` (or guard the render).** A schema entry like `link: { type: "navigation", label: "Link" }` with no initialValue means every builder-added row starts with `link: undefined`, which flows straight into `<NavigationAction navigation={undefined}>` — behavior unverified (dead element at best). Either seed it in the schema (as in the example above) or guard: `{item.link && <NavigationAction navigation={item.link}>...</NavigationAction>}`.

### Key array rows by index

```tsx
{navItems.map((item, index) => (
  <NavigationAction key={index} navigation={item.link}>{item.label}</NavigationAction>
))}
```

Never key by an editable field (`key={item.label}`). Builder-added rows all start at the schema default (`"Item"`, `"Certification"`, ...), so value keys duplicate **immediately** — broken reorder/update rendering in the pane's live preview is the default path, not an edge case. The official docs' own example keys by index; index keys are safe here because setting rows are stateless display rows fully re-rendered on every settings change. Studio's own AI gets this wrong (emits `key={item.label}`) — don't copy that part of Studio output.

## Granularity doctrine: settings-first static blocks

**For static/marketing blocks (heroes, page headers, pricing tables, testimonial bands, footers, FAQ sections): every user-visible string, image, and link is a setting by default. Hardcoded copy is the exception and needs a reason.** This is Softr's own generator's revealed philosophy — a Studio-emitted hero ships with 15 settings hooks and zero hardcoded user-visible copy — and it matches the official guidance ("Always use them for any text, images, icons, or lists that might change between block instances"). The payoff is the platform pitch itself: clients edit copy in **Content → Settings** without re-prompting, and one block template re-skins across client apps.

The recurring patterns:

- **Heading-line split** — one `useTextSetting` per visual line, joined with `<br />`, names suffixed `-line-1` / `-line-2` / `-line-3`. Gives builders line-break control without markup in a text field:

  ```tsx
  <h1>
    {headingLine1}<br />{headingLine2}<br />{headingLine3}
  </h1>
  ```

- **CTA pairing** — every call-to-action is TWO settings: `<x>-text` (`useTextSetting`) + `<x>-link` (`useNavigationSetting`). E.g. `primary-cta-text` / `primary-cta-link`, `login-button-text` / `login-button-link`.
- **Repeated groups** — any repeated UI group (nav items, badges, certifications, logos) is a `useArraySetting`, not N individual hooks.

For data-connected blocks the doctrine relaxes: record data comes from the datasource, and settings cover the frame around it (section headings, empty-state copy, CTA labels/links, toggles).

## Naming conventions and the rename-resets-value gotcha

**Convention:** kebab-case names describing the content's role — `logo-text`, `tagline`, `heading-line-1`, `primary-cta-text`, `nav-items`. Matches Studio AI's own output. (These conventions are for **setting names** only — the window-global and CustomEvent naming schemes in [helper-blocks.md](helper-blocks.md) are a different namespace; don't conflate them.)

**Gotcha [official]:** the docs annotate `name` with *"unique identifier — changing this resets the value."* `name` is the persistence key: rename a setting in a later code edit and the builder's saved value silently resets to `initialValue`. **Treat setting names as stable API once a block is deployed** — a rename is silent builder-data loss, not a refactor.

## Constraints recap

The platform-enforced rules (Hard Constraints 5–7 in SKILL.md):

- **Unique names** — no two setting hooks may share a `name`.
- **No nested arrays in schemas** — for list-like text inside an array item, use a `"text"` field with a separator and split in code.
- **`vibeCodingBlockIcon` never first** — don't put an icon field as the first field in an array schema.
- **`openIn`** must be exactly `"SELF"`, `"TAB"`, or `"MODAL"` (validator-enforced — see [anti-patterns.md](anti-patterns.md#editable-settings)).

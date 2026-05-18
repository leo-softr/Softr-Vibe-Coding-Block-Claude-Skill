---
name: softr-vibe-coding
description: >
  Generate custom Softr Vibe Coding blocks as complete JSX components. Use this skill whenever the user
  mentions Softr, Vibe Coding, Softr blocks, or wants to build a custom UI component for a Softr app.
  Also trigger when the user asks to create cards, lists, forms, dashboards, charts, detail pages,
  or any interactive block intended for Softr — even if they don't say "Vibe Coding" explicitly.
  If the user mentions Softr in the context of building a custom UI component, creating a JSX block,
  or vibe coding, use this skill.
when_to_use: >
  Triggers on "build me a Softr block", "create a card component", "make a dashboard",
  "vibe code this", "custom block for Softr", "JSX component for Softr app",
  "create a form block", "build a list view", "make a portal page",
  "Softr custom component", "vibe coding block".
effort: max
allowed-tools: Read Write Glob Grep Bash
---

# Softr Vibe Coding Block Generator

You generate complete, production-ready Softr Vibe Coding blocks as JSX files. A Vibe Coding block is a JavaScript file with a default-exported React component that runs exclusively in the browser inside a Softr app.

## Your Workflow

1. **Detect the brand source (always run first, before any block work).** Check if a `./DESIGN.md` file exists in the project folder you're about to work in.

   - **If `./DESIGN.md` is found:** Read its frontmatter and confirm with the user:

     > "I found a DESIGN.md in this project (brand: `<name>`, source: `<source>`, extracted: `<date>`). Use its brand tokens for this block?
     > 1. Yes — use this DESIGN.md
     > 2. No — use the default Softr style instead
     > 3. No — I'll paste a different brand override"

     If (1), load every relevant section: `colors`, `typography`, `rounded`, `elevation`, `components`, and especially the `Application Patterns` scaffold. Apply those tokens throughout the block. Honour the `tech_stack` block — it may pin specific shadcn variants or note bundler quirks.

     If (2), proceed with the default Softr style (see Step 3).

     If (3), accept the override and apply it.

   - **If `./DESIGN.md` is NOT found:** Tell the user:

     > "No DESIGN.md found in this project. Three options:
     > A. **Set up a brand foundation first** — run `building-design-md` to extract brand tokens from the client's website or a brand guide, then come back here. (Recommended for client work.)
     > B. **Quick brand override** — paste the brand's primary color, accent color, and font name now. I'll apply just those.
     > C. **Use the default Softr style** — primary `#386AF5`, accent `#FCB500`, Inter font."

     Wait for their pick. If (A), end the skill — the user will run `building-design-md` and then re-invoke this skill. If (B) or (C), record their choice for Step 3 and continue.

   Do not silently default to Softr's brand. The user must opt in to defaults explicitly.

2. **Understand what the user wants to build.** They will describe it in plain language. Only ask about things you genuinely cannot infer: **data source type** and **field IDs**. For everything else, make sensible defaults and flag your assumptions.

3. **Apply defaults for the rest, don't ask.** Infer these from context instead of asking:
   - **Project folder**: Derive from the block description (e.g., "partner-portal", "client-dashboard"). If the user has already specified a folder in this session, reuse it.
   - **Brand colors**: Use whatever was chosen in Step 1 — DESIGN.md tokens, the user's override, or the default Softr palette (primary `#386AF5`, accent `#FCB500`). Never silently fall back to defaults.
   - **Filename**: Derive from the block purpose (e.g., `partner-invite.jsx`, `team-directory.jsx`). The user can rename later.

4. **Load the relevant data source guide** from [datasources/](datasources/) before writing code. Read the specific guide for the user's data source type.

5. **Write the complete `.jsx` file** to the project sub-folder and tell the user the full path. Create the sub-folder if it doesn't exist yet. The file must be fully self-contained, **visually polished from the first version**, and ready to paste into Softr's Vibe Coding editor. Styling is not an afterthought -- it ships in v1. **Never deliver code inline in chat.** Copy-pasting JSX from chat corrupts characters (`>`, `>=`, `=>`, quotes), causing compilation errors that are hard to debug. Always write to a file.

6. **Self-validate before delivering.** Before presenting the code as complete, verify:
   - No optional chaining (`?.`) or nullish coalescing (`??`)
   - All imports use named imports (no `import React from 'react'`)
   - `export default function Block()` is present
   - Container + content wrappers present (`<div className="container py-0"><div className="content">`)
   - `// BLOCK PLACEMENT:` comment present at top of file with wrapper classes matching the placement (see "Block Placement & Page Spacing")
   - Loading, error, and empty states all handled
   - Mutation calls gated behind `enabled` check (if using mutations)
   - Field access uses `record.fields.alias` (not `record.alias`)
   - Every field rendered in JSX wrapped in `getFieldValue()` -- prevents React error #31
   - All hooks declared before any conditional `return` -- prevents React error #310
   - Sub-components (FieldLabel, TextInput, ChipButton, SectionCard, etc.) defined at **module scope**, NOT inside `Block()` -- prevents inputs losing focus after one keystroke (each render creates a new component identity, React unmounts/remounts the `<input>`)
   - When a custom DESIGN.md is in use, brand `fontFamily` (and any non-inherited brand defaults) set as an **inline style on the block's outermost wrapper** `<div>`, not relied on from `custom-code-header.html` -- Vibe Coding blocks render inside a shadow DOM and `html, body` rules don't cross that boundary. Per-element overrides (e.g. Fraunces serif on h1) still set inline at the element.
   - `fetchNextPage` only inside `useEffect`, never in render body
   - Mutations use `recordId` (not `id`) and call `refetch()` in `onSuccess`
   - `useRecordUpdate` calls use `.mutate(payload, { onSuccess, onError })` — **NOT** `.mutateAsync(...).then(...).catch(...)`. Softr's Action parser only recognizes the `.mutate(` token; `.mutateAsync(` is invisible to it and the Action never gets derived (`enabled` stays `false`, Actions tab shows "No actions used in this block yet")
   - `useRecordUpdate` payload is `{ recordId, fields: { ... } }` — nested, not flat. Field references inside flat payloads are invisible to the parser, same silent-failure mode as the `.mutateAsync` issue
   - No hardcoded domains in links -- use relative paths (`/page?recordId=...`)

## What to Clarify

When the user describes their block, figure out which of these areas apply and ask about anything you're missing:

- **Data source type**: Is it Airtable, Softr Database, REST API, or another source? This determines the data fetching approach. **Load the relevant data source guide** from the [datasources/](datasources/) directory before writing code.
- **Data source fields**: For Airtable/Softr Database, you need actual field IDs. For REST APIs, you access the raw API response directly. If the user doesn't know field IDs:
  - For **Softr Database**, ask the user to paste the `tablespace-with-tables` network response (DevTools -> Network -> filter that string while on Studio's Data tab). The JSON contains every field ID, type, and dropdown option UUID -- the most reliable way to receive accurate schema without transcription errors. See [datasources/fields.md](datasources/fields.md#field-inspector-block).
  - For **Airtable** and other sources where empty `q.select({})` works, suggest the Field Inspector block.
- **Brand colors**: Already resolved in Step 1 (Detect the brand source). Don't re-ask. The brand source is one of:
  - **Project's `./DESIGN.md`** (recommended for client work — produced by the `building-design-md` skill)
  - **User's quick override** (paste of primary + accent + font)
  - **Default Softr palette** (only when the user explicitly opted in — never as a silent fallback):

    | Color | Hex | Name | Use |
    |---|---|---|---|
    | Primary | `#386AF5` | Mariner (blue) | CTAs, links, active states |
    | Accent | `#FCB500` | Yellow Sea | Highlights, badges, sparkle accents |
    | Destructive | `#F53878` | Cabaret (pink) | Errors, destructive actions, required markers |
    | Text | `#030712` | Revolver (near-black) | Body text, headings |
    | Background | `#FFFFFF` | White | Page and card backgrounds |

  Softr logo assets (for blocks that need Softr branding):
  - Icon + wordmark (SVG): `https://cdn.brandfetch.io/idytCFzVcY/theme/dark/logo.svg`
  - Icon only (PNG): `https://cdn.brandfetch.io/idytCFzVcY/w/1024/h/1024/theme/dark/icon.png`
- **Layout and style**: Cards vs. table vs. list? How many columns? Apply the Premium Visual Baseline regardless.
- **Interactivity**: Create/edit/delete? Filtering? Sorting? Pagination?
- **User context**: Does it need to know who's logged in?
- **Settings**: Should anything be editable by the Softr builder (titles, images, toggle sections)?

Don't over-ask. If the user gives a clear description, fill in sensible defaults and note your assumptions.

## Examples (Decision Traces)

**User:** "Build a team directory with cards showing name, role, and photo from Airtable"
**Claude:** Reads `datasources/airtable.md` -> uses `q.select()` with Airtable column names (e.g., `"Full Name"`, `"Role"`, `"Headshot"`) -> card grid layout with `repeat(auto-fit, minmax(280px, 1fr))` -> avatar with brand-color fallback initials -> loading skeleton matching card shape -> empty state with "No team members yet"

**User:** "I need a form that pulls events from the Luma API and sends a webhook"
**Claude:** Reads `datasources/rest-api.md` -> uses `useProxyFetch` + `useQuery` (NOT `useRecords`) -> accesses raw API response directly (`event.name`, not `record.fields.name`) -> Select dropdown with event name + formatted date -> webhook via regular `fetch()` (not proxied) -> loading/error/empty states

## Data Sources

Softr supports 14 data sources. **Before writing any data-fetching code, read the relevant guide:**

| Data Source | Guide | Approach |
|---|---|---|
| Softr Databases | [datasources/softr-database.md](datasources/softr-database.md) | `useRecords` + `q.select()` |
| Airtable | [datasources/airtable.md](datasources/airtable.md) | `useRecords` + `q.select()` |
| Google Sheets | [datasources/google-sheets.md](datasources/google-sheets.md) | `useRecords` + `q.select()` |
| HubSpot | [datasources/hubspot.md](datasources/hubspot.md) | `useRecords` + `q.select()` |
| Notion | [datasources/notion.md](datasources/notion.md) | `useRecords` + `q.select()` |
| Coda | [datasources/coda.md](datasources/coda.md) | `useRecords` + `q.select()` |
| monday.com | [datasources/monday.md](datasources/monday.md) | `useRecords` + `q.select()` |
| SmartSuite | [datasources/smartsuite.md](datasources/smartsuite.md) | `useRecords` + `q.select()` |
| ClickUp | [datasources/clickup.md](datasources/clickup.md) | `useRecords` + `q.select()` |
| Xano | [datasources/xano.md](datasources/xano.md) | `useRecords` + `q.select()` |
| Supabase | [datasources/supabase.md](datasources/supabase.md) | `useRecords` + `q.select()` |
| BigQuery | [datasources/bigquery.md](datasources/bigquery.md) | `useRecords` + `q.select()` |
| SQL Database | [datasources/sql-database.md](datasources/sql-database.md) | `useRecords` + `q.select()` |
| REST API | [datasources/rest-api.md](datasources/rest-api.md) | `useProxyFetch` + `useQuery` |

For shared data fetching patterns (useRecords, mutations, uploads, metrics, charts), see [datasources/shared-patterns.md](datasources/shared-patterns.md).

For data source comparison and selection guidance, see [datasources/overview.md](datasources/overview.md).

## Reference Guides

For advanced patterns beyond data fetching, load the relevant reference when the task needs it:

| If the task involves... | Load reference |
|---|---|
| Cross-block communication, multi-table data access, invisible helper blocks, window globals, breadcrumbs | [references/helper-blocks.md](references/helper-blocks.md) |
| Embedding third-party libraries with their own CSS (Leaflet, Mapbox, TinyMCE, Quill, FullCalendar) | [references/advanced-integrations.md](references/advanced-integrations.md) |
| Debugging a broken block, checking patterns before delivery, full violation catalog | [references/anti-patterns.md](references/anti-patterns.md) |
| Quick syntax check — import paths, hook signatures, mutation call shapes, field mapping | [references/quick-reference.md](references/quick-reference.md) |
| Small reusable patterns — `localStorage` cross-page state, clipboard copy button | [references/common-patterns.md](references/common-patterns.md) |

## Code Structure

Every block follows this shape:

```jsx
// imports at the top
import { ... } from "@/lib/datasource";
// ...other imports

export default function Block() {
  // hooks, state, logic
  return (
    <div className="container py-0">
      <div className="content">
        <div className="py-3 px-8">
          {/* block content — wrapper padding depends on placement; see "Block Placement & Page Spacing" */}
        </div>
      </div>
    </div>
  );
}
```

Always wrap the outermost layout in `container` and `content` divs — these constrain width to match the Softr app's max width settings.

**Exception:** Blocks inside Softr column containers — omit wrappers so Softr controls layout.

## Block Placement & Page Spacing

Blocks rarely live alone — most Softr pages stack 2–4 blocks vertically, often between a header and a footer. Spacing must be set per-block based on **where the block sits on the page**, so adjacent blocks don't double up padding or leave inconsistent gaps.

**General rule:** the inner wrapper (the `<div>` directly inside `<div className="content">`) owns all vertical spacing. The outer `container` is always `py-0`. Top and bottom padding on the wrapper change based on what's above and below the block (another block, a header, a footer, or nothing).

**When generating a new block, if the placement is not clear from the user's description, ASK before writing code:**
- Where will this block sit on the page? (top / middle / bottom / standalone)
- Is there a Softr header immediately above this block?
- Is there a Softr footer immediately below this block?
- Is there a Back button at the top of this block?

**Detail pages — always ask about the back button AND its fallback URL.** A "detail page" is any block that reads a single record by URL recordId (i.e. it calls `useCurrentRecordId()` / `useRecord()`, or the user describes it as the target of a `/page?recordId=...` link). Users almost always want a back button there but rarely think to mention it, and shipping the page without one is the most common UX gap on these screens. So even if every other placement detail is clear, ask both:

1. **"Should the detail page have a back button?"** — if yes, always wire one. Use the back-navigation pattern in [references/helper-blocks.md](references/helper-blocks.md#breadcrumb--back-navigation): `window.history.back()` for users with history, plus a fallback URL for users who arrived via shared link.
2. **"What page should the back button fall back to when there's no history?"** — this is a separate question, easy to skip but important. Don't default silently; ask. If the user doesn't have a listing page yet, default to `/` and leave a `// TODO: update fallback when /jobs (or similar) exists` comment so it can be updated later.

**Persist the answer as a grep-able comment at the top of the generated file** so future edits know the spacing assumptions and can be updated consistently:

```jsx
// BLOCK PLACEMENT: <position on page>, <header/footer adjacency>, <back button y/n>
// Spacing: <wrapper classes; back-button container if present>
```

Example:

```jsx
// BLOCK PLACEMENT: first block on page, header-adjacent, has Back button
// Spacing: wrapper py-3 px-8; back-button container mt-6 mb-4
```

The `// BLOCK PLACEMENT:` marker is intentionally stable so it can be grepped and updated when the block's surroundings change.

### Spacing values (defaults)

**Container** (always): `<div className="container py-0">`

**Inner wrapper** classes by block position:

| Position on page | Wrapper classes | Rationale |
|---|---|---|
| First block (header-adjacent) | `py-3 px-8` | 12px top + 12px bottom; lets the Softr header own its own spacing |
| Middle block | `py-3 px-8` | 12px + Softr separator + 12px ≈ 24px between blocks |
| Last block (footer-adjacent) | `pt-3 pb-12 px-8` | 12px top + 48px bottom for footer breathing room |
| Standalone (only block on page) | `pt-3 pb-12 px-8` | Treat like a last block |

**Back button** (when present at the top of a block — typically on detail pages): wrap in `<div className="mt-6 mb-4">`. The `mt-6` (24px) adds breathing room above the button independent of wrapper padding; `mb-4` (16px) sits between the button and the first card. Apply this regardless of whether the block is first or mid-page.

**Within-block stacked cards**: each card uses `mb-6` (24px). **Do NOT add `mb-6` to the last card** in a block — the wrapper's bottom padding already handles that buffer. Doubling them produces 32–40px gaps that look bigger than the within-block rhythm.

**Net page rhythm**: between-block gaps (12 + 12 = 24px) match within-block card gaps (`mb-6` = 24px), so the page reads as one consistent vertical rhythm.

## Premium Visual Baseline

**Every block must look polished in its first version.** Styling is not a follow-up task — it is a core requirement of every code generation. Apply ALL of the following by default unless the user explicitly requests a minimal/plain style.

Refer to [ui-ux-guidelines.md](ui-ux-guidelines.md) for full design principles.

### 1. Gradient background wrapper
```jsx
<div className="rounded-2xl p-8" style={{ background: "linear-gradient(180deg, #EEF2FF 0%, #FFFFFF 100%)" }}>
  {/* header + content cards go inside here */}
</div>
```
Adjust the top gradient color to complement the user's brand.

### 2. Header section
- Icon in a colored rounded square (`h-10 w-10 rounded-xl` with brand primary, white icon)
- Title at `text-2xl font-bold`
- Optional subtitle in `text-muted-foreground`
- Primary CTA button with `shadow-md hover:shadow-lg transition-shadow`

### 3. Card-based content
- `bg-white rounded-xl shadow-sm border border-gray-100`
- Items with `hover:shadow-md hover:border-gray-200 transition-all duration-200`
- Use `space-y-3` or `gap-3`, never flat separators

### 4. Avatar and identity elements
- Brand primary color as avatar fallback with white initials
- `h-12 w-12` for list items, `h-28 w-28` for profiles
- `border-2 border-white shadow-lg` on profile avatars

### 5. Interactive feedback
- Buttons: `shadow-md hover:shadow-lg transition-shadow`
- Cards: `hover:shadow-md hover:border-gray-200 transition-all duration-200`
- Active states: blue left border accent (`border-l-4`)

### 6. Status and metadata
- Counts in pill badges: `text-xs font-medium px-2 py-0.5 rounded-full`
- Dates with icons (Calendar, Mail, Users)

### 7. Empty states
- Large icon in gradient square (`h-20 w-20 rounded-2xl`)
- Clear heading + explanation + CTA button

### 8. Loading states
- Skeleton shapes matching the final layout, `rounded-xl`

### 9. Error states
- Icon in tinted background, clear message, retry button

### 10. Modals and dialogs
- Icon in dialog title, required field markers, example placeholders

## Styling & Components

**Tailwind CSS** is pre-configured. **Semantic color tokens** preferred:
`bg-background`, `bg-card`, `bg-primary`, `bg-secondary`, `bg-muted`, `bg-accent`, `bg-destructive`, `border`, `border-input`

**Font classes:** `font-heading`, `font-sans`, `font-mono`

**Conditional classNames:** `import { cn } from "@/lib/utils";`

**DO NOT USE:** CSS modules, styled-components, or CSS file imports.

**shadcn/ui components** at `@/components/ui/[name]`:
accordion, alert, alert-dialog, aspect-ratio, avatar, badge, button, calendar, card, carousel, chart, checkbox, collapsible, command, context-menu, dialog, drawer, dropdown-menu, empty, hover-card, input, input-group, input-otp, item, kbd, label, menubar, native-select, navigation-menu, pagination, popover, progress, radio-group, resizable, scroll-area, select, separator, sheet, skeleton, slider, sonner, spinner, switch, table, tabs, textarea, toggle, toggle-group, tooltip

**Common import patterns:**

```jsx
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
```

**Lucide Icons:** `import { TrendingUp, User, Settings } from "lucide-react";`

**Dynamic icons by name string:** `<DynamicIcon>` from `@/components/dynamic-icon` renders a Lucide icon when you only know its name at runtime (e.g. from an editable setting, a window global, or a `useRecords` row). Pass the kebab-case Lucide name as `name`. Use this — not a manual lookup table — whenever the icon is data-driven.

```jsx
import { DynamicIcon } from "@/components/dynamic-icon";
<DynamicIcon name="trending-up" className="h-5 w-5" />
```

**Softr's `<NavigationAction>`** is a built-in component for triggering Softr-native navigation actions from inside a Vibe Coding block. Accepts a `recordId` prop for dynamic record-specific URLs and supports action types `OPEN_URL`, `OPEN_PAGE`, `OPEN_CHAT`, `TRIGGER_CUSTOM_WORKFLOW`. Prefer this over bare `<a href>` when you want Softr's user-group visibility checks and slide-out / modal navigation styles to apply. Bare `<a href>` is still fine for simple in-app links where you don't need that behavior.

The canonical pattern pairs a shadcn `<Button asChild>` with `<NavigationAction navigation={...}>` so the button's styling stays on-brand while the navigation behavior is handled by Softr's component:

```jsx
import { Button } from "@/components/ui/button";
import { NavigationAction } from "@/components/navigation-action";
import { useNavigationSetting } from "@/lib/editable-settings";
import { MessageSquare } from "lucide-react";

var askAi = useNavigationSetting({
  name: "ask-ai-action",
  label: "Ask AI Action",
  initialValue: { action: "OPEN_CHAT" },   // OPEN_CHAT needs no destination
});

<Button asChild size="lg" className="gap-2">
  <NavigationAction navigation={askAi}>
    <MessageSquare className="h-5 w-5" />
    Ask AI about this
  </NavigationAction>
</Button>
```

**Action types — what each one needs in `initialValue`:**

- `OPEN_CHAT` — opens Softr's AI chat. **No `destination` or `openIn` needed** — it's the cheapest "Ask AI" button to wire up. **GOTCHA:** Softr's AI pulls context from the block that triggered the chat, NOT from the page. If the block has no data source connected, `chat/prepare` returns HTTP 500 ("Failed to prepare AI assistant") even though the chat panel opens. Fix: in Softr Studio, connect the block to whatever data source the AI should read from — even if the block doesn't read or write any records itself, the connection is what gives the AI context. Verified by direct experiment, May 2026: a button-only helper block with no data source caused this exact failure; connecting it to the same table as the main block fixed it without any code change.
- `OPEN_URL` — opens an external URL. Needs `destination` (the URL) + `openIn` (`"SELF"` | `"TAB"`).
- `OPEN_PAGE` — navigates to a Softr page in-app. Needs `destination` (page path) + `openIn` (`"SELF"` | `"TAB"` | `"MODAL"`).
- `TRIGGER_CUSTOM_WORKFLOW` — runs a Softr workflow. Needs the workflow id in `destination`.

When the action navigates to a record-specific page, pass the runtime record id via the `recordId` prop on `<NavigationAction>` (not on the setting) so Softr can resolve dynamic URLs:

```jsx
<NavigationAction navigation={openWigDetails} recordId={wig.id}>
  View wig
</NavigationAction>
```

For on-brand custom styling (matching DESIGN.md inline-style conventions instead of shadcn Button), wrap the same pattern with a styled `<button>` — `<NavigationAction>` will render its children into the button's slot. The `asChild` attribute on Button is what enables this slot composition; without it shadcn renders its own native button and ignores `<NavigationAction>`.

**Any public npm package** auto-installs on import: `import { format } from "date-fns";`

### React Hooks — Critical Import Rule

```jsx
// CORRECT
import { useState, useEffect } from "react";

// WRONG — All of these fail:
const { useState } = React;
import React from 'react';
React.useState(null);
useState(null);  // without import = ReferenceError
```

## Editable Settings

Hooks from `@/lib/editable-settings` let Softr builders customize blocks. Each `name` must be unique.

```jsx
import { useTextSetting } from "@/lib/editable-settings";
var title = useTextSetting({ name: "title", label: "Title", initialValue: "Welcome", required: false });
// Returns: string

import { useImageSetting } from "@/lib/editable-settings";
var image = useImageSetting({ name: "hero", label: "Hero Image", initialValue: { src: "https://...", alt: "Hero" } });
// Returns: { src: string, alt: string }

import { useVideoSetting } from "@/lib/editable-settings";
var video = useVideoSetting({ name: "intro", label: "Intro Video", initialValue: { src: "https://..." } });
// Returns: { src: string }

import { useVibeCodingBlockIconSetting } from "@/lib/editable-settings";
import { DynamicIcon } from "@/components/dynamic-icon";
var iconSetting = useVibeCodingBlockIconSetting({ name: "icon", label: "Icon", initialValue: { icon: "trending-up" } });
// Render: <DynamicIcon name={iconSetting.icon} className="w-6 h-6" />

import { useNavigationSetting } from "@/lib/editable-settings";
var nav = useNavigationSetting({ name: "cta", label: "CTA", initialValue: { action: "OPEN_PAGE", destination: "/pricing", openIn: "SELF" } });
// Returns: { action, destination, openIn }
// `openIn` MUST be one of: "SELF" (same tab), "TAB" (new tab), or "MODAL". Any other value (e.g. "SAME_TAB", "NEW_TAB") fails Softr's setting validator with: "useNavigationSetting(): The 'initialValue.openIn' property in the 'navigation' setting must be \"SELF\", \"TAB\", or \"MODAL\" if provided".

import { useBooleanSetting } from "@/lib/editable-settings";
var show = useBooleanSetting({ name: "toggle", label: "Show header", initialValue: false });
// Returns: boolean

import { useArraySetting } from "@/lib/editable-settings";
var features = useArraySetting({
  name: "features", label: "Features",
  schema: {
    title: { type: "text", label: "Title", initialValue: "Feature" },
    description: { type: "text", label: "Description" },
    icon: { type: "vibeCodingBlockIcon", label: "Icon" },
  },
  initialValue: [{ title: "Fast", description: "Blazing fast.", icon: { icon: "zap" } }],
});
// Schema types: "text", "image", "video", "vibeCodingBlockIcon"
// No nested arrays. Don't put vibeCodingBlockIcon as first field.
```

## Hard Constraints

Non-negotiable rules enforced by the Softr platform:

1. **Browser-only** — No server-side code, no Node.js APIs.
2. **Static field mappings** — `q.select()` keys and values must be string literals.
3. **Filter nesting limit** — Maximum 2 levels deep with `q.and()` / `q.or()`.
4. **Check mutation `enabled`** — Gate mutation UI and calls behind the `enabled` boolean.
5. **Unique setting names** — No two setting hooks can share the same `name`.
6. **Array setting icon placement** — Never put `vibeCodingBlockIcon` as first field.
7. **No nested arrays in settings** — Use text with separator, split in code.
8. **Default export required** — `export default function Block()`.
9. **Container wrapping** — Always wrap in `<div className="container py-0"><div className="content">`. Vertical padding lives on the inner wrapper and depends on block placement (see "Block Placement & Page Spacing").
10. **No optional chaining or nullish coalescing** — Softr's bundler fails on `?.` and `??`. Use:
    - `(user && user.email) || ""` instead of `user?.email ?? ""`
    - `(data && data.pages) ? data.pages.flatMap(function(p) { return p.items; }) : []`
11. **Airtable: use column names, not fld... IDs** — See [datasources/airtable.md](datasources/airtable.md).
12. **Record fields nested under `fields`** — Access via `record.fields.alias`, not `record.alias`.
13. **ONE `useRecords` per block** — Filter client-side. Multiple `useMetric` calls OK.
14. **React functional components only** — No class components.
15. **Do NOT `import React from 'react'`** — Use named imports for hooks.
16. **No CSS modules or styled-components** — Tailwind only.
17. **setTimeout for scroll** -- Wrap programmatic scroll in `setTimeout(fn, 0)`.
18. **`fetchNextPage` inside `useEffect` only** -- Calling it during render causes infinite re-render loops. The component calls `fetchNextPage`, which updates data, which triggers re-render, which calls `fetchNextPage` again.
19. **All hooks before any conditional `return`** -- Hooks must be called in the same order every render. A hook declared after a conditional `return` causes React error #310.
20. **Relative paths in navigation** -- Use `/page-name?recordId=...`, never hardcoded domains like `app.client.com/page`.

## Style Conventions (preferred, not enforced)

The conventions below improve consistency across the skill's examples but are NOT enforced by the Softr bundler. Softr's AI assistant in Studio outputs `const` and arrow functions, and both compile and run fine. Adopting these conventions makes hand-written blocks visually uniform with the rest of the skill, but blocks generated by Softr's AI work without conversion.

- Prefer `var` over `const` / `let`
- Prefer `function() {}` over arrow functions in JSX callbacks and component props
- Field-value helper property priority: `label` -> `name` -> `title`

If you're editing a block originally generated by Softr's AI assistant, you can convert to skill style for consistency or leave the AI's syntax as-is. Both produce a working block. Only `?.` and `??` (Hard Constraint #10) are actual bundler blockers — verified by direct experiment, April 2026.

## Anti-Patterns Checklist

Before delivering any block, run through [references/anti-patterns.md](references/anti-patterns.md) — a categorized catalog of every violation observed in production (data access, mutations, hooks, layout, helper blocks).

## Code Quality Guidelines

- Use `sonner`'s `toast` for notifications. Also: `toast.info()`, `toast.message("Note", { description: "..." })`.
- Show loading states with `spinner` or `skeleton` when `status === "pending"`.
- Show error states gracefully when `status === "error"`.
- After mutations, call `refetch()` before success toast.
- Use Tailwind for all styling.
- Prefer shadcn/ui components over raw HTML.
- Use `date-fns` for date formatting.

## UI/UX Guidelines

For design best practices, spacing, responsive patterns, and component guidance, see [ui-ux-guidelines.md](ui-ux-guidelines.md).

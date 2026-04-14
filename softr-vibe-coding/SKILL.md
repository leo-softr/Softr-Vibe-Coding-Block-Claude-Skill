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
effort: high
allowed-tools: Read Write Glob Grep Bash
---

# Softr Vibe Coding Block Generator

You generate complete, production-ready Softr Vibe Coding blocks as JSX files. A Vibe Coding block is a JavaScript file with a default-exported React component that runs exclusively in the browser inside a Softr app.

## Your Workflow

1. **Understand what the user wants to build.** They will describe it in plain language. Only ask about things you genuinely cannot infer: **data source type** and **field IDs**. For everything else, make sensible defaults and flag your assumptions.

2. **Apply defaults, don't ask.** Infer these from context instead of asking:
   - **Project folder**: Derive from the block description (e.g., "partner-portal", "client-dashboard"). If the user has already specified a folder in this session, reuse it.
   - **Brand colors**: Apply the default premium theme — primary `#386AF5`, accent `#FCB500` — unless the user provides alternatives. Mention you're using defaults.
   - **Filename**: Derive from the block purpose (e.g., `partner-invite.jsx`, `team-directory.jsx`). The user can rename later.

3. **Load the relevant data source guide** from [datasources/](datasources/) before writing code. Read the specific guide for the user's data source type.

4. **Write the complete `.jsx` file** to the project sub-folder and tell the user the full path. Create the sub-folder if it doesn't exist yet. The file must be fully self-contained, **visually polished from the first version**, and ready to paste into Softr's Vibe Coding editor. Styling is not an afterthought — it ships in v1.

5. **Self-validate before delivering.** Before presenting the code as complete, verify:
   - No optional chaining (`?.`) or nullish coalescing (`??`)
   - No arrow functions in JSX callback props — use `function() {}`
   - All imports use named imports (no `import React from 'react'`)
   - `export default function Block()` is present
   - Container + content wrappers present (`<div className="container py-6"><div className="content">`)
   - Loading, error, and empty states all handled
   - Mutation calls gated behind `enabled` check (if using mutations)
   - Field access uses `record.fields.alias` (not `record.alias`)

## What to Clarify

When the user describes their block, figure out which of these areas apply and ask about anything you're missing:

- **Data source type**: Is it Airtable, Softr Database, REST API, or another source? This determines the data fetching approach. **Load the relevant data source guide** from the [datasources/](datasources/) directory before writing code.
- **Data source fields**: For Airtable/Softr Database, you need actual field IDs. For REST APIs, you access the raw API response directly. If the user doesn't know field IDs, suggest the Field Inspector block.
- **Brand colors**: Ask for hex values. If none provided, default to **Softr's brand palette**:

  | Color | Hex | Name | Use |
  |---|---|---|---|
  | Primary | `#386AF5` | Mariner (blue) | CTAs, links, active states |
  | Accent | `#FCB500` | Yellow Sea | Highlights, badges, sparkle accents |
  | Destructive | `#F53878` | Cabaret (pink) | Errors, destructive actions, required markers |
  | Text | `#030712` | Revolver (near-black) | Body text, headings |
  | Background | `#FFFFFF` | White | Page and card backgrounds |

  Softr logo assets (for blocks that need branding):
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

## Code Structure

Every block follows this shape:

```jsx
// imports at the top
import { ... } from "@/lib/datasource";
// ...other imports

export default function Block() {
  // hooks, state, logic
  return (
    <div className="container py-6">
      <div className="content">
        {/* block content */}
      </div>
    </div>
  );
}
```

Always wrap the outermost layout in `container` and `content` divs — these constrain width to match the Softr app's max width settings.

**Exception:** Blocks inside Softr column containers — omit wrappers so Softr controls layout.

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
var nav = useNavigationSetting({ name: "cta", label: "CTA", initialValue: { action: "OPEN_PAGE", destination: "/pricing", openIn: "TAB" } });
// Returns: { action, destination, openIn }

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
9. **Container wrapping** — Always wrap in `<div className="container py-6"><div className="content">`.
10. **No optional chaining or nullish coalescing** — Softr's bundler fails on `?.` and `??`. Use:
    - `(user && user.email) || ""` instead of `user?.email ?? ""`
    - `(data && data.pages) ? data.pages.flatMap(function(p) { return p.items; }) : []`
    - Prefer `function() {}` over arrow functions in JSX callbacks.
11. **Airtable: use column names, not fld... IDs** — See [datasources/airtable.md](datasources/airtable.md).
12. **Record fields nested under `fields`** — Access via `record.fields.alias`, not `record.alias`.
13. **ONE `useRecords` per block** — Filter client-side. Multiple `useMetric` calls OK.
14. **React functional components only** — No class components.
15. **Do NOT `import React from 'react'`** — Use named imports for hooks.
16. **No CSS modules or styled-components** — Tailwind only.
17. **setTimeout for scroll** — Wrap programmatic scroll in `setTimeout(fn, 0)`.

## Anti-Patterns Checklist

| Anti-Pattern | Correct Approach |
|---|---|
| `useRecords()` bare hook | `useRecords({ select, count: 25 })` |
| `records.map(...)` on raw hook | `data.pages.flatMap(function(p) { return p.items; })` |
| `record.fields["Field Name"]` | `record.fields.alias` via `q.select()` mapping |
| `import React from 'react'` | Named imports only |
| `.mutate({ id: ... })` | `.mutate({ recordId: ... })` — `id` causes 404 |
| `deleteRecord.mutate({ id: r.id })` | `deleteRecord.mutate(r.id)` — just the string |
| Not calling `refetch()` after mutations | Always `refetch()` in `onSuccess` |
| Including formulas in create/update | Only writable fields |
| Linked record as plain string | Must be `[{ id: "..." }]` array |
| `field.toLowerCase()` on selects | `getFieldValue(field).toLowerCase()` |
| Named export | `export default function Block()` |
| `item.fields.formula === true` | Formula booleans: `=== "1"` |
| `currentUser.role` for tiers | `window.__softr_current_user.userGroups` |
| `useLinkedRecords({ fieldId })` | `useLinkedRecords({ select, field: "alias" })` |
| `opt.label` on linked records | `opt.title` — shape is `{ id, title }` |
| `useRecords` with REST API source | Use `useProxyFetch` + `useQuery` |
| `q.select()` for REST API fields | Access raw API response directly |
| Hardcoding API keys for connected API | Use `useProxyFetch` — key stays server-side |

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

# Anti-Patterns Checklist

Run through this catalog before delivering any block. Every row is a violation observed in production that caused either runtime errors, silent data loss, or hours of debugging.

## Data Access

| Anti-Pattern | Correct Approach |
|---|---|
| `useRecords()` bare hook | `useRecords({ select, count: 25 })` |
| `records.map(...)` on raw hook | `data.pages.flatMap(function(p) { return p.items; })` |
| `record.fields["Field Name"]` | `record.fields.alias` via `q.select()` mapping |
| `useLinkedRecords({ fieldId })` | `useLinkedRecords({ select, field: "alias" })` |
| `opt.label` on linked records | `opt.title` -- shape is `{ id, title }` |
| `useRecords` with REST API source | Use `useProxyFetch` + `useQuery` |
| `q.select()` for REST API fields | Access raw API response directly |
| Hardcoding API keys for connected API | Use `useProxyFetch` -- key stays server-side |
| Using `q.select({})` to dump all fields on Softr Database | Returns record IDs with empty `fields: {}`. Look up field IDs in Studio's Data tab, or use the Softr DB REST API with `fieldNames=true` |

## Mutations

| Anti-Pattern | Correct Approach |
|---|---|
| `.mutate({ id: ... })` | `.mutate({ recordId: ... })` -- `id` causes 404 |
| `deleteRecord.mutate({ id: r.id })` | `deleteRecord.mutate(r.id)` -- just the string |
| `var { mutateAsync } = useRecordUpdate({...})` | `var updateRecord = useRecordUpdate({...})` -- keep full object for `.enabled`, `.status`, `.reset()` |
| Not calling `refetch()` after mutations | Always `refetch()` in `onSuccess` |
| Including formulas in create/update | Only writable fields |
| Linked record as plain string | Must be `[{ id: "..." }]` array |
| Writing dropdown values as `{ id, label }` objects (the read shape) | Write the option UUID as a plain string -- e.g. `status: "822b8d69-..."`, not `status: { id: "...", label: "..." }` |
| Treating Studio's Actions tab as a separately-managed configuration to keep in sync with code | Actions auto-derive from your `useRecordCreate`/`useRecordUpdate`/`useRecordDelete` + `q.select` on every save. The Actions tab is a read-only inspector; there is no manual delete control. To change an Action, change the code |

## Field Values

| Anti-Pattern | Correct Approach |
|---|---|
| `field.toLowerCase()` on selects | `getFieldValue(field).toLowerCase()` |
| `item.fields.formula === true` | Formula booleans: `=== "1"` |

## Hooks & React

| Anti-Pattern | Correct Approach |
|---|---|
| `import React from 'react'` | Named imports only |
| Named export | `export default function Block()` |
| Hook declared after conditional `return` | All hooks at top before any conditional `return` -- React error #310 |
| `fetchNextPage()` in render body | Inside `useEffect` only -- in render = infinite loop |
| `useRef` for IDs used in `useMemo` | `useState` -- ref mutations don't trigger recomputation |
| Defining a sub-component INSIDE the `Block()` function body | Define ALL sub-components at MODULE scope (above `export default function Block()`). Sub-components defined inside `Block()` get a brand-new function reference on every render, which makes React unmount/remount their entire DOM subtree every time `Block` re-renders. The user-visible symptom: **inputs lose focus after typing one character** (because each keystroke triggers a `setState` -> re-render -> the `<input>` is destroyed and recreated). Move `function FieldLabel`, `function TextInput`, `function ChipButton`, `function SectionCard`, etc. above `export default function Block()` so React sees stable component identity across renders. Closure-captured `Block`-internal state must be passed as props, not closed over. |

## Layout & Styling

| Anti-Pattern | Correct Approach |
|---|---|
| Hardcoded domain in navigation | Relative paths: `/task-details?recordId=...` |
| Emojis in UI | lucide-react icons only |
| `[&_svg]:opacity-0` on SelectTrigger | `<style>` + `data-fix-chevron` attribute (Softr bundler limitation) |
| Relying on `custom-code-header.html` (Softr → Settings → Custom Code → Code inside header) to apply brand fonts/colors INSIDE a Vibe Coding block | Vibe Coding blocks render inside a shadow DOM. CSS custom properties (`--brand-*`) pierce that boundary, but `html, body { font-family: ... !important }` rules **do not** — `<html>` and `<body>` don't exist inside the shadow root. Apply brand fonts/colors at the block's **own outermost wrapper** via inline style: `style={{ fontFamily: "'Manrope', system-ui, sans-serif", color: BRAND_INK }}` on the outer `<div>` so every descendant inherits brand defaults. Override per-element with explicit inline `fontFamily` (e.g., `"'Fraunces', Georgia, serif"` on h1/h2). Google `<link>` tags in the page head DO load `@font-face` globally — the fonts are available inside shadow DOM, they just need to be applied. |
| Painting `backgroundColor: BRAND_CANVAS` on a Vibe Coding block's outer wrapper when `custom-code-header.html` already sets `body { background-color: var(--brand-canvas) !important }` | Don't double-paint. If the body bg is already the brand canvas, the block leaves its own backgroundColor unset and the page bg shows through. Painting the same color twice produces a visible seam — Softr's content wrapper sits between `<body>` and the Vibe Coding block, and the two backgrounds composite slightly differently due to sub-pixel rendering, transparency stacking, or wrapper paddings. Set fontFamily and color on the block's wrapper (those don't inherit cleanly through shadow DOM), but **leave backgroundColor unset** — let the page bg flow through. The exception: if the block needs a brand-tinted *section* (e.g., a card-style admin shell that's different from the page bg), paint that bg explicitly on its specific container, not on the outer wrapper. |

## Permissions

| Anti-Pattern | Correct Approach |
|---|---|
| `currentUser.role` for tiers | `window.__softr_current_user.userGroups` |

## Editable Settings

| Anti-Pattern | Correct Approach |
|---|---|
| `useNavigationSetting` with `openIn: "SAME_TAB"` / `"NEW_TAB"` / any other string | `openIn` must be exactly `"SELF"`, `"TAB"`, or `"MODAL"` -- Softr's setting validator rejects unknown values at save time with: *"The 'initialValue.openIn' property in the 'navigation' setting must be \"SELF\", \"TAB\", or \"MODAL\" if provided"* |

## Helper Blocks

| Anti-Pattern | Correct Approach |
|---|---|
| Helper block returning `null` during dev | Return a minimal visible badge until feature stable |
| Single CustomEvent on full load | Dispatch `_progress` per page AND `_ready` on completion |
| Helper publishes only raw records | Also publish computed `filterOptions` as separate globals |
| Refactoring helper shape without updating consumers | Version namespace OR update all consumers in same commit |
| Helper B placed above A when B depends on A | A must be above B -- Softr renders top-to-bottom |
| Using `useLinkedRecords` for rich foreign data | It only returns `{id, title}` -- use a helper block instead |

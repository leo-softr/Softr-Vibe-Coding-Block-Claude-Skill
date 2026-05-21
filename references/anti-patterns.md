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
| `updateRecord.mutate({ recordId, status: "..." })` — flat payload | `updateRecord.mutate({ recordId, fields: { status: "..." } })` — fields **must** be nested. The flat form can run at runtime but Softr's Action parser doesn't see field references inside it, so the derived Update Action never gets created. The hook's `enabled` stays `false`, the Save button never lights up, the Actions tab in Studio shows "No actions used in this block yet" — all with no error, no warning. The symptom is a button that does nothing and a console log showing `enabled: false, error: null, status: "idle"`. Use the nested form for EVERY mutate call, even single-field updates. See [datasources/writing.md](../datasources/writing.md#critical-two-parser-requirements-for-userecordupdate) |
| `updateRecord.mutateAsync(payload).then(...).catch(...)` | `updateRecord.mutate(payload, { onSuccess, onError })` — Softr's Action parser scans for the **literal `.mutate(` token** to detect mutation call sites. `.mutateAsync()` runs fine at runtime (it's just a Promise wrapper) but the parser ignores it — no Action gets derived, `enabled` stays `false`, the Actions tab shows "No actions used in this block yet". This is the same silent-failure mode as the flat-payload anti-pattern, and the two often appear together because devs reach for `mutateAsync` to chain `.then()/.catch()`. The fix is to use `.mutate(payload, { onSuccess, onError })` — per-call handlers go in the second argument (react-query convention). Verified by direct experiment, May 2026. See [datasources/writing.md](../datasources/writing.md#critical-two-parser-requirements-for-userecordupdate) |
| Assuming `mutation.enabled === false` always means a code bug | `enabled` is BOTH a parser signal AND a permissions signal. Per the official Softr docs, "`enabled` reflects user permissions." When code looks correct and the Actions tab shows the action listed, the cause is almost always permissions. Test by switching "Preview as" in Studio to an Owner / admin; if it then works, the issue is permissions. Three places to check, in priority order: (1) the block's **Visibility** tab (right panel), (2) **Studio → Users → Data Restrictions → Global data restrictions** — an app-wide layer that easily gets overlooked because it's hidden under Users (not on the block); it overlays every block in the app, and a single restriction on the target table will silently disable every mutation against that table for the affected user group, (3) the data-source PAT scope — if granted read-only, every write fails regardless of UI permissions. See [datasources/writing.md](../datasources/writing.md#how-actions-work-studios-actions-tab) |
| `deleteRecord.mutate({ id: r.id })` | `deleteRecord.mutate(r.id)` -- just the string |
| `var { mutateAsync } = useRecordUpdate({...})` | `var updateRecord = useRecordUpdate({...})` -- keep full object for `.enabled`, `.status`, `.reset()` |
| Not calling `refetch()` after mutations | Always `refetch()` in `onSuccess` |
| Including formulas in create/update | Only writable fields |
| Linked record as plain string | Must be `[{ id: "..." }]` array |
| Writing dropdown values as `{ id, label }` objects (the read shape) | Write the option UUID as a plain string -- e.g. `status: "822b8d69-..."`, not `status: { id: "...", label: "..." }` |
| Treating Studio's Actions tab as a separately-managed configuration to keep in sync with code | Actions auto-derive from your `useRecordCreate`/`useRecordUpdate`/`useRecordDelete` + `q.select` on every save. The Actions tab is a read-only inspector; there is no manual delete control. To change an Action, change the code |
| One alias in a write-side `q.select` referencing a renamed / non-existent Airtable column | Softr's Action parser silently rejects the **entire** create/update Action — not just the bad alias. Symptoms: Studio's Actions tab shows "No actions used in this block yet", `createRecord.enabled` / `updateRecord.enabled` stays `false`, `.mutate()` calls dispatch but resolve immediately to "not yet ready". Every OTHER field in the same `q.select()` is also lost, even the ones that map cleanly. Diagnostic: bisect the `q.select` — strip down to a known-good minimal set, confirm the Action appears in Studio, then add fields back in halves until it drops out. The culprit is in the last half added. Once narrowed to a single field, grep its name against the freshest Airtable schema export to catch the rename / trailing-space / case-mismatch. Verified 2026-05-21: a `"Photos"` column on Wigs was renamed to `"Before Photos"`, the helper that wrote `photos: "Photos"` had its entire Action disabled even though 11 other fields in the same `q.select` were fine. See [datasources/airtable.md](../datasources/airtable.md#maintainability-gotcha) |

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
| Placing a `<NavigationAction navigation={{ action: "OPEN_CHAT" }}>` Ask-AI button on a block that has no data source connected | Connect the block to the data source the AI should read from in Studio's Source tab. Softr's AI pulls context from the **block that triggered the chat**, not from the page — a button-only helper block with no data source causes `chat/prepare` → HTTP 500 ("Failed to prepare AI assistant") even though the chat UI opens fine. The block doesn't need to read or write records itself; the connection is purely for AI context. Verified by direct experiment, May 2026 |
| Emojis in UI | lucide-react icons only |
| `[&_svg]:opacity-0` on SelectTrigger | `<style>` + `data-fix-chevron` attribute (Softr bundler limitation) |
| Relying on `custom-code-header.html` (Softr → Settings → Custom Code → Code inside header) to apply brand fonts/colors INSIDE a Vibe Coding block | Vibe Coding blocks render inside a shadow DOM. CSS custom properties (`--brand-*`) pierce that boundary, but `html, body { font-family: ... !important }` rules **do not** — `<html>` and `<body>` don't exist inside the shadow root. Apply brand fonts/colors at the block's **own outermost wrapper** via inline style: `style={{ fontFamily: "'Manrope', system-ui, sans-serif", color: BRAND_INK }}` on the outer `<div>` so every descendant inherits brand defaults. Override per-element with explicit inline `fontFamily` (e.g., `"'Fraunces', Georgia, serif"` on h1/h2). Google `<link>` tags in the page head DO load `@font-face` globally — the fonts are available inside shadow DOM, they just need to be applied. |
| Painting `backgroundColor: BRAND_CANVAS` on a Vibe Coding block's outer wrapper when `custom-code-header.html` already sets `body { background-color: var(--brand-canvas) !important }` | Don't double-paint. If the body bg is already the brand canvas, the block leaves its own backgroundColor unset and the page bg shows through. Painting the same color twice produces a visible seam — Softr's content wrapper sits between `<body>` and the Vibe Coding block, and the two backgrounds composite slightly differently due to sub-pixel rendering, transparency stacking, or wrapper paddings. Set fontFamily and color on the block's wrapper (those don't inherit cleanly through shadow DOM), but **leave backgroundColor unset** — let the page bg flow through. The exception: if the block needs a brand-tinted *section* (e.g., a card-style admin shell that's different from the page bg), paint that bg explicitly on its specific container, not on the outer wrapper. |
| `document.getElementById(...)` / `document.querySelector(...)` to find an element inside the block — for example, a hidden `<input type="file">` triggered by a visible "Upload" button via `getElementById('myInput').click()` | Vibe Coding blocks render inside a shadow DOM. The global `document` traversal stops at the shadow boundary, so id/selector lookups for elements inside the block return `null`. The user-visible symptom is a control that does nothing — no error, no file picker, no focus, no scroll — because the chained `.click()` / `.focus()` / `.scrollIntoView()` was called on `null`. Use a **React `useRef`** instead: `var inputRef = useRef(null)`, then `<input ref={inputRef} />` and `<button onClick={function() { if (inputRef.current) inputRef.current.click(); }}>`. Refs hold direct node references and don't depend on DOM traversal, so they work regardless of which DOM tree the node lives in. This applies to every "trigger a hidden element" pattern: hidden file inputs, programmatic focus, scroll-into-view, `.click()` on a non-visible button. |

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

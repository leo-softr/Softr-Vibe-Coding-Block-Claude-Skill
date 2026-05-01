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

## Layout & Styling

| Anti-Pattern | Correct Approach |
|---|---|
| Hardcoded domain in navigation | Relative paths: `/task-details?recordId=...` |
| Emojis in UI | lucide-react icons only |
| `[&_svg]:opacity-0` on SelectTrigger | `<style>` + `data-fix-chevron` attribute (Softr bundler limitation) |

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

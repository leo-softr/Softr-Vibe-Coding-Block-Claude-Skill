# Changelog

All notable changes to this skill are documented here. Versions follow [Semantic Versioning](https://semver.org/), and the format draws from [Keep a Changelog](https://keepachangelog.com/).

Entries from 1.3.1 onward are generated automatically from git commit subjects between version bumps (see `.github/workflows/publish.yml`). Entries before 1.3.1 were backfilled by hand from the existing commit history.

## [2.1.1] - 2026-08-26
- Release 2.1.1
- Document external-URL attachment ingestion (copy, not link)

## [2.1.0] - 2026-08-25
- Bump to 2.1.0 — official dev-guide sync (field-name rule for Airtable/Notion/Sheets, PHONE sanitization, useProxyFetch datasource routing, useCurrentUser properties) + workspace-wide Softr MCP reference with direct block deployment (softr-mcp.md replaces softr-database-mcp.md)
- Sync with the official Vibe Coding developer guide and the workspace-wide Softr MCP server (28 verified fixes). Field-name rule extended: Airtable AND Notion AND Google Sheets use field NAMES in q.select (Softr DB/Supabase use IDs; wrong form fails silently with empty data) — fixed in Hard Constraint 11, notion.md, helper-blocks.md publisher template (was modeling fldXXX IDs), fields.md. New PHONE write rule: + followed by digits only, Monday.com hard-rejects formatted values — official sanitizePhone added to writing.md (new Phone section), monday.md, anti-patterns.md. useProxyFetch is datasource-scoped: alias as its ARGUMENT (useProxyFetch(ds.store)), throws when omitted with >1 source; proxy payloads are text-only (no FormData/streams/uploads) — added to rest-api.md, multi-datasource.md, quick-reference.md, anti-patterns.md. fetchNextPage rule relaxed to match the guide's canonical Load More onClick: never in the render body, event handler or guarded useEffect both fine (SKILL.md x2, README, anti-patterns.md). useCurrentUser({ properties }) exposes custom user fields under user.properties — window.__softr_current_user narrowed to userGroups/role only; id only present with user sync (reading.md, quick-reference.md, fields.md). useLinkedRecords count default 100 max 1000. useUpload: isUploading + result.error handling + multi-file pattern. Linked-record field-type row corrected to string-array shape. TRIGGER_CUSTOM_WORKFLOW takes no destination per the documented type. references/softr-mcp.md REPLACES softr-database-mcp.md: the MCP is now workspace-wide — vibe coding block tools (get_vibe_coding_docs, create/edit/versions, data source wiring + the five official gotchas incl. action-permission reset on every code change), integrations browsing down to field level (Airtable/Sheets/Notion/Supabase/Softr DB only), databases tools (no deletes yet; 100-create/200-read/2-group-by limits), three-area bundled permission levels replacing the old granular scopes. SKILL.md workflow now offers direct MCP deployment alongside paste-into-Studio. Description gains negative scope (building-design-md, non-Softr dashboards); reading/writing/fields now linked directly from SKILL.md instead of only via the shared-patterns index; README tree gains the tools/ dir; retired "no ?." mention dropped from airtable-automations.md; common-patterns var-style sentence reworded to legacy-but-valid
- Bump to 2.0.0 — verified 2026-08 platform contract: modern TypeScript, mutateAsync write queues, label-string SELECT writes, flat create payloads, inline hook options, Actions reset on recompile

## [1.12.0] - 2026-07-22
- Bump to 1.12.0 — multi-datasource blocks, Airtable rating writability, dark-brand canvas + page-background anti-patterns
- Document the Airtable rating field as writable (plain integer 0-max; 0 clears it, so AVERAGE formulas skip it) — it was absent from the Supported Fields table, which made it the main unknown when building a star-rating form. Add two dark-brand styling anti-patterns: a block on a dark brand MUST paint its own backgroundColor because custom-code-header's body rule doesn't cross the shadow-DOM boundary and a default Softr page is white, so white text/logos/buttons render invisibly on white (the existing don't-double-paint row assumed a light app and inverts here); and setting html,body alone doesn't change the page background because Softr paints the same fill on FOUR stacked layers — html, body, #page-content, and a class-less wrapper div inside it — so paint html then clear the duplicates, excluding the .softr-topbar subtree
- Add datasources/multi-datasource.md — a block can now connect to SEVERAL data sources: datasource.define({alias: 'uuid'}) plus a from: parameter on every data hook (useRecords, useRecord, useLinkedRecords, useFieldOptions, useMetric, useChartData, useRecordCreate/Update/Delete; not useUpload/useCurrentRecordId, which are app-level). Omitting from: throws once >1 source is connected; with exactly one you can skip define entirely. The define() values must be INLINE STRING LITERALS — hoisting them into constants fails to compile with 'datasource.define() object values must be string literals', same static-analysis rule as q.select(). Ids are plain UUIDs, not the table id and not the ds_id_N placeholder shape in Softr's docs; obtain them by asking Studio's AI chat to WRITE CODE, never to recite a value — asked three times in prose for the same three connected tables it returned three different confidently-worded sets, once recycling another table's uuid. This supersedes the one-table-per-block limit: relax Hard Constraint #13 to one useRecords per DATASOURCE, reframe helper-blocks.md around genuinely cross-BLOCK jobs (triggering another block, sharing computed state) with the old rationale kept as history, and retarget the useLinkedRecords anti-pattern at a second datasource rather than a helper

## [1.11.2] - 2026-07-08
- Bump to 1.11.2 — publish recordId-less useRecord note and input.textAsync correction
- Correct input.textAsync in airtable-automations.md — it is not a real method in EITHER Airtable scripting environment; calling it in the Scripting Extension throws TypeError: input.textAsync is not a function. buttonsAsync is the only interactive runtime prompt; free-text values (e.g. an API key) go through an input.config({...}) setting at the top or a hardcoded constant. Also generalize the Automation Scripts bullet to "no interactive prompts".
- Document recordId-less useRecord via Studio data binding

## [1.11.1] - 2026-06-12
- Document the tabbed-list visibility gotcha in native-block-filters.md — Softr renders tabs with Radix and keeps the INACTIVE tab's blocks in the DOM (display:none, not unmounted), so a data-block-id lookup on a tabbed page matches BOTH tabs' lists; injecting a custom control into the hidden one makes it 'disappear' on tab switch. Add §4d: require the matched block to be visible (offsetParent !== null) and home into whichever tab is active so one control follows all tabs (each tab-list keeps its own conditional filter; ~250ms interval for snappier flips), plus a Gotchas bullet. Bump to 1.11.1

## [1.11.0] - 2026-06-12
- Add references/native-block-filters.md — dynamic date / URL-param filters and custom filter controls on native Softr List/Grid blocks. Covers driving a native block's conditional filter from a Custom Code Static block via {URL_PARAM:…}, the empty-param 'match nothing' wide-range sentinel that otherwise empties the list on load, injecting the control into the block's filter row scoped by data-block-id (a page-wide text search wrongly matches the nav 'Clients' link), resolving the row by filter-label-text + lowest-common-ancestor instead of hashed chip classes, and the key gotcha that Softr re-renders its List/Grid block and discards injected nodes so the control must be re-homed on a short interval rather than relocated once. Includes a full worked date-range picker (wide-range sentinel + wait-for-both + Clear + relocation + re-render survival) and a DevTools how-to for finding data-block-id and the filter row. Wire into the SKILL.md reference table and README structure listing; bump to 1.11.0

## [1.10.2] - 2026-06-12
- Document the autoNumber-formula blank-read gotcha — a formula that references an Airtable autoNumber field frequently reads back empty through Softr's data layer even though Airtable shows the value and a data re-sync doesn't fix it (sibling formulas without an autoNumber dependency read fine). Add to datasources/airtable.md Gotchas + the Formula row of the field table, with the JS rebuild-from-autoNumber fix and the plain-text-stamped-by-automation alternative; bump to 1.10.2

## [1.10.1] - 2026-06-12
- Document useFieldOptions companion-useRecords requirement — the hook only populates once an active useRecords in the same block has loaded the table schema; without it options settles to [] with isLoading false (bites write-only/helper blocks hardest). Add the required companion query to the example, correct the return shape to { options, isLoading } with options { id, label, color }, note the cross-table helper-block pattern, and add a prefer-live-fall-back-to-hardcoded recommendation; bump to 1.10.1

## [1.10.0] - 2026-06-04
- Bundle get-airtable-base CLI script for full base metadata export; document in SKILL.md, airtable.md, fields.md

## [1.9.0] - 2026-06-04
- Bundle get-softr-database CLI script for schema export; document in SKILL.md, softr-database.md, fields.md
- Bump publish workflow to Node 24-based action majors — actions/checkout@v4 -> @v6, actions/setup-node@v4 -> @v6 (clears the Node 20 deprecation; GitHub forces Node 20 actions to Node 24 on 2026-06-16). No version bump, so this run skips publish.

## [1.8.0] - 2026-06-04
- Expand references/native-chrome-styling.md to the full native shell — add Footer (semantic <footer> target + 160px/overflow-wrap contact-column email-wrap fix), floating "island" header/footer treatment, and Page background (Softr stacks the same fill on html/body/#page-content/inner-wrapper, so paint on html + clear the stack, EXCLUDING the .softr-topbar subtree so the dropdown panel survives) + a Console background-finder snippet; broaden SKILL.md Reference Guides row + README; add anti-patterns row for the page-background stacking; bump to 1.8.0

## [1.7.0] - 2026-06-04
- Add references/native-chrome-styling.md — restyle Softr's native header/top bar/nav/dropdowns via global Custom Code CSS (target stable .softr-* / ARIA-Radix selectors instead of regenerated f8f11e5_* hashes, the dropdown column-grid blank-space fix, icon/label color-inherit, restyle-vs-replace tradeoffs); add SKILL.md scope note + Reference Guides row; add two anti-patterns rows; update README; bump to 1.7.0

## [1.6.0] - 2026-06-03
- Document useNavigationBlocker for form-dirty navigation guards in Softr SPA mode

## [1.5.2] - 2026-05-27
- Document BLANK-guard convention for Airtable formulas — Airtable surfaces #ERROR! / #NaN! when arithmetic, date, or string operations touch a blank field and propagates the error through every downstream formula; add a quick-rule bullet calling out the failure modes (multiply/divide-by-blank, DATEADD on blank date), show the IF({field}, <expr>, BLANK()) and AND()-guarded shapes, note why explicit guards beat catch-all IFERROR (don't mask typos), and re-render the common-patterns block with guards applied to the date examples; bump to 1.5.2

## [1.5.1] - 2026-05-21
- Expand the "formulas in create/update" anti-pattern to cover every read-only field type (rollup / aiText / lookup / createdTime / lastModifiedTime / autoNumber, not just formulas), document the silent all-or-nothing parser failure (Actions tab empty, enabled stays false, every other writable field in the same q.select is lost), cite the verified 2026-05-22 wig-details-page.jsx case (Wig Tag ID formula + Total client/worker rollups + Instrucciones aiText all shared with useRecordUpdate), and point at the bisection diagnostic; bump to 1.5.1

## [1.5.0] - 2026-05-21
- Document write-side Action-disabled failure when a q.select alias references a renamed/missing Airtable column — extend datasources/airtable.md "Maintainability gotcha" with read-vs-write asymmetry (reads silently degrade, writes silently disable the entire Action), add the bisection diagnostic procedure for the "No actions used in this block yet" symptom, and add an anti-patterns Mutations-table row citing the verified 2026-05-21 Photos→Before Photos case; bump to 1.5.0

## [1.4.0] - 2026-05-21
- Document Softr Database MCP server — add references/softr-database-mcp.md (sibling to references/airtable-automations.md) covering connection, OAuth + PAT auth, Claude Code install, three permission scopes, 20 tools, why-it-matters for Vibe Coding, and the Softr-DB-only scope limitation; leave a short pointer in datasources/softr-database.md; promote MCP to option 1 for Softr DB field-ID discovery in datasources/fields.md; update SKILL.md Reference Guides table; add README TL;DR bullet, "What's Included" tree entry, and overview.md Key Concepts note; bump to 1.4.0

## [1.3.4] - 2026-05-21
- Use dynamic shields.io npm badge for version; bump to 1.3.4

## [1.3.3] - 2026-05-21
- Document field-type write shapes (Date, Date Range, Multi-Select, Checkbox, Attachment, Number); add async uploadAsync example; show useChartData bucket sample outputs; bump to 1.3.3

## [1.3.2] - 2026-05-21
- Fix CHANGELOG anchor detection in publish workflow; bump to 1.3.2

## [1.3.1] - 2026-05-21
- Add CHANGELOG.md with auto-generation on publish (workflow now prepends a new entry from commit subjects between version bumps and commits the updated CHANGELOG.md back to main with `[skip ci]`)
- Backfill CHANGELOG.md entries for 1.0.0 → 1.3.0 from existing git history
- Add CHANGELOG.md to the npm tarball via package.json `files`

## [1.3.0] - 2026-05-21
- Cross-link Airtable data source ↔ automation scripts (`datasources/airtable.md` and `datasources/writing.md` now point to `references/airtable-automations.md`)
- Refresh README's "What's Included" tree: add `airtable-automations.md` and `common-patterns.md`, update stale line counts, fix version badge

## [1.2.0] - 2026-05-20
- Add `building-design-md` companion section to SKILL.md and README
- Add install notes for the two-skill brand-to-blocks workflow

## [1.1.0] - 2026-05-20
- Package as an npm CLI: `npx softr-vibe-coding@latest init` installs into `~/.claude/skills/softr-vibe-coding/` and wires a `SessionStart` hook for auto-updates
- Add `references/airtable-automations.md` — Airtable Automation Scripts, Scripting Extension, and Airtable formulas (with `input.config()` / `input.secret()` rules, the `output` API divergence between environments, `updateRecordsAsync` duplicate-id rejection, batch-50 cap, field-ID-not-name discipline)
- Add detail-page back-button rule to placement Q&A; add Block Placement & Page Spacing section to SKILL.md; add brand-source detection step (DESIGN.md handoff)
- Document `useRecordUpdate.mutate()` parser requirements: method must be `.mutate()` not `.mutateAsync()`, payload must be nested `{ recordId, fields: {...} }` not flat
- Document `useNavigationSetting`'s `openIn` enum (`SELF` / `TAB` / `MODAL` only) and the canonical `<NavigationAction>` + `<Button asChild>` pattern, with per-action-type config requirements
- Document `OPEN_CHAT` data-source requirement (button-only helper blocks with no data source cause `chat/prepare` 500s)
- Document Global Data Restrictions as a separate permissions layer above block-level visibility
- Add anti-patterns: sub-components defined inside `Block()` (focus loss), brand fonts inside shadow DOM (need inline application), double-painted background on block wrapper, `document.getElementById` / `querySelector` failing silently inside blocks
- Verify and document Airtable column-name-only constraint with rename mitigations
- Codify three common Vibe Coding patterns and the network-inspector schema-discovery + AI-paste workflow
- Verify public Softr Database REST API write path
- Flatten repo layout: move `SKILL.md` and skill content to repo root for direct `~/.claude/skills/softr-vibe-coding/` consumption
- Add `.gitignore` covering sensitive and noise files

## [1.0.0] - 2026-04-14
- Initial release of the Softr Vibe Coding Block Claude Skill
- Full SKILL.md workflow, ui-ux-guidelines.md, references (helper-blocks, advanced-integrations, anti-patterns, quick-reference), data source guides for all 14 supported sources

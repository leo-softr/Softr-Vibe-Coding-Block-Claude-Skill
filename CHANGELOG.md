# Changelog

All notable changes to this skill are documented here. Versions follow [Semantic Versioning](https://semver.org/), and the format draws from [Keep a Changelog](https://keepachangelog.com/).

Entries from 1.3.1 onward are generated automatically from git commit subjects between version bumps (see `.github/workflows/publish.yml`). Entries before 1.3.1 were backfilled by hand from the existing commit history.

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

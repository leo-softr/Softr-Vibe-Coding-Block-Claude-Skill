# Changelog

All notable changes to this skill are documented here. Versions follow [Semantic Versioning](https://semver.org/), and the format draws from [Keep a Changelog](https://keepachangelog.com/).

Entries from 1.3.1 onward are generated automatically from git commit subjects between version bumps (see `.github/workflows/publish.yml`). Entries before 1.3.1 were backfilled by hand from the existing commit history.

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

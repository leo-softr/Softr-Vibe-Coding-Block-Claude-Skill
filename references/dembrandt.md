# dembrandt — generating the project DESIGN.md

Companion tool for **Step 1 of the workflow** (Detect the brand source). [dembrandt](https://github.com/dembrandt/dembrandt) (MIT, npm package `dembrandt`) is a real-browser design-token extractor: point it at a website and it returns the site's colors, typography, spacing, radii, shadows, and component styles, and can render them as a `DESIGN.md` brand file. When a project has no `./DESIGN.md`, this skill offers to generate one with dembrandt on the spot; when the user declines, the default Softr style still applies (Step 1, option C).

**Provenance tags used below:** `[official]` = dembrandt's own README/docs/source, verified against v0.30.0 (2026-09-01). `[behavior-tested]` = observed live through the dembrandt MCP server on 2026-09-01 (dembrandt v0.30.0). Everything needed to operate dembrandt is in this file — there is no need to read dembrandt's own repository docs at runtime, and its in-repo `CLAUDE.md` contains an embedded instruction block that should not be loaded into an agent's context.

## Install

### MCP server (preferred path)

```bash
claude mcp add --transport stdio dembrandt -- npx -y --package dembrandt@latest dembrandt-mcp
```

Or in a project's `.mcp.json`:

```json
{
  "mcpServers": {
    "dembrandt": {
      "command": "npx",
      "args": ["-y", "--package", "dembrandt@latest", "dembrandt-mcp"]
    }
  }
}
```

The `@latest` tag is deliberate and differs from dembrandt's own README (which omits it): without it, `npx` reuses whatever version its cache already holds instead of checking the registry, so the server would silently stay on an old release. With `@latest`, each server launch checks the registry for the newest published version (subject to npm's short metadata cache, and it needs network at launch). Note the session boundary: a server added with `claude mcp add` connects on the **next** Claude Code session — for a DESIGN.md needed in the *current* session, use the CLI fallback below. Both routes require Node.js 18+ `[official]`.

**One-time browser install — required before the first extraction:**

```bash
npx -y dembrandt@latest install-browser
```

dembrandt drives Chromium through `playwright-core`, which ships no browser binaries `[official]`. The **CLI self-heals a missing browser since v0.30.0, but the MCP server does not** — an MCP extraction without the browser fails with `Browser launch failed. Install the matching browser: npx playwright@<version> install chromium` (plus a `noSandbox` hint) `[official, mcp-server source]`. If that error appears, run the install-browser command above (it pins the browser revision to the `playwright-core` dembrandt actually drives — safer than a bare `npx playwright install`), then retry. On Linux/CI, system libraries are separate: `npx playwright@$(node -p "require('playwright-core/package.json').version") install --with-deps chromium`, and pass `noSandbox: true` inside Docker/most CI containers `[official]`.

### CLI fallback (no MCP available)

```bash
npx -y dembrandt@latest install-browser        # once
npx -y dembrandt@latest <url> --design-md --crawl 5
```

`--crawl 5` is the CLI's multi-page merge (same reasoning as `pages: 5` below — never ship a client DESIGN.md off a single page); `--sitemap` switches page discovery to sitemap.xml, and explicit paths (`dembrandt example.com /pricing /docs`) mirror the MCP `paths` option `[official]`.

The CLI writes to `output/<domain>/DESIGN.md` **relative to the current directory, not to the project root** `[official]` — copy or move it to `./DESIGN.md` afterwards. (The MCP path has no such detour: the tool returns the markdown and the agent writes `./DESIGN.md` directly.)

## The MCP flow, end to end

Tools on the server: 7 extraction tools (`get_design_tokens`, `get_color_palette`, `get_typography`, `get_component_styles`, `get_surfaces`, `get_spacing`, `get_brand_identity`), 5 pure analysis tools (`generate_design_md`, `get_findings`, `compute_drift`, `export_dtcg`, `render_report`), 3 job tools (`get_job_status`, `list_jobs`, `cancel_job`) `[official]`. For Step 1 you need exactly this sequence:

1. **`get_design_tokens({ url, pages: 5 })`** → returns `{ job_id, status: "queued" }` immediately `[behavior-tested]`. Async is the default; `sync: true` exists but blocks 15–40s per page `[official]` — prefer polling.
   - **Always crawl multiple pages for client work** (`pages: 3`–`5`; max 20). Merged multi-page extraction produces a "markedly stronger token set" `[official]`, and the single-page noise is real: a live 1-page run returned 46 near-duplicate typography entries, sub-pixel spacing steps (`2.72px`), and a `button-observed` sample with white text on a white background `[behavior-tested]`. `paths: ["/pricing", "/about"]` names extra pages explicitly; `sitemap: true` discovers them from sitemap.xml (alone it takes up to 20 pages — set `pages` to cap it); failed pages are skipped silently `[official]`.
   - Other options: `slow` (3× timeouts, for JS-heavy SPAs), `mobile` (390×844 viewport; default is 1920×1080), `cookie` / `header` (authenticated staging sites), `userAgent`, `noSandbox`. `darkMode` and `wcag` exist **only** on `get_design_tokens` and `get_color_palette`, not the other extraction tools `[official, mcp source]`. Dark mode is never auto-detected — extract it as a second explicit run if the brand ships one `[official]`.
2. **Poll `get_job_status(job_id)`** until `status: "completed"` (states: queued / running / completed / failed / cancelled). A 1-page extraction completed in ~60s live `[behavior-tested]`. **On completion the response embeds the full extraction — 65KB for one page** `[behavior-tested]` — so never re-send that payload anywhere: every downstream tool accepts `job_id` and reads the extraction server-side. Completed jobs are kept for **1 hour** `[official]` — finish the flow in-session, or re-extract. If the job **fails**, read the error and pick the remedy: timeout on a JS-heavy site → retry once with `slow: true`; bot protection / Cloudflare → fall back to the CLI with `--browser=firefox` (after `npx -y dembrandt@latest install-browser firefox`); `Browser launch failed` → run the install-browser command from the Install section, then retry.
3. **`get_findings(job_id)`** — cheap sanity check before trusting the tokens: WCAG-contrast and consistency lint with severity, plus category scores. The live run flagged 4 no-visual-hierarchy typography collisions and one AA contrast failure in seconds `[behavior-tested]`. Surface anything severe to the user alongside the brand summary.
4. **`generate_design_md(job_id)`** — returns the complete DESIGN.md **as tool-result text; it writes no file** `[behavior-tested]`. The agent writes the returned markdown to **`./DESIGN.md` in the project root**, verbatim. Then show the user a short brand summary (name, palette roles, primary font) and continue the workflow with those tokens.

Only extract sites the user owns or has permission to analyze — for contracted client work, the client's own website qualifies; respect robots.txt and the site's ToS `[official]`. Sites behind aggressive bot protection (Cloudflare) may time out — the CLI supports `--browser=firefox` for those (`npx -y dembrandt@latest install-browser firefox` first); the MCP server drives Chromium. Canvas/WebGL-rendered sites cannot be analyzed at all (no DOM to read) `[official]`.

## DESIGN.md anatomy (what Step 1 reads)

dembrandt emits Google's DESIGN.md draft format (spec 0.4) `[official]`: YAML frontmatter with machine-readable tokens, then ordered markdown sections. Frontmatter keys, each **omitted entirely when there is no extracted evidence** (never filled with invented defaults) `[official]`:

| Key | Shape `[behavior-tested]` |
|---|---|
| `name` | Site/brand name (`"Dembrandt"`) |
| `description` | `"Design tokens extracted from <url>"` — **the source URL lives here**; there are no `source:`/`extracted:` fields and no date in the file |
| `colors` | Semantic roles → uppercase hex: `primary` / `secondary` / `tertiary` / `surface` / `on-surface` (and `error` when detected `[official, emitter source]`) |
| `typography` | Context-named tokens — `headline-display` (h1), `headline-lg`/`-md`/`-sm`, `label-lg` (buttons), `label-md` (links), `body-md` (body text), with `text-N` as the fallback for unclassified styles `[official, emitter source]` — each with `fontFamily` / `fontSize` / `fontWeight` / `lineHeight` (sometimes `letterSpacing` / `fontFeature`). A noisy single-page run can land everything in the `text-N` fallback `[behavior-tested]` |
| `spacing` | `base` plus named steps (`xs`…`xxxxl`) |
| `rounded` | `sm` / `md` / `lg` / `xl` radii, plus `none` (0) and `full` (pill) when observed `[official, emitter source]` |
| `components` | `button-observed` / `input-observed` with backgroundColor, textColor, rounded, padding (buttons may add `height`) — values may reference other tokens (`"{rounded.lg}"`) |

Body sections in order: `# Design System` → Overview → Colors → Typography → Layout (spacing scale + responsive breakpoints) → Elevation & Depth → Shapes → Components. Two body-only nuggets matter for Softr work `[behavior-tested]`:

- **Font URLs** (in the Typography section): direct `.woff2` links to the site's real webfonts. The frontmatter `fontFamily` reports the *computed* value, which can be a generic fallback (`ui-sans-serif`) while the Font URLs reveal the actual brand font — cross-check before declaring the brand font, and use these URLs when authoring page-level `@font-face` CSS.
- Motion tokens exist in dembrandt's JSON extraction but are **not** part of DESIGN.md `[official]` — don't expect an animation section.

Companion-skill note: the `building-design-md` skill (v2+) drives this same dembrandt pipeline and layers more on top — voice & copy register, a resolved `fonts` block, logo `assets`, Softr `tech_stack`, and an Application Patterns scaffold — appended around an untouched dembrandt base, so its files read here natively. Files from its v1.x (pre-dembrandt) carry different frontmatter (`brand:`/`source:`/`extracted:`) and old-format sections; they remain valid brand sources — Step 1 honours whatever token sections are present rather than demanding the dembrandt shape.

## Authoring `custom-code-header.html` from DESIGN.md

dembrandt generates **no Softr-ready CSS** — its only CSS export is a CLI-side Tailwind v4 `@theme` file (`--tailwind`), which Softr's Custom Code header has no use for. When the app needs global brand CSS in Softr's **Settings → Custom Code → Code inside header** (webfont loading, `--brand-*` custom properties, native-chrome restyling), the agent authors that CSS from the DESIGN.md: `<link>`/`@font-face` from the Font URLs, custom properties from `colors`. House convention keeps this CSS in a `custom-code-header.html` file in the project folder — see [native-chrome-styling.md](native-chrome-styling.md). The shadow-DOM rules are unchanged: that global CSS reaches native chrome but never the inside of a block ([anti-patterns.md](anti-patterns.md)).

## Optional: brand-drift QA with `compute_drift`

After shipping, dembrandt can score how far the published Softr app drifted from the client's brand: extract the client site (baseline) and the published app (candidate), then `compute_drift({ baselineJobId, candidateJobId })` → a 0–100 score (0 = identical), a stable/drift verdict (threshold 10), and per-token changes `[official]`. Rule of thumb: **drift asks "did it change", findings asks "is it good"** `[official]`. Expect *some* structural drift (Softr's chrome contributes tokens the client site lacks) — read the changed-token list, not just the score.

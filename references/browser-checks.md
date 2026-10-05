# Checking a pushed block in a browser

How to check a deployed block's rendering and behaviour in a Softr preview with the
[agent-browser](https://github.com/vercel-labs/agent-browser) CLI. **Verified 2026-10-01** with
agent-browser v0.38.1 on macOS (Node 22) against a real Softr preview; only the commands under
[Untested but promising](#untested-but-promising) were not run. [Testing Custom Code header
CSS](#testing-custom-code-header-css) was verified 2026-10-05, except where it says otherwise.

## When to use it

After a push has passed the hash check in
[softr-mcp.md → Verifying a push](softr-mcp.md#verifying-a-push--the-deployed-source-is-the-only-proof).
The hash proves what Softr stored; a browser shows what it does: the layout at a given width, what
a control does, what a Save would send. **Not for data checks** (read records through the MCP or the
API), and **not for logged-in Studio or Airtable work**, which needs the user's own session and so
belongs to the user's own Chrome tool.

## Tool choice and why

**agent-browser**, because a check costs fewer tokens and can be made safe:

- One browser stays alive between shell commands (a daemon per `--session`), so a check is a few
  short commands rather than one script.
- `eval` prints only its result. The Playwright MCP's `browser_run_code_unsafe` repeats the whole
  script back in every result, under "### Ran Playwright code".
- Screenshots go to disk and cost nothing until someone opens one.
- It aborts requests by URL pattern and lists what a click sent: the write guard below.

An in-app or embedded browser pane stops rendering while it is hidden: IntersectionObserver and
`requestAnimationFrame` never fire, and screenshots time out. It can check scroll- or
visibility-driven behaviour only while it is visibly open.

## Install

Check with `agent-browser --version`. If it is missing, **ask the user before installing**: it is a
global npm package plus a Chrome for Testing download (182 MB, about 360 MB on disk under
`~/.agent-browser`). On a yes:

```bash
npm i -g agent-browser && agent-browser install
agent-browser doctor     # passed every check; a headless launch took about 0.9 s
```

npm may warn `EBADENGINE`, asking for Node ≥ 24. It ran fine on Node 22: that requirement is for
building from source, and the CLI is a native binary. If the user declines, drive a headless Chrome
with Playwright, or use an in-app browser only while it is visibly open.

## Why not the skills.sh `agent-browser` skill

vercel-labs also publish an `agent-browser` skill on skills.sh. Do not install it. Its description
tells the agent to prefer it over every built-in browser tool, and it triggers on generic requests,
even Slack ones. Yet it is only a stub that loads `agent-browser skills get core` (about 38 KB, some
10k tokens). The CLI serves that guide on demand, matched to the installed version: run
`agent-browser skills get core` yourself, and only when this recipe is not enough.

## The recipe

### 1. Session, preview cookie, page

Work from a scratch directory, not the project: nothing is written to the working folder, and
screenshots go where you tell them.

```bash
ab() { agent-browser --session softr-check "$@"; }   # a function, not a variable: see Gotchas
ab open '<previewUrl>' >/dev/null      # once per session: sets the preview cookie
ab set viewport 1280 900
ab open 'https://<subdomain>.preview.softr.app/<page>?recordId=<recordId>&autoUser=true'
ab wait --load networkidle             # works on Softr previews
ab wait 2500                           # 2000–3000 ms more, so the block's data hooks can load
```

`<previewUrl>` is what the MCP's `application_preview` returns. `open` prints the URL it opened, and
this one carries a sign-in token, hence `/dev/null`. The direct URL then loads the app itself, not
the toolbar shell that frames it, so `document` in `eval` is the app's.

### 2. Reaching into the block

A block renders inside a shadow root, which CSS selectors and `find` locators do not cross.
**Refs from the accessibility readout do**: `ab snapshot -i` lists the block's textboxes, buttons
and checkboxes as `[ref=eN]`, and `ab fill @eN '…'` and `ab click @eN` act inside the block. Grep
the ref out in the same shell call, so the readout never enters your context:

```bash
REF=$(ab snapshot -i | grep -o 'textbox "Search by[^[]*\[ref=e[0-9]*' | head -1 | grep -o 'e[0-9]*$'); ab fill "@$REF" 'term'
```

### 3. Measuring with `eval`

`ab eval "<expr>"`, or `ab eval --stdin < check.js` for anything longer. An async IIFE is awaited,
and only the result is printed: return `JSON.stringify(...)` to get one JSON-encoded line. Find the
block's shadow root by text only that block contains:

```js
(async () => {
  const root = [...document.querySelectorAll('*')].map(e => e.shadowRoot).filter(Boolean)
    .find(s => /<text unique to the block>/.test(s.textContent));
  if (!root) return 'block not found';
  const r = root.querySelector('<selector>').getBoundingClientRect();
  return JSON.stringify({ left: r.left, right: innerWidth - r.right, top: r.top, width: r.width });
})()
```

A date input has no ref (role `Date` in the full readout, absent from `-i`) and is React-controlled:
set it through the native setter, then fire both events, inside the IIFE once `root` is found.

```js
const i = root.querySelector('input[type="date"]');
const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
set.call(i, '2026-10-15');
i.dispatchEvent(new Event('input', { bubbles: true }));
i.dispatchEvent(new Event('change', { bubbles: true }));
```

### 4. Block saves before any click, and prove it

The preview writes to the live data
([softr-mcp.md](softr-mcp.md#testing-as-any-app-user-without-logins--the-preview-as-switcher)), so
before a check clicks anything that could save:

```bash
ab network route '*records-trigger*' --abort
ab eval "fetch('/records-trigger-probe-' + Date.now()).then(r => 'NOT BLOCKED ' + r.status).catch(e => 'blocked: ' + e.message)"
#   blocked: Failed to fetch
ab eval "fetch('/plain-probe-' + Date.now()).then(r => 'reached ' + r.status).catch(e => 'blocked: ' + e.message)"
#   reached 404 (the control: other requests still get through)
```

A `useRecordUpdate` save goes out as a PATCH, with the record ID in the path (see Gotchas):

```
PATCH https://<subdomain>.preview.softr.app/v1/datasource/applications/<app>/pages/<page>/blocks/<block>/datasources/<ds>/records-trigger/<recordId>
```

Only this update endpoint is verified. Before clicking a create or delete control, learn its URL
with `ab network requests` where a write is harmless, never on client data, and block that pattern
too. Do not assume `*records-trigger*` covers it.

### 5. Click, then read what it sent

Read the record through the database API, click Save by its ref (step 2), then read the record
again: `updatedAt` and the field should be unchanged. The aborted request is still logged, so you
see the payload without it reaching the server:

```bash
ab network requests --filter records-trigger   # lists the save, with its id
ab network request <id> --json                 # method: PATCH, postData: {"context":{…},"fields":{"<fieldId>":"2026-10-15"}}
```

### 6. Screenshots and cleanup

```bash
ab screenshot ./empty-1280.png         # ✓ Screenshot saved to …   (--full for the whole page)
ab network unroute
ab close                               # ✓ Browser closed (no process left behind)
```

Give a path; without one, it writes to a temp directory. A saved screenshot costs no tokens until
someone opens it; one shown inline costs about 1.5k. Left alone, the daemon exits after an hour idle.

## Testing Custom Code header CSS

CSS in **Settings → Custom Code → Code inside header** applies to every page of the app, and the
builder usually pastes it, not you. So test it in the preview before it is pasted, then prove what
went live. **Verified 2026-10-05** on one app with Softr's top bar and sidebar, using the app-frame
code in [native-chrome-styling.md → App frame (navigation layout)](native-chrome-styling.md#app-frame-navigation-layout)
with its Vibe-host rule in the unscoped form (see step 4), with agent-browser and the desktop app's
Browser pane; anything else is marked.

**Where header code shows:** on the published app, and in the preview: after a paste and a publish,
a fresh preview load applied it with nothing injected (verified 2026-10-05). Whether the preview
shows header code that is pasted but not yet published is untested. The Studio editor canvas is not
a test surface: header code is not known to render there.

### 1. Before pasting: inject it into the preview

Open the page as in [step 1](#1-session-preview-cookie-page), as the user whose navigation you are
styling: on the preview origin run `fetch('/studio/impersonate/<softrUserId>')`, then open the page
again ([how](softr-mcp.md#testing-as-any-app-user-without-logins--the-preview-as-switcher)). Then
inject the file exactly as it will be pasted, tagged so that a re-run replaces it:

```bash
node -e '
const h = require("fs").readFileSync("custom-code-header.html", "utf8");
process.stdout.write(`(() => {
  document.querySelectorAll("[data-hdr-test]").forEach(n => n.remove());
  const t = document.createElement("template"); t.innerHTML = ${JSON.stringify(h)};
  for (const n of [...t.content.children]) { n.setAttribute("data-hdr-test", ""); document.head.appendChild(n); }
  return "injected";
})()`);' > inject.js
ab eval --stdin < inject.js            # "injected"
```

- The injected copy lasts until the next load: inject again after every `open` or reload. A width
  change keeps it.
- This tests the `<link>` and `<style>` parts. A `<script>` in the header is out of scope.
- If an older version is already live, the preview carries it too and the injected copy only adds
  to it, so a rule you deleted still applies. Remove the live `<style>` first, found by a token
  only it contains (inferred, not run).
- A Browser pane opened on the preview link shows the toolbar shell, with the app in the
  same-origin `#preview-iframe`. Open the direct page URL instead, so that `document` is the app's.

### 2. Measure; screenshots are the extra

Computed values answer the question; a screenshot only illustrates it. A hidden pane times out on
screenshots ([why](#tool-choice-and-why)) but measures fine, so measure first and take any
screenshot with agent-browser, to disk. Save this as `measure.js`:

```js
(() => {
  const q = s => document.querySelector(s), bg = e => e ? getComputedStyle(e).backgroundColor : 'none';
  const main = q('#main-content'), sr = q('#sidebar-root'), a = sr ? getComputedStyle(sr, '::after') : null;
  return JSON.stringify({
    w: innerWidth, sidebar: !!q('.softr-sidebar'), tabBar: !!q('.softr-bottombar'),
    html: bg(document.documentElement), body: bg(document.body), page: bg(q('#page-content')),
    main: bg(main), radius: main ? getComputedStyle(main).borderTopLeftRadius : 'none',
    host: bg(q('#main-content [data-role="vibe-block-root"]')),
    corner: a ? a.content + ' @ ' + a.left : 'none',
    overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  });
})()
```

What the verified live code gave (2026-10-05; its Vibe-host rule was the unscoped
`#main-content [data-role="vibe-block-root"]`, and the recipe's scoped form is untested):

| Window | Navigation | `html`, `body`, `#page-content` | `#main-content` | `corner` |
|---|---|---|---|---|
| 768px and wider | top bar + sidebar | frame colour | sheet colour, 24px radius | `"" @ 280px` open, `"" @ 57px` collapsed |
| 767px and narrower | phone tab bar | sheet colour | transparent (`rgba(0, 0, 0, 0)`), 0px radius; the paper is on `html`, `body` and `#page-content` | `none @ auto` |

At the widths checked for it (1440, 1024 and 390/375) the Vibe host was `rgba(0, 0, 0, 0)` and
there was no sideways scroll. On phones `#sidebar-root` is still in the DOM, empty, 0px wide and
`position: static` (not sticky), which is why the corner rule is guarded with
`:has(.softr-sidebar)`. Without the guard the `::after` still renders there and is placed against
the page: likely off the right edge, adding sideways scroll (seen in a mock, not on Softr).

### 3. The width sweep

```bash
for w in 1440 1280 1024 900 768 767 390; do ab set viewport $w 900; ab wait 1200; ab eval --stdin < measure.js; done
```

Then collapse the sidebar (the top bar's "Toggle sidebar" button, a ref from `snapshot -i`; it
writes nothing) and measure 1024 and 768 again.

- **767 / 768 is Softr's switch, to the pixel:** 767 gives the phone tab bar, 768 the top bar and
  sidebar. At 768 with the sidebar open, a block gets 488px.
- **A plain width change switches the layout live.** `ab set viewport` alone moved between sidebar
  and tab bar; no reload needed.
- **Reload after leaving a mobile-device emulation.** A pane loaded under a mobile preset (an
  Android user agent and touch points, not just a width) kept the phone layout when widened to
  1440, until a reload (seen 2026-10-05; most likely a device check at load, inferred).
- **The collapsed sidebar stayed collapsed** at later widths in one headless run (seen once):
  open it again, or expect 57px.

### 4. Pages without navigation

The recipe scopes its rules with `:has(.softr-sidebar, .softr-bottombar)`, so pages without Softr's
navigation (log in, sign up, 404) should keep Softr's own colours.

- **Before pasting:** inject on a 404 page in the preview (any path that does not exist): `html`
  and `body` stayed rgb(255,255,255). A logged-in preview sends `/login` to the home page, so
  `/login` cannot be checked there.
- **Once pasted:** open `/login` and a 404 page on the published app, logged out. With the code
  live, `html`, `body` and `#page-content` stayed white on both, with no top bar, sidebar or tab
  bar (verified 2026-10-05).
- **The Vibe-host rule depends on which form you have.** In the verified live code it was unscoped
  (`#main-content [data-role="vibe-block-root"]`) and applied on these pages too; on a page without
  navigation that holds a Vibe block it is probably invisible, because the page behind the block
  is the same theme colour (inferred). The recipe scopes it with `:has(.softr-sidebar,
  .softr-bottombar)`, so nothing should apply there (untested as written). Either way, no page
  without navigation but with a Vibe block was tested: on one, check that the host keeps the
  theme white.

### 5. After the paste: prove what is live

**A publish publishes everything.** Header code reaches the published app with a publish, and a
publish also pushes every unpublished page live (seen 2026-10-05: unfinished pages went live with a
header-code publish). Before asking anyone to publish header code, check what else is unpublished,
and say so in the ask.

Then fetch the published page and pull the code out. Softr carries it in an inline script as
`appCustomHeaderCode: "…"`, an unquoted key inside `SoftrPageRenderer.render({…})`: JavaScript, not
JSON, so read the string literal rather than parsing the object. `json.loads` read Softr's string on
2026-10-05:

```bash
curl -sL 'https://<subdomain>.softr.app/' -o pub.html
python3 - <<'EOF'
import json, re
s = open('pub.html').read()
m = re.search(r'appCustomHeaderCode:\s*("(?:[^"\\]|\\.)*")', s)
if not m: raise SystemExit('appCustomHeaderCode not found: wrong page, a redirect or an empty body; fetch / again')
live = json.loads(m.group(1))
mine = open('custom-code-header.html').read()
rules = lambda t: re.sub(r'\s+', '', re.sub(r'<!--.*?-->|/\*.*?\*/', '', t, flags=re.S))
print(len(live), 'bytes live;', 'rules match' if rules(live) == rules(mine) else 'RULES DIFFER')
EOF
#   1516 bytes live; rules match
```

- **Compare the rules, not the text.** The pasted copy can lose or shorten comments; it did on
  2026-10-05, and the rules still matched.
- **`pageCustomHeaderCode`** is the page-level header code, and `appCustomFooterCode` /
  `pageCustomFooterCode` are the footers: check that they are empty, or hold what you expect.
- **The page source opens with `<!-- Last Published: … -->`.** Check that it moved, so you are not
  reading the previous publish.
- The key is in every page's source, logged out too: it was the same on Home, `/login` and a 404
  page.

Then run the sweep again in a fresh preview with nothing injected, and the pages without navigation
on the published app, logged out.

## Gotchas

- **zsh does not word-split.** `AB="agent-browser --session x"; $AB open …` fails with "command not
  found": use the function. Agent shells usually keep no functions or variables between calls, so
  define `ab`, and grep any ref, in the call that uses them; the browser lives on in the daemon.
- **Selectors stop at the shadow root.** `ab fill 'input[placeholder^="…"]' 'x'` gives
  `✗ Element not found`, and `find` locators fail the same way (upstream issue
  vercel-labs/agent-browser#1266, open since April 2026). Use refs, or `eval`.
- **Refs change on every page load.** Grep again after each `open` or reload.
- **Readouts are huge on data pages.** A table-heavy page measured 268 KB in full, 197 KB with `-c`
  and 164 KB with `-i` (or `-i -c`), about 40k tokens: `-i` keeps table cells as context for the
  buttons in them. A small page was 5.8 KB, 2.9 KB with `-i`. Never print one on a data page: grep
  it, or write it to a file.
- **Saves are PATCH, and the record ID is in the path.** A guard on POST misses them, and so does one
  that looks for the record ID in the body; that one once let a write through. Match the URL, never
  the method or the body.
- **Plain `ab network request <id>` printed only the URL** of the blocked save. Add `--json`.
- **A preview serves the version it was minted on.** After every push, mint a fresh one with
  `application_preview` and open it again before checking anything.
- **The preview URL is a sign-in token.** Never share it ([why](softr-mcp.md#application-management-tools)).
- **Attachment URLs are re-signed on every read:** compare by id, filename and size, never by URL.

## Measured

The same check, an empty-state centring check at two widths plus a screenshot, cost about 650 tokens
with agent-browser (2026-10-01) against about 1,540 with the Playwright MCP's run-code
(2026-09-30): about 58% less, mostly because Playwright repeats the script back. Learning the tool
in a fresh session cost about 1.6k tokens, once, without loading `skills get core`.

## Untested but promising

In agent-browser's docs, **not yet tried against a Softr preview**. Try one before relying on it:

- `ab pdf <path>`: to check a print layout ([printing.md](printing.md#7-gotchas-and-testing) has
  the verified Playwright route).
- `--init-script <path>` (before the first navigation) or `ab addinitscript <js>` (at runtime): for
  example, to stub `window.print` before load.
- `ab screenshot --if-changed`: skips a screenshot that matches the last one.
- `ab diff snapshot`: compares the current readout with the last one.
- `ab a11y`: the built-in axe-core accessibility audit.
- `--allowed-domains <list>`: restricts the session's network to the domains listed.

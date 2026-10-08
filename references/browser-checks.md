# Checking a pushed block in a browser

How to check a deployed block's rendering and behaviour in a Softr preview with the
[agent-browser](https://github.com/vercel-labs/agent-browser) CLI. **Verified 2026-10-01** with
agent-browser v0.38.1 on macOS (Node 22) against a real Softr preview; only the commands under
[Untested but promising](#untested-but-promising) were not run. [Testing Custom Code header
CSS](#testing-custom-code-header-css) was verified 2026-10-05, except where it says otherwise, and
[the client's time zone](#1-the-clients-time-zone) on 2026-10-08. The served-build proof in step 2,
the measuring and sizes rules in step 4, the create-save guard in step 6, [Forcing
states](#forcing-states) and [Exports and printouts](#exports-and-printouts) come from one
end-to-end QA pass of a 15-block app on 2026-10-08 (LCDB QA pass); a snippet marked as a sketch was
run on a local test page, not on a Softr preview.

## When to use it

After a push has passed the hash check in
[softr-mcp.md → Verifying a push](softr-mcp.md#verifying-a-push--the-deployed-source-is-the-only-proof).
The hash proves what Softr stored; a browser shows what it does: the layout at a given width, what
a control does, what a Save would send. **Not for data checks** (read records through the MCP or the
API; to compare a page's figures with those reads, see
[qa-playbook.md → Checking numbers against the database](qa-playbook.md#checking-numbers-against-the-database)),
and **not for logged-in Studio or Airtable work**, which needs the user's own session and so
belongs to the user's own Chrome tool. For a whole QA pass, in the order to run it, start at
[qa-playbook.md](qa-playbook.md); this file holds the browser mechanics it links to.

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

### 1. The client's time zone

Run every check in the time zone of the app's users, never the machine's. A headless Chrome takes
the zone of the computer it runs on, and a date-only value arrives as midnight UTC
([fields.md → Date-only fields arrive as midnight UTC](../datasources/fields.md#date-only-fields-arrive-as-midnight-utc)):
a block that parses it with `new Date()` or `parseISO` shows the right day east of UTC and the day
before west of it. On 2026-10-08 three blocks of an app for Pacific-time users had passed checks run in
Europe/Athens (UTC+3) while showing their users in America/Los_Angeles every date-only value a day
early. A test-data load found it, not the checks.

agent-browser has no time-zone setting (v0.38.1: no flag, and `set` offers none). Chrome takes its
zone from `TZ` in the environment of the daemon that launches it, so put `TZ` in the `ab` function:
then the command that starts the daemon carries it, whichever one that is. Check the zone straight
after launch:

```bash
ab() { TZ=America/Los_Angeles agent-browser --session softr-check "$@"; }   # the client's IANA zone
ab open 'about:blank' >/dev/null
ab eval "Intl.DateTimeFormat().resolvedOptions().timeZone + ' ' + new Date().getTimezoneOffset()"
#   "America/Los_Angeles 420"   (minutes behind UTC: 420 in summer time, 480 in winter)
#   "Europe/Athens -180"        = no TZ reached the daemon: the machine's zone
```

- **`TZ` counts only when the session's daemon starts.** Against a daemon already running,
  `TZ=America/Los_Angeles agent-browser … eval` still printed `Europe/Athens`. And `ab close` alone
  is not enough: the daemon outlives it by about a second, and an `open` in that second came back in
  the old zone. To change zone, close, wait until `agent-browser session list` no longer shows the
  session, then open again; or use a new session name.
- **Which zone:** the client's, from the project notes, as an IANA name (`America/Los_Angeles`,
  `America/New_York`). If the users span zones, run the date check ([step 5](#5-date-only-values-against-the-stored-ones))
  in each.
- **Verified 2026-10-08** with agent-browser 0.38.1 on macOS: `about:blank`, `example.com` and a new
  tab all reported `America/Los_Angeles` and 420, and a mock block rendering
  `new Date("2026-10-05T00:00:00.000Z")` showed Oct 5 in Athens and Oct 4 in Los Angeles. The zone
  belongs to the browser, not the page, so it holds on a Softr preview too (inferred, not run
  there).
- **Other browsers.** With Playwright (the fallback under [Install](#install)), pass
  `timezoneId: 'America/Los_Angeles'` to `browser.newContext()` (its documented option; not run
  here). An in-app Browser pane or the user's own Chrome runs in its machine's zone unless
  something overrides it: run the probe there before trusting any date it shows.

### 2. Session, preview cookie, page

Work from a scratch directory, not the project: nothing is written to the working folder, and
screenshots go where you tell them.

```bash
ab() { TZ=America/Los_Angeles agent-browser --session softr-check "$@"; }   # step 1; a function, not a variable: see Gotchas
ab open '<previewUrl>' >/dev/null      # once per session: sets the preview cookie
ab set viewport 1280 900
ab open 'https://<subdomain>.preview.softr.app/<page>?recordId=<recordId>&autoUser=true'
ab wait --load networkidle             # works on Softr previews, but not while a route aborts the block's reads (below)
ab wait 2500                           # 2000–3000 ms more, so the block's data hooks can load
```

`<previewUrl>` is what the MCP's `application_preview` returns. `open` prints the URL it opened, and
this one carries a sign-in token, hence `/dev/null`. The direct URL then loads the app itself, not
the toolbar shell that frames it, so `document` in `eval` is the app's.

**Do not wait for `networkidle` while a route aborts the block's reads** ([Forcing
states](#forcing-states)). The data hooks keep retrying, and the call did not return before the
shell's 120 s timeout (LCDB QA pass, 2026-10-08). Poll instead: fixed `ab wait 3000` steps, each
followed by an `eval` that looks for the expected text inside the shadow root. A selector-based wait
does not cross the shadow root (see Gotchas), so it cannot be the fallback.

**Prove which build the page loaded before you judge a change.** A fresh preview link, the
`version=` number in its URL and a press of the refresh button are not proof. The block's script
loads from `https://assets.softr-files.com/applications/<app>/vibe-coding/<page>/<block>/<versionId>/index.js`:
the page id, then the block id, then the `versionId` the push returned. That is the id in the served
script URL, **not** the id `vibe_coding_block_list_versions` shows for the same save (that tool
answers NOT_FOUND for a build id): report both, and use the first to prove what is served. Find the
URL in the page's resource timing, fetch that `index.js`, and count a string only the old build has
and one only the new build has (save it as a file and run it with `ab eval --stdin <`, step 4):

```js
(async () => {
  const u = performance.getEntriesByType('resource').map(r => r.name)
    .find(n => n.includes('/vibe-coding/') && n.includes('<blockId>'));
  if (!u) return 'script not found: the block has not loaded yet';
  const t = await (await fetch(u)).text();
  return JSON.stringify({ versionId: u.split('/').slice(-2, -1)[0],
    old: t.split('<old string>').length - 1, now: t.split('<new string>').length - 1 });
})()
```

`versionId` must equal the push result's, and `old` must be 0 and `now` at least 1 (the snippet ran
on a local test page with the same URL shape, not on a preview). **Never text-search the whole page
HTML for the string:** Softr also inlines the block's source, comments included, so an old string
can still match inside a comment that is never shown (LCDB QA pass, 2026-10-08: a search of the
page matched a code comment; the served `index.js` held "Reload the page and try again." once and
the removed "Refreshing" zero times).

### 3. Reaching into the block

A block renders inside a shadow root, which CSS selectors and `find` locators do not cross.
**Refs from the accessibility readout do**: `ab snapshot -i` lists the block's textboxes, buttons
and checkboxes as `[ref=eN]`, and `ab fill @eN '…'` and `ab click @eN` act inside the block. Grep
the ref out in the same shell call, so the readout never enters your context:

```bash
REF=$(ab snapshot -i | grep -F 'textbox "Search by' | grep -o 'ref=e[0-9]*' | head -1 | cut -d= -f2); ab fill "@$REF" 'term'
```

Match the role and name with `grep -F`, then pull out `ref=e[0-9]*`: a readout line can carry other
attributes before the ref (`[expanded=false, ref=e12]`), and a pattern that expects `[ref=` right
after the name misses it.

- **Hit-test before a coordinate click, in two parts.** `document.elementFromPoint(x, y)` must
  return the block's host: anything else means something of Softr's (the phone tab bar, the top
  bar) covers the point. Then `root.elementFromPoint(x, y)`, with the root found in step 4, must
  return the element you mean, such as the modal backdrop and not the panel. The second call alone
  ignores a fixed light-DOM bar on top, so a phone-size test that uses only it passes under the tab
  bar (LCDB QA pass, 2026-10-08).
- **A backdrop has no accessible name, so no ref.** Pick a point outside the panel that the hit test
  shows is the backdrop, then send the whole press and release the backdrop's guards listen to:
  `ab mouse move X Y`, `ab mouse down`, `ab mouse up` (LCDB QA pass, 2026-10-08: a backdrop click
  with a calendar open closed only the calendar).
- **A removed control is proven by searching every shadow root** for its text, `aria-label`, `title`
  and icon class, not `document`, which finds nothing inside a block.

### 4. Measuring with `eval`

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

A block that uses the brand `DatePicker` ([date-picker.md](date-picker.md)) has no date input: the
field is a button with a ref in `-i`. Click it, then click the day by its ref; each day is a button
named like `Thursday, October 15, 2026`.

**Measuring rules.** Measure every claim instead of eyeballing it; each of these once turned a wrong
"pass" into a finding (LCDB QA pass, 2026-10-08).

- **Prove the console capture on every load.** Run `ab console --clear` and `ab errors --clear`
  before each `open`, then log a probe after it (`ab eval "console.error('probe')"`) and see it
  listed. An empty console proves nothing until the probe shows.
- **Numbers, not looks.** A label is on one line when its height equals one line. "No sideways
  scroll" is `scrollWidth - clientWidth` of 0 on the document, the block and every scroller. Touch
  targets are 44px or more on phones. Save a screenshot to disk at every size.
- **Open every expandable row first.** A card in a grid widened the whole page by 163px at 375, and
  only after a history row was opened.
- **Past the edge is not always overflow.** Walk up to the element's clipping ancestor before
  calling it a defect: a screen-reader-only table inside `overflow: hidden` is fine.
- **An error must sit inside its dialog scroller's edges.** Compare its box with the scroller's top
  and bottom. A check that only looked for the text passed while the error sat 21px below the fold
  at 1280×800.
- **Measure a toast itself**, not the toaster list that holds it.
- **A ShadowRoot has no `innerText`.** It threw a TypeError; use
  `[...root.children].map(c => c.innerText).join('\n')`. `root.textContent` works but runs words
  together.
- **Make every lookup require its match.** A loose `aria-label` pattern matched "Download monthly
  trend as CSV" and compared nothing. Count rows by link `href`, not by a label that some widths
  hide (a "Last pickup" label found 3 of 10 rows at 1280).
- **Read figures from the root's text with a regex** (`textContent` plus a regex or `lastIndexOf`),
  not from a snapshot: far smaller on data pages.
- **Sample fast states with a 25 ms recorder.** An interval that logs a button's text and disabled
  flag, started from an idle page: a snapshot or screenshot can trigger Softr's refetch on window
  focus and show the busy state early.
- **To find what moved the page**, wrap `window.scrollBy` and log its arguments, `scrollY` and a
  timestamp. To check Escape order, add a spy on the document's bubbling `keydown`.
- **Truncation, placeholders and text under a close button:** `scrollWidth > clientWidth` everywhere
  a message shows (a 100-character message was cut to "This line was not saved: the app c…"), canvas
  `measureText` for a placeholder, and `Range.getClientRects` for header text under an absolutely
  placed close button.
- **Softr pages set `scroll-behavior: smooth` on `html`** (seen in the preview). A coordinate click
  below the fold does nothing and raises no error, and a measurement taken during a scroll reads
  mid-animation. Scroll with `behavior: 'instant'` in one `eval` and measure in the next.
- **A top-level `const` in `eval` stays in the page**, so a second run throws "already been
  declared". Keep the IIFE, or assign helpers to `window`.

**Sizes.** Check blocks at 1280×900, 1024×768 and 375×812, and modals also at 1280×600 and a
568×320 landscape phone (a date picker lost 5–7px in dialogs at 1280×600 and a third of its day
buttons on the landscape phone; nothing at the usual sizes showed it). Beside a sidebar, a block in
a 1024 window is only about 730–745px wide (measure it), which is under 48rem: a block whose
container queries switch at 48rem shows its phone layout on a tablet. Loop in zsh with two
variables, and print `innerWidth` each time so a shot that did not resize is caught:

```bash
for W H in 1280 900 1024 768 375 812; do ab set viewport $W $H; ab wait 1200; ab eval "innerWidth + 'x' + innerHeight"; done
```

CSS and container queries follow `set viewport`. A window `resize` handler did not run after it
once, so dispatch `new Event('resize')` after each change to be sure.

### 5. Date-only values against the stored ones

On every block that shows a date-only field, compare a few shown days with the stored ones, in
the client's zone ([step 1](#1-the-clients-time-zone)):

1. Read three or more records with the MCP's `database_list_records` and note each date-only value.
   Its first ten characters are the stored day: `"2026-10-05T00:00:00.000Z"` is 5 October.
2. Read the same records on the page, by a value that names each one (`innerText` keeps a space
   between table cells; `textContent` runs them together):

   ```js
   (() => {
     const root = [...document.querySelectorAll('*')].map(e => e.shadowRoot).filter(Boolean)
       .find(s => /<text unique to the block>/.test(s.textContent));
     if (!root) return 'block not found';
     const rows = [...root.querySelectorAll('tr, li, [role="row"]')];   // the block's row element
     return JSON.stringify(['<name 1>', '<name 2>', '<name 3>'].map(n => {
       const row = rows.find(e => e.textContent.includes(n));
       return row ? row.innerText.replace(/\s+/g, ' ').trim().slice(0, 160) : n + ': not found';
     }));
   })()
   ```

3. Each shown day must be the stored day. Every one a day early means the block parses date-only
   values with `new Date()` or `parseISO`: switch it to `toLocalDate`
   ([fields.md](../datasources/fields.md#date-only-fields-arrive-as-midnight-utc)).

- **A zone west of UTC is what exposes the midnight-UTC bug.** Midnight UTC on 5 October is still
  5 October anywhere at or east of UTC, and 4 October at 5 pm in Los Angeles. A check in Athens
  passes a block that is wrong for every user west of UTC, as three blocks did (step 1).
- **Check each place the block shows the date:** the list, the detail view, and the value an edit
  form opens with. A form that opens a day early can save the wrong day when the user only changes
  another field.
- **A "today" taken as the UTC day is wrong only part of the day.**
  `new Date().toISOString().slice(0, 10)` is tomorrow from 5 pm in Los Angeles (4 pm in winter), so
  a morning check misses it: look for it in the source instead, and run the "today" checks inside
  that window on purpose.
  - **When:** while UTC is already on another day than the client. West of UTC that is from the
    zone's offset before midnight until midnight (17:00 to 24:00 in Los Angeles in summer, 16:00 in
    winter). East of UTC it is from midnight until the offset (00:00 to 03:00 in Athens). Log the
    client's local time with each check (`TZ=America/Los_Angeles date`). A check at 00:50 in Los
    Angeles cannot show the bug, because both days agree (LCDB QA pass, 2026-10-08: two write-pass
    runs at 00:50 saved the right dates and still proved nothing about this class).
  - **What first:** form date defaults, "no later than today" limits, this-month figures, ages, and
    stamps in printouts and exports. A CSV "Generated" line read 2026-10-08T05:49Z while the client's
    clock said 22:49 on the 7th.
  - **Work out the expected labels from the page's own clock**, never hard-code them: read
    `new Date()` in the page and derive "Oct 1 to 7" from it. A label computed per render shows a
    day rollover only on the next render, so a test across local midnight needs a second render.
  - **Check rows dated the 1st of a month on purpose.** A one-day-early bug moves them into the
    month before, in per-month charts, "this month" counts and intake buckets. Find them with the
    MCP's `database_search_records` and OR conditions (`date IS 2026-10-01`, `IS 2026-09-01`, …), then
    see which bar or count each lands in.
  - **A block that shows no dates still gets a short date check.** Prove it from three sides: its
    data sources have no DATETIME field, its code never reads the clock (`new Date`, `Date.now`) or
    formats a date, and no rendered tab shows date-like text (a regex for month names,
    `yyyy-mm-dd`, `m/d/yyyy`, "today", "ago" and four-digit years) or a native date input.
  - **Get more rows on screen with a broad search.** A list that opens on 8 rows showed 25 with a
    common 4-digit search (part of many phone numbers), so a date check compares more records.
  - To reach a moment you cannot wait for (month end, year end, a clock change), fake the page clock:
    [Forcing states](#forcing-states).

### 6. Block saves before any click, and prove it

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

A create goes out the same way as a POST to `…/records-trigger/new`, and the one `*records-trigger*`
route blocked updates and creates alike (a live write pass and a blocked-create check, 2026-10-08).
Deletes are still unverified: before clicking a delete control, learn its URL with
`ab network requests` where a write is harmless, never on client data, and block that pattern too.
Do not assume `*records-trigger*` covers it. The URL shapes are in
[softr-mcp.md → What the server enforces on a block's data endpoints](softr-mcp.md#what-the-server-enforces-on-a-blocks-data-endpoints).

- **Re-probe the guard after every page load**, with the two `fetch` lines above. A guard you
  proved once is not one you proved for this page.
- **Clear the request log before a click**, so that the read after it belongs to that click:
  `ab network requests --clear`, click, then `ab network requests --filter records-trigger`. The
  log otherwise survives page loads and redirects (it outlived a create's redirect), so an old
  entry is not a new save.
- **A run-wide proof needs the log kept.** If you never clear it, one filtered read at the end
  shows that the whole run wrote nothing. Clearing per click loses that, so keep each per-click
  read, or do not clear.
- **At the end, summarise every non-GET request by method and endpoint**, not only
  `records-trigger`. A block's reads are POSTs to `…/datasources/<name>/records`, so count them by
  URL with `records-trigger` left out, never by method. A clean run showed 332 POSTs, all reads,
  and nothing on `records-trigger`.

### 7. Click, then read what it sent

Read the record through the database API, click Save by its ref (step 3), then read the record
again: `updatedAt` and the field should be unchanged. The aborted request is still logged, so you
see the payload without it reaching the server:

```bash
ab network requests --clear                    # before the click
ab network requests --filter records-trigger   # lists the save, with its id
ab network request <id> --json                 # method: PATCH, postData: {"context":{…},"fields":{"<fieldId>":"2026-10-15"}}
```

Read the body and URL from `postData`. An aborted save has no response, because nothing reached the
server. For requests that complete, `--json` carries a `responseBody` field (reads, and saves in a
write pass), though one run saw none for a save. So prove every save by reading the row back through
the MCP, not from the logged response.

- **Test a double tap with a real double click**, not two `element.click()` calls in one task. Two
  scripted clicks in one task slipped past a guard held only in React state and sent two writes
  that no user can send, while a real double click sent one (LCDB QA pass, 2026-10-08). Send the
  real thing at a point you have hit-tested ([step 3](#3-reaching-into-the-block)):
  `ab mouse move X Y`, then `ab mouse down`, `ab mouse up`, `ab mouse down`, `ab mouse up`; it sent
  one write on a preview. The shorter form is `ab dblclick @<ref>`, run on a preview dialog in the
  second round. Then read the code for the guard: it is set before the first `await` and held in a
  ref as well as state.
- **Force-click a control that should be disabled** and count the writes sent. A click that prints
  "Done" proves nothing: `ab click` reports success on a disabled control and does nothing.
- **Prove a lock by the payload and by `el.matches(':disabled')`.** Inputs inside a disabled
  fieldset still report `.disabled === false`, and `fill` on one changes only the page's copy.
- **After a failed save, change the form and press Retry**, then compare the retried request body
  with what the screen shows. The retry sent the values from the first click while the form showed
  new ones.
- **Prove a leave-the-page guard** by dispatching `new Event('beforeunload', { cancelable: true })`
  and reading `defaultPrevented`; without `cancelable` it is always false. The event fires on tab
  close, reload and outside links, **not** on an in-app link such as the sidebar, so a guard for
  those needs `useNavigationBlocker` ([common-patterns.md](common-patterns.md#navigation-blocker-for-unsaved-changes)).

### 8. Screenshots and cleanup

```bash
ab screenshot "$PWD/empty-1280.png"    # ✓ Screenshot saved to …   (an absolute path: see below)
ab network unroute '<pattern>'         # one pattern at a time; the bare form is the very last step
ab close                               # ✓ Browser closed (no process left behind)
```

Give a path; without one, it writes to a temp directory. A saved screenshot costs no tokens until
someone opens it; one shown inline costs about 1.5k. Left alone, the daemon exits after an hour idle.

- **Use an absolute path.** A relative path resolves against the daemon's working directory, not
  your shell's, and failed with "No such file or directory". Pass a scratch folder, so that nothing
  lands in the project root.
- **Avoid `--full` on app pages.** It drew the sticky sidebar in the middle of the page. Scroll the
  part into view (`ab scrollintoview <ref>`), wait a beat for the smooth scroll to end, and take a
  viewport shot.
- **Unroute by pattern, never bare, until the last click is done.** A bare `ab network unroute`
  also removes the write guard. Remove a forced-state route with the same pattern you added it with.

## Forcing states

Failed reads, slow saves, odd values and month ends rarely show up in normal use, so put them on
screen on purpose. None of these changes data: each is a browser-only trick. But the write guard
([step 6](#6-block-saves-before-any-click-and-prove-it)) must be in place in every session, and a new
session starts without it. **Verified 2026-10-08** with agent-browser 0.38.1 against a real preview
(LCDB QA pass); the two scripts and the route patterns are the ones that pass used.

### A fake clock

`--init-script` runs a script before the page's own code. It goes on the command that starts a new
session, so use a fresh session name, keep the time zone from [step 1](#1-the-clients-time-zone), and
give the script path in full (an absolute path: [step 8](#8-screenshots-and-cleanup)):

```bash
TZ=America/Los_Angeles agent-browser --session clock-check --init-script "$PWD/clock.js" open 'about:blank' >/dev/null
```

A new session starts with no routes and no preview cookie. Point `ab` at it, open the preview link in
it ([step 2](#2-session-preview-cookie-page)), then add and prove the write guard (step 6) before
any click.

`clock.js` replaces `window.Date` with one shifted by a fixed offset. `Date.now()`, `new Date()` and
`Date()` move; `new Date(x)`, `Date.parse` and `Date.UTC` stay real:

```js
(() => { if (window.__fakeClock) return; window.__fakeClock = true;
  const RealDate = Date, offset = RealDate.parse('2026-10-31T23:30:00-07:00') - RealDate.now();
  function FakeDate(...a) {
    if (!(this instanceof FakeDate)) return new RealDate(RealDate.now() + offset).toString();
    return a.length === 0 ? new RealDate(RealDate.now() + offset) : new RealDate(...a);
  }
  FakeDate.prototype = RealDate.prototype; FakeDate.now = () => RealDate.now() + offset;
  FakeDate.parse = RealDate.parse; FakeDate.UTC = RealDate.UTC;
  Object.defineProperty(FakeDate, 'name', { value: 'Date' });
  window.Date = FakeDate;
})();
```

The script runs again on every full page load, so the clock restarts at the target there and runs
on from it (read off the script, not measured). Moments worth testing in Los Angeles: Oct 31 at 23:30 (UTC is already Nov 1),
Dec 31 at 22:00 (UTC is already the new year), the first Monday of January, and the day after a
clock change. Every "this month" label held in the pass, and the year-end report showed "-0 items
out" for an empty year, a bug no real-time check would have reached.

**Reach a save-time check the UI blocks** by shifting the page clock just before Save. When a date
picker disables future days, pick today, set `window.Date` one day behind, click Save, then restore
it: the "no future date" guard fires and no request is sent.

### Hold a save in flight

To test double taps and "Saving" states, a script that wraps `window.fetch` can log every
`records-trigger` call and then reject it after 6 s, so nothing reaches the server (add and prove the
write guard in this session too). Start the session with it, as above:

```js
(() => { if (window.__hang) return; window.__hang = true; window.__writes = [];
  const real = window.fetch.bind(window);
  window.fetch = function (input, init) {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    if (/records-trigger/.test(url)) {
      window.__writes.push({ m: (init && init.method) || 'GET', u: url.replace(/^.*\/datasources\//, ''),
        b: String((init && init.body) || '').slice(0, 400) });
      return new Promise((_, rej) => setTimeout(() => rej(new TypeError('Failed to fetch')), 6000));
    }
    return real(input, init);
  };
})();
```

Read `window.__writes` afterwards. In the pass, five blocks each sent exactly one write on a double
tap, with the button disabled while it waited. Click as [step 7](#7-click-then-read-what-it-sent) says.

**Fail only some requests** with the same wrapper: reject from the Nth request to one read URL on
(the 4th and later reads of one table), and check that no page shows a figure built from half the
data. The same idea fails the Nth write.

### Fail reads by route

A block's reads are POSTs to `…/v1/datasource/applications/<app>/pages/<page>/blocks/<block>/datasources/<name>/records`,
where `<name>` is the name in `datasource.define`. None of these patterns matches the
`records-trigger` save URLs, so the write guard stays in place:

```bash
ab network route '*/blocks/<blockId>/datasources/*/records' --abort   # every read of one block
ab network route '*/datasources/<name>/records' --abort               # one read
ab network route '*/datasources/<name>/records/*' --abort             # a single-record read (…/records/<id>)
ab network unroute '<the same pattern>'                               # never bare: see step 8
```

- **Say which reads you broke.** A detail page's single-record read ends in `/records/<id>`, which the
  list pattern does not match: with the list pattern the lists failed while the profile still loaded.
- **Prove the route with a `fetch` to the exact URL** before you reload, as for the write guard.
- **The error state comes only after the hooks' retries**: 6 to 20 s in the pass. Hold the abort until
  it shows, sampling at 3, 6, 9, 12 and 20 s; letting go early lets a retry succeed. Do
  not wait for `networkidle` (step 2).
- **Find the block's root by text present in both states**, such as the h1: the normal text is gone
  in the error state.
- **A busy "Try again" shows only after the data has loaded once.** With no data yet, the error
  state disappears while Try again re-reads, because the data library resets the read to loading.
  Load the page, add the route, then trigger a background re-read without a click:
  `window.dispatchEvent(new Event('visibilitychange')); window.dispatchEvent(new Event('focus'))`.
  It refetched on one block and not on another (probably only once the data is stale). If nothing
  re-reads, abort the read, reload, wait for the error (about 11 s), then install the fetch patch,
  unroute, and press Try again.
- **Test Try again by failing every read, restoring them, pressing it once, and then checking every
  section.** A Try again that re-reads only the main list leaves the other failed reads failed:
  after it, every row said "No children on record" and the duplicate check ran with no children.
  Start the state recorder from an idle page ([step 4](#4-measuring-with-eval)).

### Serve a changed read

To put a state on screen that the data lacks, answer a read with an edited copy of a real one. Copy
a captured response with `ab network request <id> --json` (its `responseBody` field), edit it, and
serve it:

```bash
ab network route '*/datasources/<name>/records' --body "$(cat fake.json)"
```

- **Keep Softr's shape.** On Softr Database that is `{total, limit, offset, items, empty, complete: true}`;
  `complete: true` stops the paging.
- **Serve every empty-like value:** `null`, `''`, `0`, and the field missing. A threshold served as
  null showed "Threshold 2,000 (default)"; every threshold served as -999999 showed the new empty
  text; one block got negative stock and an empty product list the same way. No data changed.
- **Pick values where the old and the new behaviour differ**, so the check proves the setting was
  read. Remove the route with `unroute` on the same pattern, and prove it is gone by seeing real values.
- **The first route registered for a URL wins.** A mock added after an abort on the same URL never
  answers.
- **Change a setting only in page memory or in a served read, never in the table.** A monthly cap of
  12 was set to 2 in the page's memory to open its warning windows; the Settings table was never touched.

### "Saved, but a line failed"

To reach the state where a record saved and one of its lines did not, stub `window.fetch` for the one
create URL (a sketch, run on a local test page, not on a preview):

```js
(() => {
  window.__realFetch = window.__realFetch || window.fetch.bind(window);   // a second run would wrap the stub
  window.fetch = (input, init) => {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    if (/\/records-trigger\/new$/.test(url) /* && the create you mean: match its body, or count calls */)
      return Promise.resolve(new Response(JSON.stringify({ record: { id: 'qa-fake-1', fields: {} } }),
        { status: 200, headers: { 'content-type': 'application/json' } }));
    return window.__realFetch(input, init);
  };
})()
```

Return `{ record: { id, fields } }` with a JSON `content-type`. For the create, `network route --body`
was not enough: it sends no content type and the Softr SDK refused the response (reads served with
`--body` worked, above). Keep the original `fetch` in a global first, because a second run
otherwise leaves `window.fetch` undefined. Keep the `*records-trigger*` abort behind the stub, so the
stubbed create is the only one that answers and every other write is still blocked. The footer then
read "The allotment is saved, but 2 size lines are not", Close and Retry worked, and the
tables were unchanged afterwards.

## Exports and printouts

A headless run gets neither a download nor a pop-up window, so capture them in the page. Both
sketches ran on a local test page, not on a preview.

**A CSV.** Before the click, stub `URL.createObjectURL` to keep the Blob and
`HTMLAnchorElement.prototype.click` to do nothing, then click the export and read the Blob:

```js
window.__csvs = [];
URL.createObjectURL = b => { window.__csvs.push(b); return 'blob:stub'; };
HTMLAnchorElement.prototype.click = () => {};
// click Export, then read it in an async IIFE (a top-level `await` is a SyntaxError in `ab eval`):
(async () => JSON.stringify([await window.__csvs[0].text(),
  [...new Uint8Array(await window.__csvs[0].arrayBuffer(), 0, 3)].map(x => x.toString(16))]))()
//   ["<the CSV text>",["ef","bb","bf"]]   ef,bb,bf = the BOM
```

`Blob.text()` drops a UTF-8 BOM, so check the BOM through `arrayBuffer()`. A "Generated" line read
UTC (05:49Z on the 8th while the client's clock said 22:49 on the 7th); after the fix it read the
local time with its offset.

**A printout.** The Print control opens a window of its own ([printing.md](printing.md)). Replace
`window.open` with a hidden iframe that stands in for the print window, count its `print()` calls,
and measure the printout's cells in it, 700px wide for roughly A4 or Letter at 14mm margins:

```js
window.__prints = 0;
window.open = () => {
  const f = document.createElement('iframe');
  f.style.cssText = 'position:fixed;top:0;left:0;width:700px;height:900px;border:0;visibility:hidden';
  document.body.appendChild(f);
  f.contentWindow.print = () => { window.__prints++; };
  window.__printWin = f.contentWindow;
  return f.contentWindow;
};
// click Print, wait about 5 s, then measure inside window.__printWin.document:
// [...window.__printWin.document.querySelectorAll('td')].map(td => [td.scrollWidth, td.clientWidth])
```

The wait is longer than a beat: [printing.md §3](printing.md#3-print-only-when-it-is-ready)
holds `print()` until the stylesheets, fonts and images are in (capped at about 4 s), plus 250 ms, so
an earlier read finds `__prints` still 0. A cell that never wraps overflows its column without any
error; one month label longer than its column was found this way. For the Playwright pop-up route,
see [printing.md → Gotchas and testing](printing.md#7-gotchas-and-testing).

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

Open the page as in [step 2](#2-session-preview-cookie-page), as the user whose navigation you are
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
  The same slip in a viewport loop (`set -- $vp`, or `ab set viewport $vp`) left every shot at 1280
  in more than ten checks of one pass: see Sizes in step 4.
- **More shell slips that spoil a run.** zsh: `echo ====` fails with "== not found" and stops the
  chain (quote it), a function named like an alias will not define, and `"$d[^[]…"` inside a
  double-quoted pattern is read as an array subscript. macOS: there is no `timeout`, `sed -i` needs
  `''` (patch with Python instead), and a stray `cat > file` inside a multi-line command waits for
  input until the call times out at 120 s: run hash loops from a script file, with `< /dev/null`.
- **Selectors stop at the shadow root.** `ab fill 'input[placeholder^="…"]' 'x'` gives
  `✗ Element not found`, and `find` locators fail the same way (upstream issue
  vercel-labs/agent-browser#1266, open since April 2026). Use refs, or `eval`.
- **Refs change on every page load, and on any DOM change.** Grep again after each `open` or reload,
  take the ref from a snapshot in the same command as the click, and take a second snapshot after
  opening a dialog or a list (the first can miss it). A new row's list may need a second open before
  its option refs appear. While an `aria-modal` dialog is open, `snapshot -i` lists only the dialog.
- **Grep by the role the markup really has.** A segmented control built from radio inputs reads as
  `radio "X"`, not `tab`.
- **`fill` has traps.** On a number input that holds text it appends ("-3" then "2.5" gave "-32.5").
  `fill ''` empties the input but leaves React's state on the old value. `fill` with an empty ref
  types into whatever has focus. Inside a disabled fieldset only the page's copy changes. A fill also
  changed a field behind an open modal, so close dialogs before row checks. Set a value with the
  native setter plus `input` and `change` events (step 4), then type with `ab keyboard type`.
- **Select-all is unreliable headless.** `Meta+a` failed in one run and `Control+a` in another: use
  the native setter. An in-app browser pane's `type` action inserts text without key events, so it
  can make a correct control look broken.
- **Readouts are huge on data pages.** A table-heavy page measured 268 KB in full, 197 KB with `-c`
  and 164 KB with `-i` (or `-i -c`), about 40k tokens: `-i` keeps table cells as context for the
  buttons in them. A small page was 5.8 KB, 2.9 KB with `-i`. Never print one on a data page: grep
  it, or write it to a file.
- **Updates are PATCH, creates are POST, and an update's record ID is in the path.** A guard on POST
  misses updates, and so does one that looks for the record ID in the body; that one once let a
  write through. Match the URL, never the method or the body.
- **Plain `ab network request <id>` printed only the URL** of the blocked save. Add `--json`.
- **A preview serves the version it was minted on.** After every push, mint a fresh one with
  `application_preview` and open it again before checking anything, then prove which build loaded
  (step 2).
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
- `ab addinitscript <js>` (at runtime, on a session that is already open): for example, to stub
  `window.print` before load. The `--init-script <path>` flag at session start is verified: see
  [Forcing states](#forcing-states).
- `ab screenshot --if-changed`: skips a screenshot that matches the last one.
- `ab diff snapshot`: compares the current readout with the last one.
- `ab a11y`: the built-in axe-core accessibility audit.
- `--allowed-domains <list>`: restricts the session's network to the domains listed.

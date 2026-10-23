# QA of a Softr Vibe Coding app

How to QA an app made of Vibe Coding blocks, end to end, in the order to run it. This file is the
procedure and the reasons behind it. The mechanics are linked, not repeated: the browser commands
are in [browser-checks.md](browser-checks.md), the MCP in [softr-mcp.md](softr-mcp.md) and the data
shapes in [datasources/](../datasources/overview.md).

**Verified 2026-10-08.** Written from one end-to-end QA pass of a 15-block back-office app on Softr
Database: 68 findings, two rounds of fixes and a live write pass. Each rule below
cost someone a wrong result first. The second round of the pass, the same day, added the walk of a
successful save and what the read-only checker does (QA round 2). Later builds and pushes added,
on 2026-10-15, how to keep the push scripts, a jsdom render of a block's own code, a recipe for
proving a read guard, a cross-block contract check, gating a pipeline's stages and saying what did
not run.

## When to use it

When an app's blocks are built and pushed (each push has passed the hash check in
[softr-mcp.md → Verifying a push](softr-mcp.md#verifying-a-push--the-deployed-source-is-the-only-proof)),
before the client relies on it, and again after each round of fixes. For a quick look at one
block, [browser-checks.md](browser-checks.md) is enough.

## The order of a pass

1. [Set-up](#set-up): which app to test, with which build, in which zone.
2. [Never writing by accident](#never-writing-by-accident): the guard first, the proof last.
3. [Roles](#roles): each page as each kind of user.
4. [Logged out](#logged-out): access from outside the browser, and
   [proving a read guard](#proving-a-read-guard).
5. [Measuring](#measuring): sizes, and numbers instead of looks.
6. [Checking numbers against the database](#checking-numbers-against-the-database).
7. [Testing edges on purpose](#testing-edges-on-purpose): failures, clocks, odd values.
8. [Proving a fix before and after](#proving-a-fix-before-and-after).
9. [Live write pass with a read-only checker](#live-write-pass-with-a-read-only-checker), only when
   a fix needs a real save.
10. [Running QA with several agents and skeptics](#running-qa-with-several-agents-and-skeptics).
11. [Say what did not run](#say-what-did-not-run), wherever a push or a pass is reported.

## Set-up

- **Prove the connector can open the app before any preview or QA wave:** call `application_get` on
  the app id and `workspace_list`, and stop at once if the app's workspace is missing. A connector
  can read as connected while signed in to another Softr account, and subagents inherit that login
  ([softr-mcp.md](softr-mcp.md#permissions-model)).
- **Check changes in the preview (the draft), not the live app.** A push reaches the draft, and the
  live app changes only when someone publishes. Only two things run on the published app: the
  [logged-out checks](#logged-out) and the re-check after a publish.
- **Mint a fresh preview link for each session and after every push** (`application_preview`), and
  again when a page in a long pass lands on `/login`: that is the session ending, not a permission
  fault ([browser-checks.md → Gotchas](browser-checks.md#gotchas)). The
  link is a sign-in token: never print it, store it, or write it into a script file
  ([browser-checks.md → Gotchas](browser-checks.md#gotchas)).
- **Prove which build is served before you judge a change**
  ([browser-checks.md → step 2](browser-checks.md#2-session-preview-cookie-page)).
- **Run every check in the client's time zone**
  ([browser-checks.md → step 1](browser-checks.md#1-the-clients-time-zone)).
- **Give each agent its own `--session` name.** Agents that share an agent-browser session
  overwrite each other's pages.
- **Log times with `date -u`.** The machine's zone may not be the client's: the pass ran on a Mac at
  UTC+3 for an app used at UTC−7, and UTC is the one clock that the stored stamps use.
- **Keep the push and check scripts, and any working copy of a blocked push, outside the session's
  scratch folder.** A scratch folder can be wiped overnight, and one was, with the planning, gate
  and replay scripts in it. Put the scripts in a stable folder with a pinned dependency file, make
  the gate script install its own dependencies when they are missing, and keep no secrets or client
  data there. Copy the working copy of a push that cannot go out into the project the same day,
  under a name nobody can mistake for the mirror (a "pending push" folder, with "not deployed" and
  the sha in the file names), and leave the mirror at the deployed bytes until the push is read back
  ([softr-mcp.md → When a push is blocked](softr-mcp.md#when-a-push-is-blocked)).
  To recover a lost script from the session transcripts, replay **every** revision of it in time
  order: the first version of one gate script lacked three rules that later revisions added.

Why: agents judged fixes on stale builds, shared one browser session across parallel agents,
logged times in the wrong zone (QA pass, 2026-10-08) and lost their push scripts to a wiped
scratch folder.

## Never writing by accident

The preview is wired to the live data
([softr-mcp.md](softr-mcp.md#testing-as-any-app-user-without-logins--the-preview-as-switcher)), so a
pass against a client's database has to leave no trace.

- **Block every save before the first click, and prove the block works**
  ([browser-checks.md → step 6](browser-checks.md#6-block-saves-before-any-click-and-prove-it)).
  Probe again after every page load.
- **Press Save on purpose only with the guard proven**, and after you have read the save's own
  guard in the source. Confirm in the request log that each write was aborted. A write that gets
  through is reported at once, with its record id.
- **Afterwards, prove with MCP reads that nothing was written:**
  - exact per-table counts against a baseline taken before the pass;
  - the records you opened, by `updatedAt` (get the record);
  - rows whose own fields point at the QA day or the QA logins (entered by, updated by, a date
    field).

  `database_search_records` ignores a sort on `updatedAt` and rejects a filter on `id`, so do not
  rely on either to show "nothing unlisted" (write pass checker, 2026-10-08).
- **A race you cannot reproduce live with writes blocked stays in the local harness**, and the
  report says so. "A second row still saving" is one: the first write fails at once, so the second
  is never reached.
- To put a state on screen without changing data, see [Forcing
  states](browser-checks.md#forcing-states).

## Roles

Role bugs were found only when a pass compared roles side by side: hints that pointed users to pages
they could not open, admin pages that opened blank for volunteers, and an update action with no
record condition (QA pass, 2026-10-08).

- **Check each page as an administrator, as an ordinary user, and as a logged-in user in no
  group.** Impersonate rather than log in
  ([softr-mcp.md → Preview as](softr-mcp.md#testing-as-any-app-user-without-logins--the-preview-as-switcher)).
- **Read each block's Visibility first.** A block gated to one group does not render for the
  others, so its role-dependent copy cannot be checked from those roles.
- **Use the administrator as the positive control.** Count the controls the lower role must not see
  (void buttons, adjustments): an administrator saw 8 and 13 void buttons on two records where the
  volunteer saw none, only a hint. A missing control is then proven, not just unseen.
- **Prove each impersonation took effect.** After `fetch('/studio/impersonate/<softrUserId>')` on
  the preview origin, reopen the direct page URL and read the global:

  ```js
  JSON.stringify(window.__softr_current_user)   // name, email, avatar, userGroups
  ```

  On a direct page URL it sits in the top window; only the toolbar shell lacks it, where it is in
  the app iframe ([Preview as](softr-mcp.md#testing-as-any-app-user-without-logins--the-preview-as-switcher)).
  The `fetch` returns 200 even before the page switches user, so read the global after reopening.
  Take `<softrUserId>` from `application_list_users`, which lists manual memberships only: a
  conditionally matched group shows only in this global
  ([softr-mcp.md → Condition-based user groups](softr-mcp.md#condition-based-user-groups)).
- **Read what each role is told, not only what it can click.** An empty state or a hint that sends a
  role to a page it cannot open is a bug: three blocks pointed volunteers at Settings.
- **Check page visibility for every role**, and **every UPDATE or DELETE action on a per-user
  table.** At "logged-in users" with no record condition, any login can overwrite another user's
  row. What the server does and does not enforce is in
  [softr-mcp.md](softr-mcp.md#what-the-server-enforces-on-a-blocks-data-endpoints).

## Logged out

A publish can change what an anonymous visitor reaches, and nothing in the browser session shows it.
After every publish, check from outside the browser:

```bash
HOST=<subdomain>.softr.app          # or the app's custom domain
curl -sI "https://$HOST/<page>" | grep -i -E '^(HTTP|location)'
#   HTTP/… 301
#   location: /login?next-page=/<page>
curl -s -o /dev/null -w '%{http_code}\n' -X POST -H 'content-type: application/json' -d '{}' \
  "https://$HOST/v1/datasource/applications/<app>/pages/<page>/blocks/<block>/datasources/<name>/records"
#   403
curl -s -o /dev/null -w '%{http_code}\n' "https://$HOST/sign-up"   # 404 when sign-up is off
```

- **Every page that is not meant to be public** answers with a 301 to
  `/login?next-page=<path>`. An app with a public landing page returns 200 there.
- **A POST to a block's records endpoint with no session** answers 403. The published-host form of
  this URL is inferred from the one the preview calls (on `<subdomain>.preview.softr.app`); the 403
  was seen on 2026-10-08.
- **A logged-out probe proves little while the page is logged-in-only.** The 403 is then the page's
  own rule, and it is the same before and after a guard on the block, so it says nothing about what
  an anonymous visitor would get once the page is public. What proves a block-level guard is the
  signed-in comparison across blocks that read the same table
  ([below](#proving-a-read-guard)). State which half is proven. A page made over the MCP starts at
  the app's default VIEW permission (logged-in users), and making it public is
  `application_page_set_permissions` ([softr-mcp.md](softr-mcp.md#pages-permissions-and-deleting)). Once the page is public, repeat the
  logged-out probe from `curl` with no cookies and from a private window. Expect 403, or 200 with
  `total` 0; a record id or a field value anywhere in the body is a failure. Then submit the form
  once from a logged-out browser and watch the row land.
- **If sign-up is meant to be off**, `/sign-up` returns 404, and on `/login` the public
  `window.application_context` shows `signUpSettings.policy` as `DISABLED` (a read-only check).
- **Never POST to a `records-trigger` URL to test a write endpoint.** If the action is open, it
  writes. Read the block's action permissions through the MCP instead (a push puts them back to
  Softr's defaults: [softr-mcp.md](softr-mcp.md#verifying-a-push--the-deployed-source-is-the-only-proof)).

### Proving a read guard

A block whose connection exists only to create has a records endpoint like any other. The case
probed was a public form (a sign-up or a check-in has the same shape, but none was probed), and
there the endpoint answered: on 2026-10-15 a signed-in session that posted to it got the row count
of the whole table and every row's id. It got no values, because the block selected no fields. The
guard is a Source condition that no row can match, set on that connection with
`vibe_coding_block_set_data_source_record_filters`. What the server enforces is in
[softr-mcp.md](softr-mcp.md#what-the-server-enforces-on-a-blocks-data-endpoints), and the probe the
recipe comes from is in
[softr-mcp.md](softr-mcp.md#a-create-only-connection-on-a-public-block). The condition is per block
and per connection, so every other block that reads the table for a public page needs a guard of its
own. Steps 1 and 5 write real rows, so this is a live write pass: get the owner's go-ahead first, and
keep the manifest as described in [Live write pass](#live-write-pass-with-a-read-only-checker). To
prove a guard, in this order:

1. **Make the test rows first**, over the MCP, marked so that nobody takes them for client data and
   no queue, report or count lists them: a status that no queue reads, a source of "Test", and a
   reason line that says who made the row, when, and "Safe to delete". They carry no email
   ([a test row must not create a user](#live-write-pass-with-a-read-only-checker)). With no rows
   in the table, `total` 0 before and after proves nothing.
2. **Set the save guard and prove it** before the first probe
   ([Never writing by accident](#never-writing-by-accident)).
3. **Probe as the signed-in preview user, with the same body, before and after the guard.** Before:
   the test row's id comes back, with empty fields. After: `total` 0 and no items. Also send what a
   crafted request could try: filters on fields the block does not select, extra body keys such as
   `select`, `fields` and `fieldIds`, and a filter that tries to undo the condition. Each must give
   0 too, because filters fail open
   ([reading.md](../datasources/reading.md#filters-fail-open)).
4. **Read the condition back** with `vibe_coding_block_get_settings` (`dataSources[].condition`). A
   filter change adds no version, so `vibe_coding_block_list_versions` cannot show it, and it sits
   on the draft until the app is published.
5. **Prove the form still works.** Remove the save guard and prove its removal (the first probe line
   of [browser-checks.md → step 6](browser-checks.md#6-block-saves-before-any-click-and-prove-it)
   now reaches the server). Fill the form once as a test user, press Send once, and read the request
   log: one non-asset request, a `POST …/records-trigger/new`, status 200
   ([step 7](browser-checks.md#7-click-then-read-what-it-sent)). Then read the new row through the
   MCP. It is a real submission, so mark it as a test at once, before a queue or an automation
   picks it up.
6. **A second agent in a fresh session** redoes the probes, compares a neighbouring block on the
   same table (it must still return the rows, which shows the guard is per block), reads the
   settings back, matches the block's sha with the mirror, and checks with
   `vibe_coding_block_list_versions` that no code write came after the first test row. It writes
   nothing.
7. **Test rows stay until a person deletes them** (in this practice agents delete nothing). List
   them in the manifest so they can be purged
   ([Live write pass](#live-write-pass-with-a-read-only-checker)).

The cost of the guard is that the block can never read back its own row. A form that must show
the submission needs another route, not the guard removed.

## Measuring

Measure, do not eyeball. The rules are in
[browser-checks.md → step 4](browser-checks.md#4-measuring-with-eval): prove the console capture on
every load, numbers for heights and scroll widths, an error inside its dialog's edges, focus
recorded over time, Escape order proven by a spy on `document`, a shadow root without `innerText`,
and the sizes to check, which include the width a block really gets beside a sidebar.

- **Hit-test in two parts before a coordinate click.** `document.elementFromPoint` must be the
  block's host and `root.elementFromPoint` the element you mean. The shadow root alone ignores
  Softr's fixed phone tab bar, so a phone-size test that uses only it passes under the bar
  ([browser-checks.md → step 3](browser-checks.md#3-reaching-into-the-block)).
- **Look at the whole page, not just the part you changed.** Two buttons wrapping onto a second line
  at 1280 were noticed during an unrelated focus check and fixed the next day.

## Checking numbers against the database

A page can look right and be wrong, and a browser cannot tell. Compare it with the database.

- **Recompute every figure with the MCP's aggregate and list reads**, using the client's month
  boundaries and the app's own exclusions (voided rows, records entered in error). Compare each
  page's figure with that number, and with the same figure on every other page that shows it.
- **Hold one counting rule per figure.** The "same number on every page" lens found 7 of the 15
  major findings: allotments counted as served, received with or without repacked bulk, headcount
  per row or per person. Where two pages cannot show the same number, compare it term by term
  against the database and word the check "same rule, same terms".
- **Before you trust a boundary, check that rows exist on the boundary days** (Dec 31 and Jan 1, the
  last and first day of each month in range). If none do, say so: every total matches with or
  without a one-day bug. Base the boundary on the code (dates compared as `yyyy-mm-dd` text) and on
  a one-day range read against the server. In one report the nearest rows were Dec 29 and Jan 2.
- **Read the live table before you trust a counting rule.** Old or migrated rows may have empty
  links and drop out of past years. Check what one linked row stands for: a link counted child
  rows, not visits, with voided rows included. Before a fix changes a `select`, make the two checks in
  [multi-datasource.md](../datasources/multi-datasource.md#one-connection--one-read-payload-the-union-of-its-selects):
  the field is in the connection's field list, and a shared alias maps to the same field id in both
  selects.
- **Pair each before and after with an independent count.** `DISTINCT` on a link field counted
  distinct people in one call (it worked in one run and was refused in another): 57 + 296 + 43 = 396
  showed that a tile reading 442 was wrong, and later matched the fixed tile. When the call is
  refused, count the people from the rows.
- **Recompute the expected figure at check time.** Never use a baseline plus deltas from notes:
  when agents write at the same time, the shared totals move under you.
- **Check one complete past year as well as the year in progress**, and for a header-and-lines
  ledger make the period's line count equal the sum of the headers' link counts (an `IS_EMPTY`
  filter on the line's header link must return 0).
- **A reconciliation flag must be seen to fire, or it is no guard.** A "table total against pivot
  total" flag built from the same ledger rows cannot detect an orphaned row, because both sides
  include it: build the fixture and watch it fire.
- **Rows shown rounded to two decimals can differ from their total by 0.01 per row.** That is
  display rounding, not a bug: allow a tolerance of 0.01 times the row count.
- **Have the QA synthesis name, for each finding, the fix site (the block and the code), the exact
  change, and the figure you now expect after the fix** (for example "September children 442 →
  396"). The fixers and the final cross-check work from that line and prove each fix with a number.
- **Date-only values and boundaries** have their own steps: [browser-checks.md → step
  5](browser-checks.md#5-date-only-values-against-the-stored-ones).
- **Every filter must be seen to narrow the result**, with row counts with and without it: filters
  fail open ([reading.md](../datasources/reading.md#filters-fail-open)).
- **Prefer filter-only calls with one metric each**, and check that the parts add up to the
  unfiltered total. The aggregate tool refused some combinations in the pass, and its limits are in
  [softr-mcp.md → Softr Database tools](softr-mcp.md#softr-database-tools). Leave voided rows out
  with an `IS_NOT true` filter, and for a handful of rows read them with `database_search_records`
  and add them up.

## Testing edges on purpose

The happy path passed everywhere. The real bugs were on these edges, and several checks passed
without reaching the step they asserted (QA pass, 2026-10-08). The mechanics for the
first five are in [browser-checks.md → Forcing states](browser-checks.md#forcing-states).

- **A fake clock**: month end, year end, a clock change.
- **Held saves and double taps** ([step 7](browser-checks.md#7-click-then-read-what-it-sent)).
- **A save that succeeds, walked without writing**: the form refilled, the toast and where focus
  lands, the payload a void sends ([Walk a successful
  save](browser-checks.md#walk-a-successful-save-without-writing)). Focus is recorded over time, not
  read once ([step 4](browser-checks.md#4-measuring-with-eval)).
- **The record changing under an open form**: change one field in the form, change another field of the same record from a second session (or through a mocked read), then bring the first tab back so the hooks refetch ([Forcing states](browser-checks.md#forcing-states)). The untouched field should take the new value, the typed one should stay, and Save should send only the typed one ([A form open while its record changes](common-patterns.md#a-form-open-while-its-record-changes)).
- **Partial and total read failures**, then every Try again and every section after it.
- **Served reads** for empty-like values: `null`, `''`, `0`, and the field missing. A blank number
  is not zero: `Number(null)` and `Number("")` are both 0, and a partner with no monthly allocation
  showed 0.
- **Detail pages with no id, and with an id that does not exist.** One page said "Partner not
  found"; another opened an editable "Unnamed volunteer" that accepted Log hours; a third offered
  Try again forever.
- **Keyboard number entry.** `fill` cannot enter unreadable text, so type quantities with the
  keyboard, in Firefox as well, and probe with `5e`. What goes wrong and how to refuse it is in
  [ui-ux-guidelines.md §11](../ui-ux-guidelines.md#number-inputs).
- **Retry after an edit**, and **leaving mid-save**
  ([step 7](browser-checks.md#7-click-then-read-what-it-sent)).
- **Reusing the form after a save, without a reload.** A form filled by an effect keyed on query
  data was not refilled when the re-read returned the same data.
- **A void that leaves rows of zeros** in a per-entity totals table: a report built from ledger
  links includes entities whose rows all net to zero.
- **Logged out** and **roles**: the two sections above.

Two rules for every one of these:

- **Pick test values where the old and the new behaviour give different results, and that do not
  collide with seed data.** A size at 2,180 on hand is Low at a default of 2,500 but not at 2,000, so
  the check proves the setting was read. A five-digit test phone number collided with a seed family
  and opened the duplicate panel.
- **A negative check must reach the step it asserts.** Prove it got there: the request was or was not
  sent, the guard's message showed. `ab click` on a disabled calendar day prints "Done" and does
  nothing, so a refused day is proven by its disabled state, not by the click.

## Proving a fix before and after

A fix that passes against a friendly stub can fail live, and a check that cannot fail on the old
code proves nothing. Prove each fix with a figure or a failing-then-passing check.

### A local harness

React 18.2 in a shadow root with Tailwind v4, the block file bundled exactly as it is, fake data
seeded from live rows. Run the same test on the deployed version (it must fail) and on the fix (it
must pass): a date fix showed 18 failures on the deployed copy and none after.

- **Match the block's real width.** Either a fake sidebar of the measured width at the real window
  size, or no sidebar and a viewport narrowed to the block's measured width (985px copied one app's
  1280 window). Key a table-or-stack switch on the content's own `@container`, and confirm the
  container-query branches in the real app, since a harness at the wrong width picks the wrong one.
- **Copy Softr's `scroll-behavior: smooth` on `html`.** Without it, block code that scrolls and then
  measures passes in the harness and fails live (a calendar landed outside a landscape phone's
  strip). Put any tab-bar stand-in in the light DOM at document level, as Softr's is.
- **Load the real table rows.** With them the harness matched the live column widths to the pixel,
  and a column min-width fix that sounded right pushed every row button out of its card at 1280
  until it was measured on the real rows. MCP records keyed by field id load into the harness as
  they are.
- **Honest stubs:**
  - blanks as `''` and as `null` (real blanks arrive both ways);
  - a link field sometimes a single `{id, label}` object, not an array;
  - `where` honoured, with a switch to ignore it: that proves the client-side filter still shows
    the right rows if the server ignores `where`;
  - `onError` called when a write rejects (a stub that ignores it hides the deployed block's error
    toasts, and "no toast" is then an artifact);
  - no list refresh after a write, and a re-read with the same rows returns the same `data`
    object (otherwise a reset and a refetch land in one render and mask a refill bug);
  - switches to fail the Nth write and to add per-table delays, and `root.unmount()` exposed so a
    test can leave mid-save.
- **Clear `sessionStorage` between tests that share a tab.** A draft feature leaked between tests
  and turned two unrelated date tests red.
- **No browser needed for focus and hook logic: render the block's own code in jsdom.** To prove a
  focus fix or a hook before and after, without the live app, bundle the block's module-scope
  components and hooks with `esbuild` (`jsx: "automatic"`, and a stub plugin for the platform
  imports: the `@/…` paths, `sonner` and `lucide-react`). Render them with real React 18.2, `jsdom`
  and `date-fns`, and drive them with a mock data function. Run the same sequence on the pre-fix
  and the post-fix file. In one case focus fell to `<body>` while a retry ran and after it
  succeeded; after the fix it stayed on the action button. A hook that gates on read status is
  covered the same way, with stubbed reads for pending, partly loaded, refetching, error and
  success. Build the stub's export list from the file's `^import` lines (the `m` flag) and check
  that each name is an identifier, because comments in a shared kit hold text such as
  `import { … } from` that breaks the stub. This covers components and hooks; "Test pure logic in
  node", below, covers logic outside React. jsdom does not reproduce Safari or Firefox focus, so it
  proves the logic and the engine check in [Which engine ran](#which-engine-ran) still applies.

### A check that can fail

- **A check proves something only if it fails on the pre-fix bundle.** Run it there and report both
  results (3 of 11 checks passed on the base, 11 of 11 on the fix).
- **Rebuild the bundle after every edit**, stubs included. A printout-against-screen check passed
  on a stale bundle because both sides were stale.
- **Run the full suite before you quote counts.** A filtered run overwrote a results file with one
  test.
- **Treat older suites as a no-new-fails baseline.** They fail for stale reasons (a button that is
  gone, a removed default, changed copy): count fails against the previous baseline, not against zero.
- **Make every lookup require its match** ([browser-checks.md → step
  4](browser-checks.md#4-measuring-with-eval)).
- **Diff the page's text before and after, against a whitelist of the intended lines.** It catches
  copy changes nobody meant.
- **Test pure logic in node.** Logic moved out of `Block()` can be compared with the old function
  over thousands of generated inputs in several time zones (3,007 date ranges in three zones), and a
  multi-source block renders to HTML with a `useRecords` stub keyed on `from`. Cut the logic out
  between marker comments and run it with `esbuild` and `vm`, so the test runs the shipped code and
  not a copy.
- **Check `uptime` before blaming a timing test.** A load average of 111 broke a 400 ms check that
  passed alone.

### Which engine ran

- **Report the engine that actually ran each check.** A harness launcher quietly ran Chromium when
  asked for WebKit, and one Firefox build would not launch, so cross-engine claims were Chromium-only.
- **Test focus and number entry in Firefox as well as Chromium.** Safari and macOS Firefox do not
  focus a clicked button, so code that returns focus to "the button that opened this" must be handed
  that button; number fields differ by engine and by the Mac's region
  ([Testing edges](#testing-edges-on-purpose)).
- **For WebKit without a download**, a small Swift `WKWebView` runner can load the harness page; it
  found a WebKit-only scroll bug.
- **Give each parallel harness its own port.** A shared fixed-port Firefox wrapper killed other
  agents' runs.
- **Firefox quirk:** it reports a `console.error` of an error object as just "Error".

## Live write pass with a read-only checker

Some fixes can be proven only by a real save. Run a write pass only then, and only with the app
owner's go-ahead: the preview writes live data. On 2026-10-08 it ran after the owner said yes.

- **Use clearly marked test data**, and keep a manifest of record ids per table so that it can be
  purged before go-live.
- **A test row must not create a user.** If a table is synced as the app's users table, a row with an
  email creates an app user (and an invite, if the sync sends one). Test rows carry no email;
  compare `application_list_users` before and after (the same users, no "QA" match).
- **Prove every save by reading it back through the MCP.** Do not rely on the logged response: an
  aborted save has none, and one write-pass run showed no response body for a save. The request log
  still shows the payload (`postData`) ([browser-checks.md → step
  7](browser-checks.md#7-click-then-read-what-it-sent)).
- **With several agents writing, verify through your own rows and the links they carry**, not the
  shared totals. A product's total moved by an unrelated −50 while the pass ran; other agents' rows
  are the ones entered after your start time.
- **Put residue in the manifest.** Saving a setting and putting it back restores the value but not
  `updated_by`, which stays on the editor.
- **Run a separate read-only checker afterwards** that recomputes the figures and the counts
  ([Never writing by accident](#never-writing-by-accident),
  [Checking numbers](#checking-numbers-against-the-database)). It also does three things the
  agents' reports cannot:
  - **It reads the agents' screenshots.** Two polish findings, a label wrapped onto a second line
    and a panel left under the form after a save, showed only in the pictures and were in neither
    agent's report. Hand it the screenshot folder, and have it open the shots of every state the
    agents changed.
  - **It proves that no block was pushed during the pass.** The newest version's `createdAt` must be
    earlier than the first save, both in UTC. One `vibe_coding_block_list_versions` call with
    `includeCode: false` and `limit: 1` per block is far smaller than reading the block
    ([softr-mcp.md → Which read to use](softr-mcp.md#vibe-coding-block-tools)).
  - **It splits the changed existing records into edited and links only.** When a new row links to a
    record, Softr updates the record's inverse link list, and its `updatedAt` moves though nobody
    edited it (two records in the second round's pass). List those as "links only" in the manifest,
    after checking field by field that nothing else changed.
- **Re-check live after publishing:** the [logged-out checks](#logged-out) again, every block's
  deployed hash against your copy, and the checker's figures once more.

## Running QA with several agents and skeptics

- **Split agents by job, not by page.** Our lenses were front desk at the door, warehouse stock,
  partner agencies, volunteer coordination, and reports and settings, plus one for the "same number
  on every page" and one for roles. A person doing one job crosses several pages, and that is
  where the bugs hide.
- **Tell every agent what is already known and decided**, with a link to the decision log, and
  which items are deferred on purpose. Otherwise they re-report settled behaviour: a live check that
  did not know a shared-component change had been rejected listed it as a failure on 11 blocks, and
  the repair agents then synced the rejected change into every one of them.
- **A skeptic re-runs and recomputes each finding** and drops what does not reproduce.
- **A gap agent goes last.** It looks for what nobody checked (pages, controls, sizes, roles, month
  and year ends, empty and failed states) and checks those itself.
- **Only the orchestrator edits shared documents** (the app map, the decision log, the task list),
  and the prompt says so. Check anyway: one agent edited the app map despite the instruction.
  Project memory reaches subagents too: after "log QA lessons in this file" was saved as a memory,
  agents appended to it themselves, and two agents writing one file at once can lose an edit. Say
  in the prompt whether agents may write to it.
- **Give agents an absolute scratch folder** for screenshots and scratch files: eight PNGs landed in
  the project root, an agent's working directory.
- **Verify an agent's claim before you act on it.** Two agents reported the page and block ids
  swapped in the app map; the map was correct.
- **For parallel work**, give each agent its own browser session and harness port, and pinned
  copies of files another agent may be editing. Another session may be working on the same app: on
  2026-10-08 a second session pushed fixes to five blocks and published the app while the pass ran,
  so scratch copies went stale. Compare the deployed hash with your copy right before editing and
  right before pushing, and start from the project's mirror, not a scratch copy.
- **A reviewer re-reads the deployed hash, regenerates the diff, reruns the harness and checks that
  the tests a report cites exist.** One review cited a test that was not on disk.
- **A reviewer also reads the code against the written decision.** Hash checks, replays and gates
  cannot catch a build that departs from what was decided. In one build a control meant to stay
  visible while its read loaded was hidden, and the code comment admitted it; a verify pass found
  it. A control that keeps a repair reachable fails open: shown unless the read has settled (status
  success and no next page) and the row is known to be fine. Test pending, partly loaded,
  refetching, error and success, in the jsdom harness above. The rule is in
  [ui-ux-guidelines.md §12](../ui-ux-guidelines.md#12-loading-states).
- **Compare paired fixes side by side.** When one rule lands in several places, check where each block
  shows it, not only how it counts (two reports named the requests not yet fulfilled, Home did
  not). Diff a shared paragraph word for word before you push, because separate editors'
  sentences drift apart. Compare paired dialogs on first focus, close button, button colour and
  where the error shows, and grep every other reader of a field whose label changed.
- **After the per-block reviews, run one cross-block contract check.** Two blocks can each pass
  their own review and still disagree. One reviewer reads each pair of blocks that share a
  contract: the setting keys and how each side parses them (range and fallback), status strings,
  query parameters such as `?month=`, and shared aliases. In one build a block told staff that a
  setting takes 1 to 36 with a fallback of 8, while the block that read it accepted 1 to 999. The
  side-by-side rule above covers one rule landing in several places; this covers blocks that were
  not edited together.
- **Let a different agent, ideally a different model, check what one agent built.**
- **A per-block pipeline** that held: author, two reviews, fixes, a hash-verified push (a large plan is cut by
  one tested script: [softr-mcp.md → Which edit tool](softr-mcp.md#which-edit-tool-full-replace-vs-targeted-search-replace)),
  action permissions re-applied and read back (a push resets them), a browser check at the sizes in
  [browser-checks.md → step 4](browser-checks.md#4-measuring-with-eval) with saves blocked, and a
  live write pass only where one is approved. A stage with nothing to do returns a placeholder
  string, never `null`: a `null` drops the item from every later stage. One block needed no edit or
  review, so its review stage returned `null` and it never got its sync (QA pass, 2026-10-08).
  **Gate each stage on the evidence of the one before it.** A verify stage needs a non-empty pushed
  sha, so before dispatching one, compare the mirror's and the base copy's sha with the push plan's
  target sha: if the mirror still has the base sha and not the target, nothing is confirmed pushed
  (the mirror moves last, so a push that landed but whose mirror move did not run looks the same),
  so read the live `sourceSha256` with `includeCode: false` before deciding. **Stop
  on a repeated access error.** When two stages report the same one (NOT_FOUND or FORBIDDEN on the
  app or its database, say), hand it to the person instead of looping: a repair stage cannot fix a
  login. A connector signed in to another Softr account fails exactly this way, and subagents
  inherit that login. In one push of seven blocks, the ship, repair and verify stages of four of
  them each reported the same NOT_FOUND.

## Say what did not run

Wherever a push or a pass is reported (the ship report, a doc update, the hand-off message), say
which checks ran and which did not. A build can be gated, replayed and reviewed and never have been
opened in a browser, and a report that says only "pushed" is read as "tested". Name each check
that is still open (the browser pass at the sizes, a live write pass, the logged-out probe of a
page that is not public yet, the re-check after a publish) and what blocks it. If a pass was
stopped early, say where it stopped.

Why: after one 18-block push the browser QA was stopped, and the owner opened the app before any
live check had run, apart from one targeted privacy probe (2026-10-15).

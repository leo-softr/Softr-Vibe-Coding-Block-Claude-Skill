# QA of a Softr Vibe Coding app

How to QA an app made of Vibe Coding blocks, end to end, in the order to run it. This file is the
procedure and the reasons behind it. The mechanics are linked, not repeated: the browser commands
are in [browser-checks.md](browser-checks.md), the MCP in [softr-mcp.md](softr-mcp.md) and the data
shapes in [datasources/](../datasources/overview.md).

**Verified 2026-10-08.** Written from one end-to-end QA pass of a 15-block back-office app on Softr
Database (LCDB QA pass): 68 findings, two rounds of fixes and a live write pass. Each rule below
cost someone a wrong result first.

## When to use it

When an app's blocks are built and pushed (each push has passed the hash check in
[softr-mcp.md → Verifying a push](softr-mcp.md#verifying-a-push--the-deployed-source-is-the-only-proof)),
before the client relies on it, and again after each round of fixes. For a quick look at one
block, [browser-checks.md](browser-checks.md) is enough.

## The order of a pass

1. [Set-up](#set-up): which app to test, with which build, in which zone.
2. [Never writing by accident](#never-writing-by-accident): the guard first, the proof last.
3. [Roles](#roles): each page as each kind of user.
4. [Logged out](#logged-out): access from outside the browser.
5. [Measuring](#measuring): sizes, and numbers instead of looks.
6. [Checking numbers against the database](#checking-numbers-against-the-database).
7. [Testing edges on purpose](#testing-edges-on-purpose): failures, clocks, odd values.
8. [Proving a fix before and after](#proving-a-fix-before-and-after).
9. [Live write pass with a read-only checker](#live-write-pass-with-a-read-only-checker), only when
   a fix needs a real save.
10. [Running QA with several agents and skeptics](#running-qa-with-several-agents-and-skeptics).

## Set-up

- **Check changes in the preview (the draft), not the live app.** A push reaches the draft, and the
  live app changes only when someone publishes. Only two things run on the published app: the
  [logged-out checks](#logged-out) and the re-check after a publish.
- **Mint a fresh preview link for each session and after every push** (`application_preview`). The
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

Why: agents judged fixes on stale builds, shared one browser session across parallel agents and
logged times in the wrong zone (LCDB QA pass, 2026-10-08).

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
  rely on either to show "nothing unlisted" (LCDB write pass checker, 2026-10-08).
- **A race you cannot reproduce live with writes blocked stays in the local harness**, and the
  report says so. "A second row still saving" is one: the first write fails at once, so the second
  is never reached.
- To put a state on screen without changing data, see [Forcing
  states](browser-checks.md#forcing-states).

## Roles

Role bugs were found only when a pass compared roles side by side: hints that pointed users to pages
they could not open, admin pages that opened blank for volunteers, and an update action with no
record condition (LCDB QA pass, 2026-10-08).

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
- **If sign-up is meant to be off**, `/sign-up` returns 404, and on `/login` the public
  `window.application_context` shows `signUpSettings.policy` as `DISABLED` (a read-only check).
- **Never POST to a `records-trigger` URL to test a write endpoint.** If the action is open, it
  writes. Read the block's action permissions through the MCP instead (a push puts them back to
  Softr's defaults: [softr-mcp.md](softr-mcp.md#verifying-a-push--the-deployed-source-is-the-only-proof)).

## Measuring

Measure, do not eyeball. The rules are in
[browser-checks.md → step 4](browser-checks.md#4-measuring-with-eval): prove the console capture on
every load, numbers for heights and scroll widths, an error inside its dialog's edges, a shadow root
without `innerText`, and the sizes to check, which include the width a block really gets beside a
sidebar.

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
  rows, not visits, with voided rows included.
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
- **Name the figure you now expect after each fix** (for example "442 → 396"), so the fixer and the
  final cross-check prove the fix with a number.
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
without reaching the step they asserted (LCDB QA pass, 2026-10-08). The mechanics for the
first four are in [browser-checks.md → Forcing states](browser-checks.md#forcing-states).

- **A fake clock**: month end, year end, a clock change.
- **Held saves and double taps** ([step 7](browser-checks.md#7-click-then-read-what-it-sent)).
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
  [Checking numbers](#checking-numbers-against-the-database)).
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
- **Compare paired fixes side by side.** When one rule lands in several places, check where each block
  shows it, not only how it counts (two reports named the requests not yet fulfilled, Home did
  not). Diff a shared paragraph word for word before you push, because separate editors'
  sentences drift apart. Compare paired dialogs on first focus, close button, button colour and
  where the error shows, and grep every other reader of a field whose label changed.
- **Let a different agent, ideally a different model, check what one agent built.**
- **A per-block pipeline** that held: author, two reviews, fixes, a hash-verified push, action
  permissions re-applied and read back (a push resets them), a browser check at the sizes in
  [browser-checks.md → step 4](browser-checks.md#4-measuring-with-eval) with saves blocked, and a
  live write pass only where one is approved.

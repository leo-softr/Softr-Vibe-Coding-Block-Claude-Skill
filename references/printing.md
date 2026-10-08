# Printing from a block — a window of its own

**Print opens a new window (or tab) holding its own printout document. Always.** Never
`window.print()` on the Softr page, and never an in-page "print view". This is the default for
every Print, "printable version" or save-as-PDF control in a block, whatever the data source.
Leo, 2026-09-30: "I don't want this print view, it needs a new tab opening", and as the default,
"so it doesn't create a weird UI".

A block is page *content*, rendered inside a shadow root, and that rules out both of the obvious
ways to print:

| Option | What ends up on paper |
|---|---|
| `window.print()` from the block | The whole Softr page: the app header, the footer, every sibling block, and the block's own buttons and filters. The block's CSS lives in its shadow root and cannot reach any of the rest. Hiding it takes global Custom Code CSS aimed at Softr's page structure, which you do not control ([native-chrome-styling.md](native-chrome-styling.md)), plus print CSS inside the block for its own controls: two stylesheets in two places. |
| An in-page "print view" (the block switches itself to a print layout) | A second screen of the block, still under the app chrome, with its own "Print again" / "Exit print view" buttons: a mode the user has to find their way out of. It still prints through `window.print()`, so it inherits the whole row above. Leo rejected it by name. |
| A new window holding its own document (this page) | The printout and nothing else. No chrome to hide, no print CSS, no siblings, and the same from any page. The one cost is a pop-up, and the click itself gets it past the blocker. |

Four parts make it work: a **builder** that turns the view into one HTML string (1), a **click**
that opens the window and writes the string into it (2), a **wait** so it prints only once fonts
and images are in (3), and a **Print button that waits for the data** (4). Printing from *another*
page adds the `?print=1` deep link (5). Then the paper layout (6), and gotchas and testing (7).

**Verified live 2026-09-30** in a Softr preview: the button opens a separate window holding only
the printout (no app header or footer, no controls), photos load before print fires, and the page
behind it is untouched; a `?print=1` link opens a window that shows "Preparing the printout…" and
then becomes the same printout; every table cell measured 0px off its row's middle. (The snippets
are modern TS, per SKILL.md's Style Conventions, generalised from the var-style original that was
verified.)

## 1. The builder: one HTML string

The printout is a complete HTML document, built as one string by module-scope functions. Three
rules make it safe and self-sufficient.

**Escape every interpolated value, text and attribute values alike.** The window that
`window.open("")` returns is an `about:blank` page on the app's own origin, and a `?print=1`
printout (section 5) *is* the app's page. Record text written in unescaped is markup: an
`<img onerror=…>` in a vendor name runs as the signed-in user. Escape all five characters, `&`
first. The builder's attributes are single-quoted (`src='…'`), so `'` is not optional:

```tsx
function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replace(/&/g, "&amp;") // first, or it re-escapes the four below
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
```

Then every `${…}` in the builder is one of three things: `escapeHtml(…)`, a number the code
computed, or a fragment built only from those two and literals (`printCellHtml(…)`, `colgroup`,
`headRow`, `PRINT_STYLES`). Nothing else.

**Bring your own styles and fonts.** The new document starts empty. Tailwind, shadcn, the lucide
React icons, the app's fonts and the Custom Code header CSS all stay behind in the app, so a class
like `text-sm` means nothing there. Write plain CSS into the printout's own `<style>`, load the
brand font with its own `<link>` (DESIGN.md's Font URLs), and draw anything iconic as text or an
inline SVG string.

**The `<title>` is the PDF's file name.** "Save as PDF" names the file after it, so give it the
context as well as the view: `Project name — List name`, not `Print`.

```tsx
/* One cell on paper: the label the row shows ON SCREEN for that column (formatted dates, "—" for
   empty), as escaped HTML. The name cell carries the photo at 24px, or an empty square of the
   same size where there is none, so the names keep one straight edge. Adapt to your row shape. */
type PrintRow = { name: string; photoUrl: string; labels: Record<string, string> };

function printCellHtml(row: PrintRow, key: string): string {
  if (key === "name") {
    const photo = row.photoUrl
      ? `<img class='ph' src='${escapeHtml(row.photoUrl)}' alt=''>`
      : "<span class='ph none'></span>";
    return `<span class='item'>${photo}<span>${escapeHtml(row.name)}</span></span>`;
  }
  return escapeHtml(row.labels[key] || "—");
}

/* Plain CSS for a document with no Tailwind in it. Black text on white prints best; put the
   brand colour (DESIGN.md) on the eyebrow and the heading only. Section 6 explains each rule. */
const PRINT_STYLES = [
  "body{font:12px Inter,Helvetica,Arial,sans-serif;color:#000;margin:24px}",
  ".eyebrow{font-size:13px;font-weight:600;letter-spacing:0.75px;text-transform:uppercase;color:#111;margin:0 0 4px}",
  "h1{font-size:18px;font-weight:600;color:#111;margin:0 0 2px}",
  ".meta{font-size:11px;color:#333;margin:0 0 2px}",
  ".meta.note{font-weight:600}",
  ".grp{font-size:12px;font-weight:700;margin:14px 0 4px}",
  "table{width:100%;table-layout:fixed;border-collapse:collapse;font-size:11px}",
  "th{text-align:left;border-bottom:1px solid #DDD;padding:3px 4px;overflow-wrap:anywhere}",
  "td{text-align:left;border-bottom:1px solid #DDD;padding:3px 4px;vertical-align:middle;overflow-wrap:anywhere}",
  "tbody tr{break-inside:avoid}",
  ".item{display:flex;align-items:center;gap:6px}",
  ".ph{display:inline-block;flex:none;width:24px;height:24px;object-fit:cover;border:1px solid #DDD}",
  ".ph.none{background:#F2F2F2;-webkit-print-color-adjust:exact;print-color-adjust:exact}",
  ".chk{text-align:center}",
  ".box{display:block;margin:0 auto;width:12px;height:12px;border:1px solid #000}",
  ".notes{margin-top:18px;break-inside:avoid}",
  ".notes-body{white-space:pre-wrap;font-size:12px}",
  "@page{margin:14mm}",
].join("");

type PrintColumn = { key: string; label: string };
type PrintContext = {
  title: string; // the <title>: what "Save as PDF" names the file
  eyebrow: string; // the context above the heading (the project, the client), or ""
  heading: string;
  meta: string[]; // plain-text lines under the heading, the print date first
  filterNote: string; // "Filtered view — 12 of 40 items" while a search or filter is on, else ""
  columns: PrintColumn[]; // the columns on show, in their on-screen order
  widths: Record<string, number>; // on-screen widths by key; only the proportions matter
  groups: { name: string; rows: PrintRow[] }[]; // one table per group; name "" when ungrouped
  tickBox: boolean; // a title-less ☐ column at the end, to tick on paper
  notes: string;
  emptyText: string;
};

function buildPrintHtml(ctx: PrintContext): string {
  const cols = ctx.columns;
  const tick = ctx.tickBox ? 6 : 0; // the ☐ column's share of the width, in %
  const total = cols.reduce((sum, c) => sum + (ctx.widths[c.key] || 100), 0);
  const pct = (key: string) => (((ctx.widths[key] || 100) / total) * (100 - tick)).toFixed(2);
  /* ONE <colgroup>, shared by every group's table. With table-layout:fixed, that is what lines
     the columns up from one group to the next (section 6). */
  const colgroup =
    "<colgroup>" +
    cols.map((c) => `<col style='width:${pct(c.key)}%'>`).join("") +
    (tick ? `<col style='width:${tick}%'>` : "") +
    "</colgroup>";
  const headRow =
    "<tr>" +
    cols.map((c) => `<th>${escapeHtml(c.label)}</th>`).join("") +
    (tick ? "<th aria-label='Done'></th>" : "") + // no title over the tick boxes
    "</tr>";

  const out: string[] = [];
  out.push("<!doctype html><html><head><meta charset='utf-8'>");
  out.push(`<title>${escapeHtml(ctx.title)}</title>`);
  out.push(
    "<link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap'>"
  );
  out.push(`<style>${PRINT_STYLES}</style></head><body>`);
  if (ctx.eyebrow) out.push(`<p class='eyebrow'>${escapeHtml(ctx.eyebrow)}</p>`);
  out.push(`<h1>${escapeHtml(ctx.heading)}</h1>`);
  ctx.meta.forEach((line) => out.push(`<p class='meta'>${escapeHtml(line)}</p>`));
  if (ctx.filterNote) out.push(`<p class='meta note'>${escapeHtml(ctx.filterNote)}</p>`);

  ctx.groups.forEach((group) => {
    if (group.name) {
      out.push(`<div class='grp'>${escapeHtml(group.name)} &middot; ${group.rows.length}</div>`);
    }
    out.push(`<table>${colgroup}<thead>${headRow}</thead><tbody>`);
    group.rows.forEach((row) => {
      out.push(
        "<tr>" +
          cols.map((c) => `<td>${printCellHtml(row, c.key)}</td>`).join("") +
          (tick ? "<td class='chk'><span class='box'></span></td>" : "") +
          "</tr>"
      );
    });
    out.push("</tbody></table>");
  });
  if (ctx.groups.length === 0) out.push(`<p class='meta'>${escapeHtml(ctx.emptyText)}</p>`);

  if (ctx.notes) {
    out.push(
      `<div class='notes'><div class='grp'>Notes</div><div class='notes-body'>${escapeHtml(ctx.notes)}</div></div>`
    );
  }
  out.push("</body></html>");
  return out.join("");
}
```

**What goes on paper: the view as it stands.** Build the context inside `Block()` from the same
derived values the screen renders (the columns on show, in their order, hidden ones left out; the
same groups, sort and filters), so paper and screen cannot disagree. Two meta lines earn their
place: the date, because a sheet outlives the day it was printed, and a line that says so when a
search or filter is on. (A printout that is a different document by design, such as a packing slip
or an invoice, builds its own content, but keeps every other rule on this page.)

```tsx
/* Inside Block(), next to the values it reads. */
function printContext(): PrintContext {
  return {
    title: `${projectName} — ${listName}`,
    eyebrow: projectName,
    heading: listName,
    meta: ["Printed " + format(new Date(), "MMM d, yyyy")],
    filterNote: hasActiveFilter ? `Filtered view — ${shownRows.length} of ${rows.length} items` : "",
    columns: visibleColumns,
    widths: columnWidths,
    groups: groups, // the grouped, sorted, filtered rows the table renders, as PrintRow
    tickBox: true,
    notes: notes.trim(),
    emptyText: rows.length === 0 ? "Nothing on this list yet." : "No items match this filter.",
  };
}
```

## 2. Open it from the click

```tsx
function handlePrint() {
  // FIRST, and synchronously: the click's user activation is what gets the window past the
  // pop-up blocker. No await, .then() or setTimeout in front of this line.
  const win = window.open("", "_blank", "width=900,height=700");
  if (!win) {
    toast.error("Your browser blocked the print window. Allow pop-ups for this site and try again.");
    return;
  }
  writePrintout(win, buildPrintHtml(printContext()));
}
```

- **Nothing asynchronous before `window.open`.** A browser lets a page open a window only while
  the user's click is fresh. An `await` (fetching the data on click, say), a `.then()` or a
  `setTimeout` in front of it spends that allowance, and the window is blocked some of the time,
  in some browsers: the worst kind of bug to chase. Section 4 makes sure the data is already there
  when the button can be pressed, so there is nothing to wait for.
- **`null` means blocked.** Say how to fix it (the toast above) instead of failing silently.
- **No `noopener` or `noreferrer` in the features.** With either one, `window.open` returns `null`
  even though the window opened: there is no handle to write the printout into, and the code reads
  the `null` as "blocked".
- **`width` / `height` make it a pop-up window.** A features string like the one above makes
  Chromium and Firefox open a separate window at that size; with no features string it is a new
  tab. Either meets the rule. Pick one and make every Print in the app the same call, so every
  Print behaves the same; nothing but discipline keeps two blocks alike (SKILL.md Hard
  Constraint 22).
- **The block that has the data writes the printout itself.** Do not route its own button through
  `?print=1` (section 5): that reloads the whole app and every query in the new window to print
  data this page already holds.

## 3. Print only when it is ready

```tsx
/* Writes the printout into `win` and prints it once it is ready. `win` is a window of its own or,
   for a ?print=1 open (section 5), this very window, whose page the printout then replaces.
   Ready means the font stylesheets and every image have loaded or failed, and then the web fonts
   are in: a print fired earlier comes out with empty squares where the photos go, or in the
   fallback font. It never waits more than 4s, then gives the layout a 250ms beat, because some
   browsers otherwise print a blank first page. */
function writePrintout(win: Window, html: string) {
  win.document.open();
  win.document.write(html);
  win.document.close();
  win.focus();

  let fired = false;
  const fire = () => {
    if (fired || win.closed) return;
    fired = true;
    window.setTimeout(() => {
      if (!win.closed) win.print();
    }, 250);
  };
  window.setTimeout(fire, 4000); // the cap: one slow or hung request never holds the print hostage

  const settled = (el: HTMLElement) =>
    new Promise((resolve) => {
      el.addEventListener("load", resolve);
      el.addEventListener("error", resolve); // a failed image or stylesheet must not hold it either
    });
  const waits: Promise<unknown>[] = [];
  // The stylesheets too: document.fonts.ready does not wait for a font stylesheet still in flight.
  win.document.querySelectorAll<HTMLLinkElement>("link[rel='stylesheet']").forEach((link) => {
    if (!link.sheet) waits.push(settled(link));
  });
  Array.from(win.document.images).forEach((img) => {
    if (!img.complete) waits.push(settled(img));
  });
  Promise.all(waits)
    .then(() => win.document.fonts?.ready) // with the stylesheets in, this covers the font files
    .then(fire, fire);
}
```

- **Stylesheets and images first, then the fonts.** Those are what go missing on paper. The
  stylesheet wait matters because `document.fonts.ready` only counts the fonts the document
  already knows it needs. Measured in Chromium on 2026-09-30: with a font stylesheet taking 1.5s,
  `fonts.ready` resolved at once and the print fired at 255ms; waiting for the `<link>` first held
  the print until the font file had arrived. (The live-verified deployment waited on `fonts.ready`
  and the images only. Photos usually arrive after the stylesheet, which hides the gap; without
  photos, the brand font can miss the paper.)
- **`fired` makes it print once**, whichever comes first: the cap or the waits.
- **Guard `win.closed`.** The user can close the window during the wait.

## 4. The Print button waits for the data

A printout built before the data is in is a skeleton on paper, or worse, the first page of
records, which looks complete. Keep Print disabled until every query has succeeded **and every
page is fetched** (`hasNextPage` false on each; the auto-load-all effect in
[../datasources/reading.md](../datasources/reading.md#loading-all-records-auto-pagination) is what
gets it there), and say why on hover:

```tsx
const dataReady =
  itemsResult.status === "success" &&
  !itemsResult.hasNextPage &&
  vendorsResult.status === "success" &&
  !vendorsResult.hasNextPage;

<button
  type="button"
  onClick={handlePrint}
  disabled={!dataReady}
  title={dataReady ? "Opens the printout in a new window" : "Loading…"}
  className="inline-flex items-center gap-1.5 … disabled:cursor-wait disabled:opacity-60"
>
  <Printer className="h-4 w-4" />
  Print
</button>
```

If the printout reads anything else from state that arrives after the data, such as a saved
layout or view settings hydrated from a record, add its ready flag to the same condition
(`viewReady` in section 5).

## 5. Printing from another page: `?print=1`

A Print control on a page that does not hold the data (a card on an index page, say) needs the
target page to build the printout. But a page that has just loaded cannot open a window (there is
no user gesture, so the pop-up blocker stops it), and it must not `window.print()` itself (the
rule at the top). So the two pages split the work.

**The linking page opens the window, straight from the click**, pointed at the target page with a
flag:

```tsx
<a
  href={`/list?recordId=${encodeURIComponent(record.id)}&print=1`}
  onClick={(e) => {
    // A window of its own, the same call as every other Print. preventDefault ONLY when it
    // opened: if a pop-up blocker returns null, the link still works, in this tab.
    const win = window.open(e.currentTarget.href, "_blank", "width=900,height=700");
    if (win) e.preventDefault();
  }}
  className="…"
>
  <Printer className="h-3.5 w-3.5" />
  Print
</a>
```

A real `<a href>` rather than a button, so the fallback costs nothing and the URL is a real one.
Keep `noopener` out here too: `window.open` would return `null` although the window opened, the
handler would not `preventDefault`, and the tab would navigate as well, giving two printouts.

**The target block turns its own window into the printout.** It reads the flag once, shows a
one-line holding state instead of its UI, and, once the data and anything else the printout reads
are in, replaces its own document with the printout and prints:

```tsx
export default function Block() {
  // Read once, at mount.
  const [printOnLoad, setPrintOnLoad] = useState(() => {
    try {
      const p = new URLSearchParams(window.location.search).get("print");
      return p === "1" || p === "true";
    } catch (e) {
      return false;
    }
  });

  // … the data hooks, the auto-load-all effects, dataReady (section 4), anyQueryFailed (any of
  //   them in status "error"), and viewReady if a saved layout is hydrated into state (drop it
  //   from the effect below if there is none) …

  /* Runs once: printOnLoad goes false first, so a later refetch cannot print a second time.
     printContext is declared further down and reads values computed during the render; the
     effect runs after the render, by which time they are all set. */
  useEffect(() => {
    if (!printOnLoad || !dataReady || !viewReady) return;
    setPrintOnLoad(false);
    writePrintout(window, buildPrintHtml(printContext()));
  }, [printOnLoad, dataReady, viewReady]);

  // … every other hook: ALL of them above the holding return below (Hard Constraint 19) …

  if (printOnLoad) {
    // This window exists only to become the printout: a holding line, never the full UI.
    return (
      <div className="container py-0">
        <div className="content">
          <div className="px-8 pt-10 pb-12 text-sm text-muted-foreground">
            {anyQueryFailed
              ? "Couldn't load this to print it. Reload this window to try again."
              : "Preparing the printout…"}
          </div>
        </div>
      </div>
    );
  }

  // … the normal view …
}
```

- **The ready flags are the effect's dependencies.** It has to run again each time one of them
  flips; an empty dependency array runs it once, at mount, before any data exists.
- **A holding line, not the full UI.** Rendering the normal view meanwhile flashes the whole app
  (filters, buttons, a table filling in) for a second before it turns into paper.
- **`writePrintout(window, …)` replaces the Softr page in that window.** `document.open()` clears
  the app's DOM, header and footer included, and the printout is all that is left. Whatever React
  renders after that goes into a root that is no longer in the document.
- **The fallback.** If the linking page's pop-up was blocked, the link opened this URL in the
  user's own tab, and the printout replaces the app there. The link still works; it is just less
  graceful.

## 6. Layout on paper

The CSS in section 1 carries all of this; each rule is there for a reason.

- **One `<colgroup>`, shared by every group's table, with `table-layout: fixed`.** A grouped view
  prints as one table per group. With automatic layout each table sizes its columns to its own
  content, and the columns zig-zag from one group to the next. A fixed layout takes its widths
  from the `<col>` elements, and one shared `<colgroup>` gives every table the same ones.
  Percentages in proportion to the on-screen widths keep the paper recognisable as the screen.
- **`overflow-wrap: anywhere` on every cell**, so a long SKU or URL wraps inside its fixed column
  instead of running into the next one.
- **`vertical-align: middle` on every `td`.** A room or category that wraps to two lines otherwise
  leaves the one-line values in its row hanging from the top. (Verified: every cell 0px off its
  row's middle.)
- **A tick-box column is a bordered block, centred:** `.box{display:block;margin:0 auto;…}` in a
  `text-align:center` cell, under a title-less `<th>` that carries an `aria-label`. A block sits
  on no text line, so no line-height can nudge it off the middle; an inline box sits on the text
  baseline, and the line's descender space pushes it off-centre.
- **`tbody tr { break-inside: avoid }`**, so a row never splits across two pages. The same for the
  notes.
- **Backgrounds do not print by default.** Browsers drop background colours and images unless the
  user ticks "Background graphics". Where a background carries meaning (a placeholder square, a
  status fill), set `-webkit-print-color-adjust: exact; print-color-adjust: exact` on it, and draw
  photos as `<img>`, never as a CSS `background-image`.
- **Images at a fixed size with `object-fit: cover`**, and an empty square of the same size where
  a row has none, so the text beside them keeps one straight edge.
- **`@page { margin: 14mm }`** is the margin on paper; the `body` margin is for the window on
  screen.

## 7. Gotchas and testing

**Attachment URLs work as they are.** Softr Database attachment URLs are pre-signed links that
carry their auth in the query string, so the new window loads them with no cookie or header
(verified 2026-09-30); any file URL that needs no cookie behaves the same. They expire after a
couple of hours and are re-signed on every fetch, so build the printout from what the block has
just fetched, never from a URL saved earlier.

**Capture the window with `page.waitForEvent("popup")`** (Playwright). The printout is a popup of
the page that was clicked, for the Print button (`window.open("")`) and for a `?print=1` link on
another page (`window.open(href)`) alike:

```ts
const [popup] = await Promise.all([
  page.waitForEvent("popup"),
  page.getByRole("button", { name: /print/i }).click(),
]);

// Replace print() before it fires, so no dialog blocks the run and the test sees when it fired.
// For the Print button the document is already written by the time you hold the popup, and
// print() comes at least 250ms later.
await popup.evaluate(() => {
  window.print = () => {
    (window as any).__printedWithImages = Array.from(document.images).every((img) => img.complete);
  };
});
await expect
  .poll(() => popup.evaluate(() => (window as any).__printedWithImages), { timeout: 10_000 })
  .toBe(true); // the 4s cap plus the 250ms beat is too close to the 5s default

// A plain document: no shadow roots and no Softr chrome, so ordinary locators work.
await expect(popup.locator(".softr-topbar")).toHaveCount(0);
await expect(popup.locator("tbody tr")).toHaveCount(expectedRows);

// Each tick box's centre against its row's.
const offsets = await popup.evaluate(() =>
  Array.from(document.querySelectorAll("tbody tr")).map((tr) => {
    const row = tr.getBoundingClientRect();
    const box = tr.querySelector(".box")!.getBoundingClientRect();
    return Math.abs(box.top + box.height / 2 - (row.top + row.height / 2));
  })
);
expect(Math.max(...offsets)).toBeLessThan(1);
```

For a `?print=1` link, click the link instead. That window loads the Softr page first, so wait
for it to *become* the printout before asserting on it:
`await expect(popup).toHaveTitle("Project name — List name")`. Stub `print` there once the Softr
page has loaded (`await popup.waitForLoadState()`): `document.open()` keeps a `print` set on the
window before it (checked in Chromium, 2026-09-30). The printout has no print-only CSS, so the
window lays it out as the paper will; narrow it to about the paper's printable width (roughly
700px for A4 or Letter at 14mm margins) to see the wrapping the paper gets.

**Do not mock a popup printout's images or fonts with `route()`.** The Print button writes the
printout in the same task that opens the window, so its first requests go out before Playwright
has attached to the popup. With Playwright attached over CDP (seen 2026-09-30) they hang: no
`request` event, the route handler never runs, the images stay pending, and the print falls
through to the 4s cap, which looks exactly like a broken wait. Use real URLs or `data:` URLs in
the popup, or mock on a page that loaded normally (the `?print=1` path), where routing works.

**Preview links pin the app version they were minted on.** An `application_preview` link carries
`&version=<n>` in its URL and keeps serving that version, by design. After pushing a change, mint a
fresh preview link before you verify anything; otherwise you are testing the old Print. (What else a preview link is, and why
it is never shared: [softr-mcp.md](softr-mcp.md#application-management-tools).)

**Check a printout for overflow, not only for content.** A `white-space: nowrap` cell (a mono figure column) overflows its column silently when a label gets longer, and the page still prints. Measure `scrollWidth > clientWidth` on those cells in the printout (LCDB QA pass, 2026-10-08: longer month labels overflowed a column with no error). A date stamp in the printout is local time with its UTC offset ([common-patterns.md → CSV export](common-patterns.md#csv-export)). To capture the printout without a pop-up, see the Exports and printouts section of [browser-checks.md](browser-checks.md).

**A browser that is not painting does not run the page.** A hidden browser pane or a background
tab fires no `requestAnimationFrame` and no IntersectionObserver callbacks, so anything that waits
on them (a reveal-on-scroll, lazy content, a check timed off a frame) stalls there, and a check
fails for reasons that have nothing to do with your code. Verify in a visible window or a
headless browser.

## Checklist before shipping a Print control

- [ ] Print opens a window of its own: `window.open("", "_blank", …)`, first thing in the click
      handler, nothing asynchronous before it. No `window.print()` on the Softr page, no in-page
      print view
- [ ] `null` → a toast telling the user to allow pop-ups; no `noopener` / `noreferrer` in the
      features
- [ ] The same `window.open` features string as every other Print in the app
- [ ] Every interpolated value through `escapeHtml` (`& < > " '`, attribute values included)
- [ ] The printout carries its own `<style>` (no Tailwind classes), its fonts' `<link>`, a
      `<title>` with the context, and an `@page` margin
- [ ] It prints once the stylesheets, fonts and images are in (capped at ~4s), after a 250ms
      beat, with `win.closed` guarded
- [ ] Print is disabled until every query has succeeded and every page is fetched (and any saved
      layout is applied), with a `title` that says why
- [ ] Printing from another page: the linking page opens the window (`preventDefault` only when
      it opened); the target block shows "Preparing the printout…", then replaces its own
      document once the ready flags are set, once
- [ ] Paper: one shared `<colgroup>` + `table-layout: fixed`; `vertical-align: middle`;
      `break-inside: avoid` on rows; `print-color-adjust: exact` where a background must print;
      photos as fixed-size `<img>`
- [ ] Verified on a freshly minted preview link, with the window captured by
      `waitForEvent("popup")`

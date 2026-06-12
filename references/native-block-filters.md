# Dynamic Filters & Custom Controls on Native Softr Blocks

Softr's native **List / Grid** blocks support category chips and *static* filters, but they have **no dynamic date filter** ("show me records due between X and Y") and no way to add your own filter control to the block's chrome. You can add both with a **Custom Code Static block** — raw HTML/JS rendered in the **main document** (NOT a shadow-DOM Vibe Coding block) — that:

1. writes the user's choice into a **URL parameter** and reloads, while
2. the native block's own **Conditional Filter** reads that parameter via `{URL_PARAM:...}`, and (optionally)
3. the same script **relocates the control into the native block's filter row** so it looks built-in.

> **Sibling to [native-chrome-styling.md](native-chrome-styling.md).** That doc restyles Softr's *shell* (header/footer/nav) with global CSS. This one *drives and augments native blocks* with custom-code JS. Both reach the **main document**, never a block's shadow DOM — so this is a **Custom Code Static block**, not a Vibe Coding (JSX) block.

House code style still applies in the `<script>`: `var`, `function(){}`, **no** optional chaining (`?.`) or nullish coalescing (`??`).

---

## 1. The mechanism — steer a native filter with a URL param

The custom control never filters anything itself. It writes the user's selection into the URL and reloads; Softr's *own* conditional filter does the work.

**Wire the native block (Studio):** open the List/Grid block → **Conditional Filters** → add rules that reference a URL param instead of a static value. For a date range:

```
Due date  is on or after   {URL_PARAM:start_date}
Due date  is on or before  {URL_PARAM:end_date}
```

**The control (Custom Code Static block):** write the param + reload.

```html
<input id="startDate" type="date" />
<script>
  (function () {
    var input = document.getElementById("startDate");
    var url = new URL(window.location.href);
    if (url.searchParams.has("start_date")) input.value = url.searchParams.get("start_date");
    input.addEventListener("change", function () {
      url.searchParams.set("start_date", input.value);
      window.history.replaceState({}, "", url);
      window.location.reload();  // Softr re-reads {URL_PARAM:...} on load
    });
  })();
</script>
```

That's the whole steering loop: **control → URL param → native conditional filter.**

---

## 2. The empty-param trap → the wide-range sentinel ⚠️

**Softr treats an empty or missing `{URL_PARAM:x}` as "match NOTHING", not "ignore this filter."** So on first load with no params, a filtered list renders **empty** — the single most confusing symptom of this technique.

**Fix: seed a wide sentinel range that means "show all", and keep the inputs visually blank.** When the user clears the control, fall back to the sentinel instead of an empty value.

```js
var WIDE_START = "2000-01-01";
var WIDE_END = "2099-12-31";

var rawStart = url.searchParams.get("start_date");
var rawEnd = url.searchParams.get("end_date");

// Blank/first load → seed the wide range so EVERYTHING shows, then reload once.
// Falsy check (not .has) so an EMPTY param self-heals the same as a missing one.
if (!rawStart && !rawEnd) {
  url.searchParams.set("start_date", WIDE_START);
  url.searchParams.set("end_date", WIDE_END);
  window.history.replaceState({}, "", url);
  window.location.reload();
  return;
}

// Reflect only REAL user dates back into the inputs; hide the sentinels (inputs stay empty).
if (rawStart && rawStart !== WIDE_START) startInput.value = rawStart;
if (rawEnd && rawEnd !== WIDE_END) endInput.value = rawEnd;

// On apply, empty input → sentinel (so "no bound" still means "show all", not "show none").
function apply() {
  url.searchParams.set("start_date", startInput.value ? startInput.value : WIDE_START);
  url.searchParams.set("end_date", endInput.value ? endInput.value : WIDE_END);
  window.history.replaceState({}, "", url);
  window.location.reload();
}
```

---

## 3. Date filters need a `date_list` helper table

For **date** comparisons, Softr's conditional filter can only compare against dates that *exist as data*. Two patterns:

- **Direct range (simplest):** the `{URL_PARAM:start_date}` / `{URL_PARAM:end_date}` rules above compare against the record's own date field. No helper table needed if your "is on or after / before" comparator accepts a raw param value. (Works for List/Grid filtering by a record date.)
- **Bridge for charts/metrics/many blocks (AppGrape pattern):** to drive *many* blocks off one date without repeating URL-param rules, add a hidden **Item Details** block bound to a **`date_list`** table (one record per day), conditionally filtered to `Date is {URL_PARAM:selected_date}`. That exposes the chosen date as a page-level **Current Record**; every chart/metric then filters `Date is → Current Record > Date`. Hide the bridge block with page CSS (`#item-details1 { display:none !important; }`).

Either way, if you compare against `date_list`, it must hold **one record for every day** in range. Populate it **once** with an Airtable automation/Scripting script (one record per calendar day, batched 50/call, re-runnable via a dedupe read). See [airtable-automations.md](airtable-automations.md) for the script shape; field-ID discipline applies.

---

## 4. Injecting the control into the native block's filter row

A Custom Code block renders wherever you place it on the page — Softr gives no setting to drop it *inside* a list's filter bar. So after the page renders, the script finds the native filter row in the DOM and **re-parents** the control into it. Three hard-won rules:

### 4a. Scope to the block by `data-block-id` — never search page-wide
Every Softr block renders as `<section data-block-id="...">` (stable; read it off the block in DevTools). **Always scope DOM queries to that section.** A page-wide search will grab the wrong thing — e.g. matching filter buttons by the text "Client" also hits a **"Clients" link in the nav**, dropping your control into the sidebar.

### 4b. Find the filter row WITHOUT hashed classes
Softr's filter chips carry only **hashed build classes** (e.g. `a0e85ef_wsthdk3`) that change on every deploy — same rule as native-chrome-styling.md: don't anchor on them. Durable approach: match the filter **buttons by the label text you configured**, then take their **lowest common ancestor** = the filter row. Keep the hashed class as a fast fallback.

```js
var YOUR_BLOCK_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"; // the List/Grid block
// The filter labels YOU set on the block — content, not Softr hashes; survives deploys.
var FILTER_LABELS = ["Client", "Status", "Owner", "Region"]; // only need any 2 to still match

function lowestCommonAncestor(els) {
  if (!els.length) return null;
  var anc = els[0];
  for (var i = 1; i < els.length; i++) {
    while (anc && !anc.contains(els[i])) anc = anc.parentElement;
    if (!anc) return null;
  }
  return anc;
}

function findFilterRow() {
  var block = document.querySelector('[data-block-id="' + YOUR_BLOCK_ID + '"]');
  if (!block) return null;

  // PRIMARY (deploy-proof): the filter buttons by their label text → their shared container.
  var btns = block.querySelectorAll("button");
  var hits = [];
  for (var i = 0; i < btns.length; i++) {
    var t = (btns[i].textContent || "").replace(/\s+/g, " ").trim();
    for (var j = 0; j < FILTER_LABELS.length; j++) {
      if (t === FILTER_LABELS[j]) { hits.push(btns[i]); break; }
    }
  }
  if (hits.length >= 2) {
    var lca = lowestCommonAncestor(hits);
    if (lca && !lca.querySelector(".softr-list-container")) return lca; // guard: not too high
  }

  // FALLBACK (works today, may break on a Softr CSS rebuild): the hashed chip wrapper.
  var chip = block.querySelector(".a0e85ef_wsthdk3");
  if (chip && chip.parentElement) return chip.parentElement;
  return null;
}
```

### 4c. Survive re-renders — re-home on an interval ⚠️ (THE big one)
**Softr re-renders its List/Grid block on every data or filter change, and a re-render discards any node you injected into it.** A one-shot relocation works once, then the control **vanishes** the first time the user touches a native chip or the data refreshes. Don't relocate once — **re-home on a short interval** (or a `MutationObserver`) so the same node snaps back whenever Softr rebuilds the row.

```js
var wrap = document.getElementById("yourControlWrap");
var host = wrap ? (wrap.closest("section") || wrap.parentElement) : null;

function ensureHomed() {
  try {
    var row = findFilterRow();
    if (!row || !wrap) return;
    if (wrap.parentElement !== row) {        // only acts when knocked out → no loop
      wrap.style.marginLeft = "8px";
      row.appendChild(wrap);
    }
    // Collapse the now-empty Custom Code block — but NEVER hide the list itself.
    if (host && host.style.display !== "none" && !host.querySelector(".softr-list-container")) {
      host.style.display = "none";
    }
  } catch (err) { /* leave the control where it is on any error */ }
}

ensureHomed();                 // place ASAP
setInterval(ensureHomed, 500); // and re-home after every Softr re-render
```

`ensureHomed` is idempotent (it only re-appends when the control is *not* already in the row), so the interval is cheap and can't loop.

---

## 5. Full worked example — date-range picker that joins the filter row

A complete Custom Code Static block: range picker with the wide-range sentinel, "wait for both ends before reloading", a Clear button, relocation into the filter row, and re-render survival.

```html
<div id="duePickerWrap" style="display:inline-flex; align-items:center; gap:8px; font-family:inherit;">
  <label style="font-size:13px; font-weight:600;">Due between</label>
  <input id="startDate" type="date" style="padding:7px 10px; font-size:13px; border-radius:9999px; border:1px solid rgba(0,0,0,0.1); background:transparent; cursor:pointer;" />
  <span style="font-size:13px; color:#666;">and</span>
  <input id="endDate" type="date" style="padding:7px 10px; font-size:13px; border-radius:9999px; border:1px solid rgba(0,0,0,0.1); background:transparent; cursor:pointer;" />
  <button id="dueClear" type="button" style="padding:7px 12px; font-size:13px; font-weight:600; border-radius:9999px; border:1px solid rgba(0,0,0,0.1); background:transparent; color:#666; cursor:pointer;">Clear</button>
  <span id="dueHint" style="display:none; font-size:12px; color:#999;">Pick both dates to filter</span>
</div>

<script>
  (function () {
    var WIDE_START = "2000-01-01", WIDE_END = "2099-12-31";
    var BLOCK_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx";
    var FILTER_LABELS = ["Client", "Status", "Owner", "Region"];

    var wrap = document.getElementById("duePickerWrap");
    var startInput = document.getElementById("startDate");
    var endInput = document.getElementById("endDate");
    var clearBtn = document.getElementById("dueClear");
    var hint = document.getElementById("dueHint");
    var host = wrap ? (wrap.closest("section") || wrap.parentElement) : null;
    var url = new URL(window.location.href);

    var rawStart = url.searchParams.get("start_date");
    var rawEnd = url.searchParams.get("end_date");
    if (!rawStart && !rawEnd) {                       // blank load → seed wide → show all
      url.searchParams.set("start_date", WIDE_START);
      url.searchParams.set("end_date", WIDE_END);
      window.history.replaceState({}, "", url);
      window.location.reload();
      return;
    }
    if (rawStart && rawStart !== WIDE_START) startInput.value = rawStart;
    if (rawEnd && rawEnd !== WIDE_END) endInput.value = rawEnd;

    function apply() {
      url.searchParams.set("start_date", startInput.value ? startInput.value : WIDE_START);
      url.searchParams.set("end_date", endInput.value ? endInput.value : WIDE_END);
      window.history.replaceState({}, "", url);
      window.location.reload();
    }
    function applyWhenComplete() { if (startInput.value && endInput.value) apply(); }
    function updateHint() {
      var one = (startInput.value && !endInput.value) || (!startInput.value && endInput.value);
      if (hint) hint.style.display = one ? "inline" : "none";
    }
    startInput.addEventListener("change", function () { updateHint(); applyWhenComplete(); });
    endInput.addEventListener("change", function () { updateHint(); applyWhenComplete(); });
    clearBtn.addEventListener("click", function () {
      startInput.value = ""; endInput.value = ""; updateHint(); apply();
    });

    function lowestCommonAncestor(els) {
      if (!els.length) return null;
      var anc = els[0];
      for (var i = 1; i < els.length; i++) {
        while (anc && !anc.contains(els[i])) anc = anc.parentElement;
        if (!anc) return null;
      }
      return anc;
    }
    function findFilterRow() {
      var block = document.querySelector('[data-block-id="' + BLOCK_ID + '"]');
      if (!block) return null;
      var btns = block.querySelectorAll("button"), hits = [];
      for (var i = 0; i < btns.length; i++) {
        var t = (btns[i].textContent || "").replace(/\s+/g, " ").trim();
        for (var j = 0; j < FILTER_LABELS.length; j++) {
          if (t === FILTER_LABELS[j]) { hits.push(btns[i]); break; }
        }
      }
      if (hits.length >= 2) {
        var lca = lowestCommonAncestor(hits);
        if (lca && !lca.querySelector(".softr-list-container")) return lca;
      }
      var chip = block.querySelector(".a0e85ef_wsthdk3");
      if (chip && chip.parentElement) return chip.parentElement;
      return null;
    }
    function ensureHomed() {
      try {
        var row = findFilterRow();
        if (!row || !wrap) return;
        if (wrap.parentElement !== row) { wrap.style.marginLeft = "8px"; row.appendChild(wrap); }
        if (host && host.style.display !== "none" && !host.querySelector(".softr-list-container")) {
          host.style.display = "none";
        }
      } catch (err) {}
    }
    ensureHomed();
    setInterval(ensureHomed, 500);
  })();
</script>
```

---

## Gotchas (verified June 2026)

- **Empty `{URL_PARAM}` = match NOTHING.** A blank/missing param empties a filtered list. Seed a wide sentinel range (and map it back to blank inputs) so "no selection" shows all. §2.
- **Softr re-renders its list block and discards injected nodes.** One-shot relocation vanishes on the first interaction. Re-home on an interval/observer. §4c.
- **Page-wide DOM searches hit the native chrome.** Matching by text "Client" also matches a "Clients" nav link → control lands in the sidebar. Always scope to the block's `data-block-id`. §4a.
- **Filter chips have only hashed classes** (`a0e85ef_…`) that change on deploys. Anchor on your **filter label text + lowest common ancestor**; keep the hash as a fallback only. §4b.
- **`window.location.reload()` is how Softr re-reads the param.** `replaceState` alone updates the URL but won't re-run the conditional filter — you must reload.
- **Custom Code renders on the published app, sometimes not in the Studio editor.** Verify on the live/preview app, and **hard-refresh** (Cmd/Ctrl+Shift+R) after editing — a cached empty state can masquerade as "broken."
- **If the picker AND the records both vanish, the block isn't running.** Quick console probe: `new URL(location.href).searchParams.get("start_date")` (null = the seed never fired → script not executing) and `!!document.querySelector("#duePickerWrap")` (false = the HTML isn't on the page → re-paste/save the block).

## Finding the `data-block-id` and filter row in DevTools

1. Right-click the List/Grid block → **Inspect**. Walk up to the enclosing `<section data-block-id="…">` and copy that id → `BLOCK_ID`.
2. Inspect one filter chip; confirm its visible label text matches an entry in `FILTER_LABELS`.
3. Console sanity check (scoped, deploy-proof): 
   ```js
   var b = document.querySelector('[data-block-id="BLOCK_ID"]');
   console.log([].filter.call(b.querySelectorAll("button"), function (x) {
     return ["Client","Status","Owner","Region"].indexOf((x.textContent||"").trim()) > -1;
   }).length, "filter buttons found");
   ```
   ≥2 means the label/LCA path will resolve the row.

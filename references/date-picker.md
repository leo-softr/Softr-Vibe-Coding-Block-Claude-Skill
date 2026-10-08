# The brand date picker (`DatePicker`)

**No native date field in a branded block.** `<input type="date">`, `type="datetime-local"` and
`type="month"` open the browser's own calendar pop-up. That pop-up is browser UI, not page content,
so no CSS reaches it, from the block or from the header code: it shows the browser's colours and
fonts whatever the brand is. Use the `DatePicker` below instead. It draws its calendar in the
block's own DOM, styled with the brand tokens, and takes and returns the same `"yyyy-MM-dd"`
strings as the native field, so swapping one for the other changes nothing that is saved.

| Option | Why it fails in a block, or doesn't |
|---|---|
| `<input type="date">` and friends | The calendar pop-up is the browser's: unstyled by any CSS, and different in Chrome, Safari and Firefox. |
| shadcn `<Popover>` + `<Calendar>` | The Popover portals to `document.body`, outside the block's shadow root, like shadcn `<Select>` in [searchable-dropdown.md](searchable-dropdown.md) — so its styles would stay behind. Inferred from that same portal; not tried in a block. |
| `DatePicker` (below) | Local DOM, brand-styled, keyboard grid, min / max, Today and Clear, clip-aware placement, `"yyyy-MM-dd"` in and out. |

The kit picks a day. A time of day or a month-only value has no kit yet; build one on the same
rules before adding the native field back.

**Where it comes from.** On 2026-10-07 the Lane County Diaper Bank app (a Softr Database app with
Softr's sidebar navigation) set out to replace all 21 native date fields across 12 blocks, after
Leo flagged the browser calendar on the Reports page and again on Inventory's transaction history.
The component was built once, checked in a React 18.2 shadow-root harness (22 checks, Chromium and
macOS Firefox), pushed into the Reports and Volunteer Detail blocks first and checked there in a
browser with saves blocked, then rolled out block by block, each reviewed before its push. The
reviews produced the eight lessons below. Two of them (2 and 3) were faults in the component
itself, fixed once in the kit and synced into every block; that sync is why the kit sits between
markers.

## The API

Define it at **module scope**, never inside `Block()` (a component redefined per render remounts
and loses focus, like the Combo).

| Prop | Type | What it does |
|---|---|---|
| `id` | `string` | The trigger button's id. The calendar is `<id>-calendar`, the shown value `<id>-value`. |
| `value` | `string` | `"yyyy-MM-dd"`, or `""` for none. A value that does not parse is shown as it is. |
| `onChange` | `(next: string) => void` | Receives `"yyyy-MM-dd"`, or `""` from Clear. |
| `min`, `max` | `string?` | `"yyyy-MM-dd"`. Days outside are dimmed and cannot be picked; the keyboard and the month arrows stop at them. |
| `labelledBy` | `string?` | The label's id. The trigger is named by the label and the shown value, so it reads "Start date Oct 15, 2026". |
| `describedBy` | `string?` | A hint or error message id, as on a text input. |
| `placeholder` | `string?` | Shown while empty. Default `"Choose a date"`. |
| `clearable` | `boolean?` | Adds a Clear button for optional dates. Default `false`. |
| `disabled` | `boolean?` | Disables the trigger and closes an open calendar. |
| `textClass` | `string?` | The trigger's text size classes. Default `"text-[16px] @min-[48rem]:text-[14px]"`; see lesson 3. |

```tsx
// A labelled field. The label keeps htmlFor: a click on it opens the calendar, as it focused the native field.
<label id="start-label" htmlFor="start" className="mb-1.5 block text-[13px] font-medium">Start date</label>
<DatePicker id="start" labelledBy="start-label" value={start} onChange={setStart} max={end} clearable />
```

Most blocks wrap it once, as they wrap their text inputs (a `DateField` with the label, or a
`type="date"` branch in the block's own field component that renders `DatePicker` instead of an
`<input>`). The wrapper lives outside the kit's markers, below.

## The kit between markers

A Vibe block is one file and cannot import another (Hard Constraint 22), so every block that uses
the picker carries its own copy. Copies that are edited in place drift: a fix lands in the block
that showed the bug and in no other. So the copy is never edited in a block. The convention:

1. **One kit file in the project** holds the component, e.g. `Assets/Softr App/Shared/DatePicker.tsx`.
   It is the only place the component is edited.
2. **Each block pastes it verbatim, at module scope, between two marker lines.** The start line names
   the kit file and the first 12 hex of its sha256:

   ```tsx
   // ===== DatePicker: verbatim copy of Shared/DatePicker.tsx sha256 4763ca393a6c - edit there, not here =====
   /** DatePicker — brand-styled date field … (the kit file, byte for byte)
   …
   // ===== /DatePicker =====
   ```

3. **Anything block-specific stays outside the markers**: the `DateField` wrapper, the block's own
   imports (merge the kit's three import lines into the block's), and every difference between blocks,
   which goes through a prop (`textClass` exists for exactly that, lesson 3).
4. **A fix is synced mechanically.** Edit the kit file, then rewrite every marked region from it and
   check that none is left behind:

   ```bash
   cd "Assets/Softr App"   # the folder above the block folders; the marker records the kit path as given
   python3 Shared/kit-sync.py sync  DatePicker Shared/DatePicker.tsx */*.jsx
   python3 Shared/kit-sync.py check DatePicker Shared/DatePicker.tsx */*.jsx
   ```

   Each synced block is then a normal deploy: push it, prove the push by `sourceSha256`
   ([softr-mcp.md → Verifying a push](softr-mcp.md#verifying-a-push--the-deployed-source-is-the-only-proof)),
   re-apply its Action permissions (Hard Constraint 21: every save resets them) and update the
   mirror's header date. The sha in the marker tells anyone reading a deployed block which kit it
   carries without diffing 700 lines.

`kit-sync.py` (stdlib Python, keep it beside the kit file; any component can use it — the first
argument is the marker name):

```python
#!/usr/bin/env python3
"""Keep a shared component pasted verbatim between marker lines in every block.

  cd "Assets/Softr App"
  python3 Shared/kit-sync.py check DatePicker Shared/DatePicker.tsx */*.jsx
  python3 Shared/kit-sync.py sync  DatePicker Shared/DatePicker.tsx */*.jsx

The kit's markers in a block (the start line names the kit file and the first 12 hex of its sha256):
  // ===== DatePicker: verbatim copy of Shared/DatePicker.tsx sha256 f5753a191077 - edit there, not here =====
  ...the kit file, byte for byte...
  // ===== /DatePicker =====
Blocks without the markers are skipped. check exits 1 when any copy differs from the kit; sync rewrites the
copies that differ, and nothing outside the markers.
"""
import hashlib
import re
import sys


def main():
    if len(sys.argv) < 5 or sys.argv[1] not in ("check", "sync"):
        sys.exit(__doc__)
    mode, name, kit_path, blocks = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    with open(kit_path, encoding="utf-8", newline="") as f:  # newline="": bytes in, bytes out
        kit = f.read()
    if not kit.endswith("\n"):
        sys.exit(kit_path + ": must end with a newline, or the end marker joins its last line")
    sha = hashlib.sha256(kit.encode("utf-8")).hexdigest()[:12]
    start_re = re.compile(r"^// ===== %s: verbatim copy of .*sha256 ([0-9a-f]+) .*=====\n" % re.escape(name), re.M)
    end_re = re.compile(r"^// ===== /%s =====$" % re.escape(name), re.M)
    start_line = "// ===== %s: verbatim copy of %s sha256 %s - edit there, not here =====\n" % (name, kit_path, sha)
    bad = 0
    for path in blocks:
        with open(path, encoding="utf-8", newline="") as f:
            src = f.read()
        starts = list(start_re.finditer(src))
        if not starts:
            continue
        end = end_re.search(src, starts[0].end())
        if len(starts) > 1 or not end:
            print("BROKEN " + path + ": " + ("two start markers" if end else "no end marker"))
            bad += 1
            continue
        m = starts[0]
        if src[m.end():end.start()] == kit and m.group(1) == sha:
            print("ok     " + path)
        elif mode == "check":
            print("STALE  %s (marker %s, kit %s)" % (path, m.group(1), sha))
            bad += 1
        else:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(src[:m.start()] + start_line + kit + src[end.start():])
            print("synced %s (%s -> %s)" % (path, m.group(1), sha))
    sys.exit(1 if bad else 0)


main()
```

Tested on 2026-10-07 on copies of two LCDB blocks: `check` passes against their kit, flags both as
stale against a changed kit, `sync` rewrites only the marked region, and syncing back to the
original kit gives a file byte-identical to the original block. Blocks without the markers are
skipped.

The same convention fits any shared component, the Combo in
[searchable-dropdown.md](searchable-dropdown.md) included, whose "keep one canonical copy and port
changes from there" it makes mechanical.

## Lessons from the rollout

**1. Nothing between the field and its scroller may clip.** The calendar is an absolute panel
(`top-full` or `bottom-full`, `z-40`) inside the field's `relative` wrapper, in the block's own DOM,
for the same reasons as the Combo's menu: a portal leaves the shadow root and its styles, and
`position: fixed` breaks under any transformed ancestor
([searchable-dropdown.md → Why not portal](searchable-dropdown.md#the-four-things-that-will-bite-you)).
So every ancestor whose `overflow` is not `visible` clips it: `overflow-hidden`, `overflow-*-auto`,
`truncate`, `line-clamp-*`. A card given `overflow-hidden` to clip its rounded corners cuts the
calendar off at the card's edge. Same rule as Combo rule 1: no clipping class on anything that
contains a date field; bound an over-wide child at the child. A scroller the field genuinely sits
in (a modal body, a table scroller) is fine, because the placement measures it: the kit's
`dpClipBox` walks every ancestor, out through the shadow host, as `comboClipBox` does.

**2. In a short modal body, the calendar may scroll its trigger partly out of view.** The panel
opens down when it fits below, up when it fits above. When it fits neither way, the box that cuts
it off is scrolled by the smaller amount that makes room. When no scroll makes it fit, it opens
down and scrolls the box as far as it can, and that limit is the trigger's **bottom** edge, not its
top. The first version stopped at the trigger's top, to keep the whole field in view. In the
family page's Add child modal, whose body is short and sized by its content, that left the
calendar's Today / Clear row below the body's edge, cut off. Allowing the trigger to scroll
partly away fixed it. Down is the fallback because what hangs past a scroller's bottom extends its
scroll range, and what hangs past its top never does. The focused day is kept in view the same
way: scroll the one clipping box, never `scrollIntoView` (it scrolls every ancestor, the page
included), and issue the scroll from a `setTimeout` (Hard Constraint 17).

**3. Blocks that size controls by named containers pass the text size in.** The trigger must
look like the block's text inputs, text size included. The kit's default,
`text-[16px] @min-[48rem]:text-[14px]`, matches inputs sized by the nearest container (16px on a
narrow block, as inputs there must be so iOS does not zoom on focus). An unnamed `@min-[48rem]:`
resolves against the nearest ancestor container, whatever its name, which need not be the
container the block's own inputs are sized by.
The family page sizes its fields by named containers (`@min-[48rem]/page:` on the page,
`@min-[30rem]/panel:` inside its modal), and inside the modal the nearest container is the panel,
which is at most 40rem wide, so the default never reached 14px: the date fields showed 16px text
beside 14px inputs. The fix was a prop, not an edit inside the kit. Pass the input's own size
classes, copied from the block's input class string, as a static string so Tailwind's scan finds
them:

```tsx
<DatePicker … textClass="text-[16px] @min-[48rem]/page:text-[14px] @min-[30rem]/panel:text-[14px]" />
```

A block with no `@container` at all never matches the default's `@min-` class, so its trigger
stays at 16px. Pass that block's own sizes too.

**4. Escape on an open calendar closes only the calendar.** The panel's keydown handler (and the
trigger's, while open) calls `e.preventDefault()` and `e.stopPropagation()`, closes the calendar
and puts focus back on the trigger. An in-block modal listens for Escape on `document`
([common-patterns.md → A modal above Softr's bars](common-patterns.md#a-modal-above-softrs-bars))
and returns early on `defaultPrevented`; `stopPropagation` covers a document listener that does
not check it. React's handler runs at the block's root, inside the shadow root, before the event
reaches `document`. Without this, one Escape closes the calendar and the modal, or shows the modal's
"Discard your changes?" prompt with the calendar still open. Same rule as the Combo's
([Move focus into the Combo when it opens](searchable-dropdown.md#move-focus-into-the-combo-when-it-opens)).

**5. A backdrop click while a calendar is open must not silently drop the form.** The calendar
closes itself on `pointerdown` (a capture listener on `document`, read through `composedPath()`).
The press continues, and its `click` lands on the modal's backdrop, which dismisses the modal. A
form modal that dismisses without asking loses everything typed, for a click the user meant only
to close a calendar. Two acceptable outcomes:

- **Close only the calendar.** The modal records, at `pointerdown`, whether a calendar inside it
  was open, and the backdrop's click returns early if so:

  ```tsx
  // In the modal's mount effect: registered before any calendar inside can open, so it runs before the
  // calendar's own pointerdown close (capture listeners on one node run in registration order).
  const onPointerDownCapture = () => {
    pickerOpenAtDownRef.current = !!panel && !!panel.querySelector('[aria-haspopup="dialog"][aria-expanded="true"]');
  };
  document.addEventListener("pointerdown", onPointerDownCapture, true);
  // …and in the effect's cleanup: document.removeEventListener("pointerdown", onPointerDownCapture, true);

  // The backdrop:
  onClick={() => {
    if (pickerOpenAtDownRef.current) {
      pickerOpenAtDownRef.current = false; // that press only closed the calendar
      return;
    }
    dismissRef.current();
  }}
  ```

  Read it at `pointerdown`, the event the calendar closes on: a `mousedown` listener may already find
  it closed. A modal that also holds Combos (which close on `mousedown`) keeps its `mousedown` guard
  for them as well.
- **Ask.** The backdrop goes through the modal's dismiss request, which shows "Discard your
  changes?" when anything was typed — the in-block modal's own rule for Escape, the X and Cancel.

Either is fine. A backdrop that closes a dirty form without asking is not.

**6. A modal's focus fix-up must wait one task.** Some in-block modals watch their panel with a
`MutationObserver` and pull focus back to the panel when the focused control unmounts (Go back,
Keep editing, a failed confirm), so Tab stays inside the dialog. The calendar closes on blur when
Tab leaves it, so it unmounts in the middle of Tab's focus move. In Chromium, a synchronous
`panel.focus()` from the observer at that moment cancels the move: Tab landed on the modal panel
instead of the next field. Check one task later, and only refocus if focus really fell out:

```tsx
let observerTimer = 0;
const observer = new MutationObserver(() => {
  window.clearTimeout(observerTimer);
  observerTimer = window.setTimeout(() => {
    const a = root.activeElement as HTMLElement | null; // root = panel.getRootNode(): the shadow root
    if (!panel.isConnected) return;
    if (!a || a === document.body || !panel.contains(a)) panel.focus({ preventScroll: true });
  }, 0);
});
observer.observe(panel, { childList: true, subtree: true });
// cleanup: window.clearTimeout(observerTimer); observer.disconnect();
```

**7. Safari and macOS Firefox do not focus a clicked button.** Chrome does. So the kit never relies
on the click: once the panel is placed, it moves focus itself to the active day (the selected day,
else today, else the nearest day `min` / `max` allow), with `preventScroll`. On those browsers,
focus would otherwise stay in the text field above the date field, and keys and Escape would go
there. Two related details the kit handles: a blur with no `relatedTarget` (a click on nothing
focusable, the window losing focus) is not a Tab out, so it leaves the calendar open for the
click-outside listener to judge; and Chrome sends no `mousedown` for a disabled button (a dimmed
day, Today out of range) but focuses the panel itself instead, so the panel hands that focus on to
the active day. To reproduce Safari in any browser: focus a text field, call `.click()` on the
trigger from the console (a synthetic click moves focus nowhere either), then read the block's
shadow-root `activeElement`, which must be the day marked `data-dp-active="true"`.

**8. Date-only values stay `"yyyy-MM-dd"` strings.** In, out, `min`, `max`:

- **Compare as strings.** Zero-padded ISO days sort in date order, so `start <= end`,
  `max={end}` and "not after today" need no `Date` at all.
- **Load a stored date-only field by its first ten characters.** It arrives as midnight UTC
  ([fields.md](../datasources/fields.md#date-only-fields-arrive-as-midnight-utc)), whose date part
  is the intended day: `String(raw ?? "").slice(0, 10)`. Only for fields you know are date-only.
- **Write the string back as it is.** That is what the native field sent, so the saved bytes don't
  change (verify it, below).
- **Display through a local date:** `toLocalDate()` from fields.md, or the kit's `dpParse`. Never
  `new Date("yyyy-MM-dd")`, which is UTC midnight and a day early west of Greenwich.
- **Today is the browser's local day:** `format(new Date(), "yyyy-MM-dd")`. Not
  `new Date().toISOString().slice(0, 10)`, which is the UTC day: tomorrow, on a US evening.

## Verifying a block

**1. No native date field is left.** In the source, every hit of
`grep -nE 'type="(date|datetime-local|month)"' <block files>` must be a prop on the block's own
wrapper that renders the kit (`<FText type="date" …>`), never an `<input>`. Then in the preview,
with every form and modal that holds a date field opened, the count across all shadow roots is 0
([browser-checks.md](browser-checks.md) for the preview session and `eval`):

```js
(() => {
  const roots = [...document.querySelectorAll('*')].map(e => e.shadowRoot).filter(Boolean);
  const sel = 'input[type="date"], input[type="datetime-local"], input[type="month"]';
  return roots.reduce((n, r) => n + r.querySelectorAll(sel).length, 0) + document.querySelectorAll(sel).length;
})()
```

And `kit-sync.py check` passes, so every marked copy is the current kit.

**2. Nothing clips or covers the open calendar.** Open the calendar in the tight spots: the last
field of a modal body, a field low in a table scroller, near the window's right edge, at phone
width (375px, above Softr's tab bar). Then hit-test points on the panel through the shadow root
(`document.elementFromPoint` only returns the host):

```js
(() => {
  const root = [...document.querySelectorAll('*')].map(e => e.shadowRoot).filter(Boolean)
    .find(s => s.querySelector('[role="dialog"][id$="-calendar"]'));
  if (!root) return 'no open calendar';
  const panel = root.querySelector('[role="dialog"][id$="-calendar"]');
  const r = panel.getBoundingClientRect();
  const pts = { topLeft: [r.left + 6, r.top + 6], topRight: [r.right - 6, r.top + 6],
                bottomLeft: [r.left + 6, r.bottom - 6], bottomRight: [r.right - 6, r.bottom - 6] };
  for (const b of panel.querySelectorAll('button')) {
    const t = b.textContent.trim();
    if (t === 'Today' || t === 'Clear') { const q = b.getBoundingClientRect(); pts[t] = [q.left + q.width / 2, q.top + q.height / 2]; }
  }
  const out = {};
  for (const [k, [x, y]] of Object.entries(pts)) { const el = root.elementFromPoint(x, y); out[k] = !!el && panel.contains(el); }
  return JSON.stringify(out); // every value true; a false names the corner a clip or a bar covers
})()
```

Wait a beat after opening: when the panel needs room, the placement scrolls a box from a
`setTimeout`.

**3. Escape order.** With real key presses (`ab press Escape`), in a modal with something typed in
another field and the calendar open: the first Escape closes the calendar only (the modal is open,
no discard prompt, focus is on the date field's trigger); the second Escape reaches the modal
(it closes, or asks to discard). Then the backdrop case of lesson 5, and Tab out of the open calendar
inside the modal: focus lands on the next field, not on the modal panel (lesson 6).

**4. The saved value is byte-identical to the native version's.** Block saves first
([browser-checks.md → Block saves before any click, and prove it](browser-checks.md#6-block-saves-before-any-click-and-prove-it)),
pick a day, save, and read the aborted request's payload: the field holds the same string the native
field sent for that day (`"2026-10-15"`, not a timestamp). Clear sends what an emptied native field
sent, unless the block deliberately changed it (one LCDB block now saves a cleared optional date as
`null`).

## Re-skinning the kit

The tokens sit in `DP_C` at the top, and the Tailwind class strings repeat some of them as literal
hex, because a class string cannot read a constant (each string has a comment saying which hex is
which token). Change both, with a find-and-replace per hex over the kit file:

| Token | Kit value (LCDB) | Used for |
|---|---|---|
| `primary` | `#680058` | Selected day, today's ring, focus rings, Today button, the open trigger's border |
| `primaryDeep` | `#4E0042` | Hover on the selected day |
| `primaryTint` | `#F5EAF3` | Hover on Today |
| `ink` | `#030712` | Text |
| `muted` | `#6B7280` | Placeholder, weekday names, days of the next and previous month |
| `canvas` | `#F3F4F6` | Hover on days and icon buttons |
| `border` | `#D1D5DB` | Trigger and panel border |
| `divider` | `#E5E7EB` | The rule above Today / Clear (inline only) |
| `faint` | `#C4C8CF` | Days outside `min` / `max` |

Also: `DP_FONT_BODY` (the trigger's value, as the block's text inputs) and `DP_FONT_DISPLAY` (the
calendar), the trigger's height and radius in `DP_TRIGGER` (match the block's inputs), and
`DP_SOFTR_TOP_BAR`: `0` as verified (LCDB has no top bar), `56` when the app shows Softr's sticky
top bar, so the calendar never opens up under it (untested at 56; the bar heights are in
[searchable-dropdown.md](searchable-dropdown.md#the-four-things-that-will-bite-you)). After a
re-skin, the kit file's sha changes; sync it into every block.

## The kit file

Below is the whole kit, ready to save as the project's kit file. It is the LCDB kit (sha256
`f5753a191077…`, deployed 2026-10-07) with its comments made client-neutral and `DP_SOFTR_TOP_BAR`
added; at `0` it behaves exactly as deployed. This copy (sha256 `4763ca393a6c…`) passed the same
22 harness checks in Chromium 149 on 2026-10-07; the Firefox run was not repeated for it.

<details>
<summary>DatePicker.tsx (694 lines)</summary>

```tsx
/** DatePicker — brand-styled date field for Softr Vibe Coding blocks, replacing native <input type="date">: its
 * calendar pop-up is browser UI that no CSS reaches, so this one is drawn in the block's own DOM. Paste everything below
 * this comment at MODULE scope (never inside Block()). From softr-vibe-coding references/date-picker.md: the Lane County
 * Diaper Bank kit of 2026-10-07 (sha256 f5753a191077), comments generalized and DP_SOFTR_TOP_BAR added (0 = the
 * verified behaviour). That kit passed 22 checks in a React 18.2 shadow-root harness with Tailwind v4 (Chromium 149 and
 * macOS Firefox 157, TZ America/Los_Angeles, today fixed at 2026-10-07) and shipped in 12 blocks.
 *
 * Imports it needs (merge the names into the block's existing import lines):
 *   import { useEffect, useLayoutEffect, useRef, useState } from "react";
 *   import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";
 *   import { addDays, addMonths, addYears, format, startOfMonth, startOfWeek } from "date-fns";
 *
 * Usage:
 *   <label id="start-label" htmlFor="start">Start date</label>
 *   <DatePicker id="start" labelledBy="start-label" value={start} onChange={setStart} max={end} clearable />
 * value, min and max are "yyyy-MM-dd" strings or ""; onChange(next) receives "yyyy-MM-dd", or "" from Clear.
 * textClass sets the trigger's text size. The default suits blocks that size controls by the nearest container; a block
 * that sizes them by named containers passes its own (e.g. "text-[16px] @min-[48rem]/page:text-[14px]").
 * The label's htmlFor may stay: a click on the label opens the picker, as it focuses a native date field.
 * Nothing between the field and the scroller it belongs to may clip (overflow-hidden, truncate, line-clamp): the
 * calendar is an absolute panel in the block's DOM (softr-vibe-coding references/searchable-dropdown.md, rule 1).
 */

// Brand tokens this component uses (the project's DESIGN.md): a copy, because blocks cannot import each other (Hard
// Constraint 22). Tailwind class strings repeat some as literal hex; each says which. Re-skin both.
const DP_C = {
  primary: "#680058",
  primaryDeep: "#4E0042", // hover on primary
  primaryTint: "#F5EAF3",
  ink: "#030712",
  muted: "#6B7280", // labels, weekday names, days of the next and previous month
  canvas: "#F3F4F6", // hover on days and icon buttons
  border: "#D1D5DB",
  divider: "#E5E7EB",
  faint: "#C4C8CF", // days outside min / max: dimmed, not selectable (not a text colour for anything to read)
} as const;
const DP_SHADOW_MENU = "0 8px 24px rgba(3,7,18,0.08)";
const DP_FONT_BODY = "Verdana, Geneva, 'DejaVu Sans', Tahoma, sans-serif"; // the field's value, as in the text inputs
const DP_FONT_DISPLAY = "'Poppins', ui-sans-serif, system-ui, sans-serif"; // the calendar: heading, days, buttons
const DP_PANEL_REM = 18.5; // panel width: 296px, fits a 343px phone content column
const DP_GAP = 4; // trigger to panel
const DP_EDGE = 8; // room kept free at the edges of the strip the panel can paint into
const DP_SOFTR_TAB_BAR = 57; // Softr's phone tab bar, window below 768px: measured 57px
const DP_SOFTR_TOP_BAR = 0; // 56 when the app shows Softr's sticky top bar (window 768px and up); untested at 56
const DP_WEEKDAYS = [
  ["Su", "Sunday"],
  ["Mo", "Monday"],
  ["Tu", "Tuesday"],
  ["We", "Wednesday"],
  ["Th", "Thursday"],
  ["Fr", "Friday"],
  ["Sa", "Saturday"],
] as const;

// Days: a 36px circle in a ~39px column. Hover lives in classes (inline would beat it).
// #680058 = DP_C.primary · #4E0042 = DP_C.primaryDeep · #030712 = DP_C.ink · #6B7280 = DP_C.muted
// #F3F4F6 = DP_C.canvas · #C4C8CF = DP_C.faint
const DP_DAY =
  "mx-auto flex h-9 w-9 items-center justify-center rounded-full text-[14px] leading-none transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#680058]";
const DP_DAY_SELECTED = "bg-[#680058] font-semibold text-white hover:bg-[#4E0042]";
const DP_DAY_TODAY = "font-semibold text-[#680058] hover:bg-[#F3F4F6]";
const DP_DAY_IN = "text-[#030712] hover:bg-[#F3F4F6]";
const DP_DAY_OUT = "text-[#6B7280] hover:bg-[#F3F4F6]";
const DP_DAY_OFF = "cursor-default text-[#C4C8CF]";
// Months in the month / year view: same states, as 44px pills.
const DP_MONTH =
  "flex h-11 w-full items-center justify-center rounded-full text-[14px] transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#680058]";
// Month arrows: 44px targets. aria-disabled (not disabled), so an arrow keeps focus when it reaches min or max.
const DP_ICON_BTN =
  "flex h-11 w-11 items-center justify-center rounded-full transition-colors hover:bg-[#F3F4F6] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#680058] aria-disabled:cursor-default aria-disabled:opacity-35 aria-disabled:hover:bg-transparent";
// The trigger is the blocks' text input: 44px. Its text size comes from the textClass prop: by default 16px below a
// 48rem container (stops iOS zoom) and 14px from it.
// #D1D5DB = DP_C.border · #680058 = DP_C.primary (focus border and ring; kept while the calendar is open)
const DP_TRIGGER =
  "flex h-11 w-full items-center justify-between gap-2 rounded-xl border border-[#D1D5DB] bg-white px-3 text-left transition-colors focus:border-[#680058] focus:outline-none focus:ring-2 focus:ring-[#680058]/25 aria-expanded:border-[#680058] aria-expanded:ring-2 aria-expanded:ring-[#680058]/25 disabled:cursor-not-allowed disabled:opacity-60";

type DpPlace = { up: boolean; x: number; maxW: number | null; ready: boolean };

// "yyyy-MM-dd" -> a local-midnight Date, or null. Never new Date("yyyy-MM-dd"): that is UTC midnight, a day early
// west of Greenwich. Rejects impossible dates (2026-02-30) instead of rolling them over.
function dpParse(s: string | null | undefined): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s ?? "").trim());
  if (!m) return null;
  const y = Number(m[1]);
  const mo = Number(m[2]) - 1;
  const day = Number(m[3]);
  const d = new Date(2000, 0, 1);
  d.setFullYear(y, mo, day); // setFullYear: years below 100 stay themselves
  return d.getFullYear() === y && d.getMonth() === mo && d.getDate() === day ? d : null;
}
const dpIso = (d: Date) => format(d, "yyyy-MM-dd");
const dpKey = (d: Date) => d.getFullYear() * 10000 + d.getMonth() * 100 + d.getDate(); // compare days, not times
function dpToday() {
  const n = new Date();
  return new Date(n.getFullYear(), n.getMonth(), n.getDate());
}
function dpAllowed(d: Date, min: Date | null, max: Date | null) {
  return (!min || dpKey(d) >= dpKey(min)) && (!max || dpKey(d) <= dpKey(max));
}
function dpClamp(d: Date, min: Date | null, max: Date | null) {
  if (min && dpKey(d) < dpKey(min)) return min;
  if (max && dpKey(d) > dpKey(max)) return max;
  return d;
}

// The strip of screen the panel can paint into: the window (minus Softr's bars), cut down by every ancestor that
// clips, as comboClipBox in searchable-dropdown.md. Also returns the boxes that set the top and bottom edges (null =
// the window), for the nudge in dpPlace.
function dpClipBox(node: HTMLElement) {
  const phone = window.innerWidth < 768;
  let top = phone ? 0 : DP_SOFTR_TOP_BAR;
  let left = 0;
  let right = window.innerWidth;
  let bottom = window.innerHeight - (phone ? DP_SOFTR_TAB_BAR : 0);
  let topEl: HTMLElement | null = null;
  let bottomEl: HTMLElement | null = null;
  let el: any = node;
  while (el && el !== document.body && el !== document.documentElement) {
    // clientHeight / clientWidth are 0 for the boxes overflow does not apply to (inline, display: contents)
    if (el.clientHeight > 0 || el.clientWidth > 0) {
      const cs = window.getComputedStyle(el);
      const r = el.getBoundingClientRect();
      if (cs.overflowY !== "visible") {
        const t = r.top + el.clientTop; // the clip edge is the padding box: inside the border
        const b = t + el.clientHeight; //  and above a horizontal scrollbar
        if (t > top) {
          top = t;
          topEl = el;
        }
        if (b < bottom) {
          bottom = b;
          bottomEl = el;
        }
      }
      if (cs.overflowX !== "visible") {
        const l = r.left + el.clientLeft;
        const rr = l + el.clientWidth;
        if (l > left) left = l;
        if (rr < right) right = rr;
      }
    }
    // Where the parent chain ends at the shadow root, carry on from its host.
    el = el.parentElement || (el.getRootNode ? (el.getRootNode() as any).host : null) || null;
  }
  return { top, bottom, left, right, topEl, bottomEl };
}

// Can this edge box (null = the window) be scrolled, and how far is it scrolled now?
function dpScrollable(el: HTMLElement | null) {
  return el
    ? /(auto|scroll)/.test(window.getComputedStyle(el).overflowY)
    : window.getComputedStyle(document.documentElement).overflowY !== "hidden";
}

// focus({ preventScroll: true }) does not reveal what it focuses. When the active day sits past the edge of the box
// that clips it (a short modal body), scroll that one box just far enough; never scrollIntoView, which scrolls every
// ancestor including the page.
function dpKeepVisible(el: HTMLElement) {
  const clip = dpClipBox(el);
  const r = el.getBoundingClientRect();
  if (r.bottom > clip.bottom - DP_EDGE && dpScrollable(clip.bottomEl)) {
    const by = r.bottom - (clip.bottom - DP_EDGE);
    if (clip.bottomEl) clip.bottomEl.scrollTop += by;
    else window.scrollBy(0, by);
  } else if (r.top < clip.top + DP_EDGE && dpScrollable(clip.topEl)) {
    const by = clip.top + DP_EDGE - r.top;
    if (clip.topEl) clip.topEl.scrollTop -= by;
    else window.scrollBy(0, -by);
  }
}

// Where the panel goes. Down when it fits below, else up when it fits above. When it fits neither way (a short modal
// body, a small window), the box that cuts it off is nudged by the smaller scroll that makes it fit with the trigger
// still in view: up into room above (only as far as that box is scrolled down), or down into room below. When no
// nudge makes it fit: down, scrolled as far as the trigger allows, so the rest can be scrolled to (what hangs past a
// scroller's bottom extends its scroll range; past its top it never does); with no scroller at all, the larger side.
// Horizontally it hangs from the trigger's left edge and shifts left to stay inside the strip.
function dpPlace(wrapper: HTMLElement, panelH: number) {
  const clip = dpClipBox(wrapper);
  const r = wrapper.getBoundingClientRect();
  const below = clip.bottom - r.bottom - DP_GAP - DP_EDGE;
  const above = r.top - clip.top - DP_GAP - DP_EDGE;
  let up = below < panelH && above >= panelH;
  let scroller: HTMLElement | Window | null = null;
  let scrollBy = 0; // positive scrolls down (the content moves up)
  if (below < panelH && above < panelH) {
    const needUp = panelH - above; // scroll the top box back this far to make room above
    const needDown = panelH - below; // scroll the bottom box on this far to make room below
    const topScroll = clip.topEl ? clip.topEl.scrollTop : window.scrollY;
    const canUp =
      dpScrollable(clip.topEl) && topScroll >= needUp && r.bottom + needUp <= clip.bottom - DP_EDGE;
    const canDown = dpScrollable(clip.bottomEl);
    const downFits = canDown && r.top - needDown >= clip.top + DP_EDGE;
    if (canUp && (!downFits || needUp <= needDown)) {
      up = true;
      scroller = clip.topEl || window;
      scrollBy = -needUp;
    } else if (canDown) {
      up = false;
      scroller = clip.bottomEl || window;
      // Up to the trigger's bottom edge, not its top: in a short modal body the whole calendar then fits, and only
      // part of the trigger scrolls out of view.
      scrollBy = Math.max(0, Math.min(needDown, r.bottom - clip.top - DP_EDGE));
    } else {
      up = above > below;
    }
  }
  const remPx = parseFloat(window.getComputedStyle(document.documentElement).fontSize) || 16;
  const room = clip.right - clip.left - 2 * DP_EDGE;
  const w = Math.min(DP_PANEL_REM * remPx, Math.max(256, room));
  let x = 0;
  if (r.left + w > clip.right - DP_EDGE) x = clip.right - DP_EDGE - w - r.left;
  if (r.left + x < clip.left + DP_EDGE) x = clip.left + DP_EDGE - r.left;
  return { up, x: Math.round(x), maxW: w < DP_PANEL_REM * remPx ? Math.floor(w) : null, scroller, scrollBy };
}

function DatePicker({
  id,
  value,
  onChange,
  placeholder = "Choose a date",
  min,
  max,
  labelledBy,
  describedBy,
  clearable = false,
  disabled = false,
  textClass = "text-[16px] @min-[48rem]:text-[14px]",
}: {
  id: string;
  value: string;
  onChange: (next: string) => void;
  placeholder?: string;
  min?: string;
  max?: string;
  labelledBy?: string;
  describedBy?: string;
  clearable?: boolean;
  disabled?: boolean;
  textClass?: string;
}) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const focusPending = useRef(false); // move focus to the active day / month after the next render
  const triggerPointer = useRef(false); // a pointer press on the trigger is under way (its click toggles)
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<"days" | "months">("days");
  const [focusDate, setFocusDate] = useState<Date>(() => dpToday());
  const [today, setToday] = useState<Date>(() => dpToday());
  const [place, setPlace] = useState<DpPlace>({ up: false, x: 0, maxW: null, ready: false });

  const selected = dpParse(value);
  const minD = dpParse(min);
  const maxD = dpParse(max);
  const shown = selected ? format(selected, "MMM d, yyyy") : value; // an unreadable value is shown as it is
  const dialogId = `${id}-calendar`;
  const valueId = `${id}-value`;
  const monthLabelId = `${id}-month`;

  function openPicker() {
    if (disabled) return;
    const t = dpToday();
    setToday(t);
    // The selected day, else today, else the nearest day min / max allow.
    setFocusDate(dpClamp(selected || t, minD, maxD));
    setView("days");
    setPlace({ up: false, x: 0, maxW: null, ready: false });
    focusPending.current = true;
    setOpen(true);
  }
  function closePicker(refocus: boolean) {
    setOpen(false);
    setView("days");
    focusPending.current = false;
    if (refocus) triggerRef.current?.focus({ preventScroll: true });
  }
  function pick(d: Date) {
    if (!dpAllowed(d, minD, maxD)) return;
    onChange(dpIso(d));
    closePicker(true);
  }
  function moveTo(d: Date) {
    focusPending.current = true;
    setFocusDate(dpClamp(d, minD, maxD));
  }

  // Place the panel before it paints: measured hidden, then shown up or down, shifted to stay inside the strip.
  useLayoutEffect(() => {
    if (!open) return;
    const wrap = rootRef.current;
    const panel = panelRef.current;
    if (!wrap || !panel) return;
    const p = dpPlace(wrap, panel.offsetHeight);
    setPlace({ up: p.up, x: p.x, maxW: p.maxW, ready: true });
    if (p.scroller && p.scrollBy !== 0) {
      const sc = p.scroller;
      const by = p.scrollBy;
      // Hard Constraint 17: programmatic scrolls go through setTimeout. Only this one box scrolls (no scrollIntoView).
      window.setTimeout(() => {
        if (sc === window) window.scrollBy(0, by);
        else (sc as HTMLElement).scrollTop += by;
      }, 0);
    }
  }, [open]);

  // Move focus into the calendar on open, and onto the active day or month after keyboard moves and view changes.
  // Done here, not by the click: Safari and macOS Firefox do not focus a clicked button, and a synthetic .click()
  // moves focus nowhere. preventScroll: focusing must not scroll the page or a modal body.
  useEffect(() => {
    if (!open || !place.ready || !focusPending.current) return;
    focusPending.current = false;
    const el = panelRef.current?.querySelector('[data-dp-active="true"]') as HTMLElement | null;
    if (!el) return;
    el.focus({ preventScroll: true });
    // After the placement's own scroll (queued first, so it runs first).
    window.setTimeout(() => {
      if (el.isConnected) dpKeepVisible(el);
    }, 0);
  });

  // Click outside closes: pointerdown on the document, read through composedPath() because the shadow root
  // retargets the event's target to the block's host.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: PointerEvent) => {
      const root = rootRef.current;
      if (!root) return;
      const path = e.composedPath ? e.composedPath() : [];
      if (path.indexOf(root) !== -1) return;
      if (path.length === 0 && e.target && root.contains(e.target as Node)) return;
      closePicker(false);
    };
    document.addEventListener("pointerdown", onDown, true);
    return () => document.removeEventListener("pointerdown", onDown, true);
  }, [open]);

  // A window resize (a turned tablet) re-places the open panel.
  useEffect(() => {
    if (!open) return;
    const onResize = () => {
      const wrap = rootRef.current;
      const panel = panelRef.current;
      if (!wrap || !panel) return;
      const p = dpPlace(wrap, panel.offsetHeight);
      setPlace({ up: p.up, x: p.x, maxW: p.maxW, ready: true });
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [open]);

  useEffect(() => {
    if (disabled && open) closePicker(false);
  }, [disabled, open]);

  // Keyboard on the day grid (WAI-ARIA date picker dialog). Enter and Space are the buttons' own clicks.
  function onDayKey(e: React.KeyboardEvent) {
    const d = focusDate;
    let next: Date | null = null;
    if (e.key === "ArrowLeft") next = addDays(d, -1);
    else if (e.key === "ArrowRight") next = addDays(d, 1);
    else if (e.key === "ArrowUp") next = addDays(d, -7);
    else if (e.key === "ArrowDown") next = addDays(d, 7);
    else if (e.key === "Home") next = startOfWeek(d, { weekStartsOn: 0 });
    else if (e.key === "End") next = addDays(startOfWeek(d, { weekStartsOn: 0 }), 6);
    else if (e.key === "PageUp") next = e.shiftKey ? addYears(d, -1) : addMonths(d, -1);
    else if (e.key === "PageDown") next = e.shiftKey ? addYears(d, 1) : addMonths(d, 1);
    else if (e.key === "Enter" && e.repeat) e.preventDefault(); // a held Enter that opened the picker must not pick
    if (!next) return;
    e.preventDefault();
    moveTo(next);
  }
  function onMonthKey(e: React.KeyboardEvent) {
    const d = focusDate;
    let next: Date | null = null;
    if (e.key === "ArrowLeft") next = addMonths(d, -1);
    else if (e.key === "ArrowRight") next = addMonths(d, 1);
    else if (e.key === "ArrowUp") next = addMonths(d, -3);
    else if (e.key === "ArrowDown") next = addMonths(d, 3);
    else if (e.key === "Home") next = addMonths(d, -d.getMonth());
    else if (e.key === "End") next = addMonths(d, 11 - d.getMonth());
    else if (e.key === "PageUp") next = addYears(d, -1);
    else if (e.key === "PageDown") next = addYears(d, 1);
    else if (e.key === "Enter" && e.repeat) e.preventDefault();
    if (!next) return;
    e.preventDefault();
    moveTo(next);
  }
  function chooseMonth(m: number) {
    // Same day of the month where it exists (addMonths clamps the 31st), inside min / max.
    moveTo(addMonths(focusDate, m - focusDate.getMonth()));
    setView("days");
  }

  // The month on show and the arrows' limits.
  const monthStart = startOfMonth(focusDate);
  const year = focusDate.getFullYear();
  const prevOff =
    view === "days"
      ? !!minD && dpKey(addDays(monthStart, -1)) < dpKey(minD)
      : !!minD && year - 1 < minD.getFullYear();
  const nextOff =
    view === "days"
      ? !!maxD && dpKey(addMonths(monthStart, 1)) > dpKey(maxD)
      : !!maxD && year + 1 > maxD.getFullYear();
  function step(dir: -1 | 1) {
    if (dir < 0 ? prevOff : nextOff) return;
    const next = dpClamp(view === "days" ? addMonths(focusDate, dir) : addYears(focusDate, dir), minD, maxD);
    setFocusDate(next); // a click on an arrow leaves focus on the arrow
  }
  const todayOff = !dpAllowed(today, minD, maxD);

  const gridStart = startOfWeek(monthStart, { weekStartsOn: 0 });
  const weeks: Date[][] = [];
  for (let w = 0; w < 6; w++) {
    const row: Date[] = [];
    for (let i = 0; i < 7; i++) row.push(addDays(gridStart, w * 7 + i));
    weeks.push(row);
  }
  const heading = view === "days" ? format(focusDate, "MMMM yyyy") : String(year);

  return (
    <div ref={rootRef} className="relative">
      <button
        ref={triggerRef}
        id={id}
        type="button"
        disabled={disabled}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={dialogId}
        aria-labelledby={labelledBy ? `${labelledBy} ${valueId}` : undefined}
        aria-describedby={describedBy}
        onPointerDown={() => {
          triggerPointer.current = true;
        }}
        onClick={() => {
          triggerPointer.current = false;
          if (open) closePicker(true);
          else openPicker();
        }}
        onKeyDown={(e) => {
          triggerPointer.current = false;
          if (!open && e.key === "ArrowDown") {
            e.preventDefault();
            openPicker();
          } else if (open && e.key === "Escape") {
            e.preventDefault();
            e.stopPropagation();
            closePicker(false);
          }
        }}
        className={DP_TRIGGER + " " + textClass}
        style={{ fontFamily: DP_FONT_BODY, color: shown ? DP_C.ink : DP_C.muted }}
      >
        <span id={valueId} className="min-w-0 truncate">
          {shown || placeholder}
        </span>
        <CalendarDays
          className="h-[18px] w-[18px] shrink-0"
          style={{ color: open ? DP_C.primary : DP_C.muted }}
          aria-hidden="true"
        />
      </button>

      {open ? (
        <div
          ref={panelRef}
          id={dialogId}
          role="dialog"
          aria-label="Choose a date"
          tabIndex={-1}
          onMouseDown={(e) => {
            // A press on the padding or a weekday name leaves focus on the active day, so the keys keep working.
            if (!(e.target as HTMLElement).closest("button")) e.preventDefault();
          }}
          onFocus={(e) => {
            // Chrome sends no mousedown for a disabled button (a dimmed day, Today out of range) and focuses the
            // panel itself instead: hand that focus on to the active day or month.
            if (e.target !== e.currentTarget) return;
            const el = e.currentTarget.querySelector('[data-dp-active="true"]') as HTMLElement | null;
            el?.focus({ preventScroll: true });
          }}
          onKeyDown={(e) => {
            if (e.key !== "Escape") return;
            // Escape closes this calendar and nothing else: preventDefault for a surrounding modal that checks
            // defaultPrevented, stopPropagation for any document listener that does not.
            e.preventDefault();
            e.stopPropagation();
            closePicker(true);
          }}
          onBlur={(e) => {
            // Tab or Shift+Tab out of the calendar closes it. A null relatedTarget (a click on nothing focusable,
            // the window losing focus) is not a leave: clicks outside are the pointerdown listener's job.
            const next = e.relatedTarget as Node | null;
            if (!next || panelRef.current?.contains(next)) return;
            if (next === triggerRef.current && triggerPointer.current) return; // the trigger's click will toggle
            closePicker(false);
          }}
          className={`absolute z-40 w-[18.5rem] rounded-xl border bg-white p-3 outline-none ${
            place.up ? "bottom-full mb-1" : "top-full mt-1"
          }`}
          style={{
            left: place.x,
            maxWidth: place.maxW ?? undefined,
            visibility: place.ready ? "visible" : "hidden",
            borderColor: DP_C.border,
            boxShadow: DP_SHADOW_MENU,
            fontFamily: DP_FONT_DISPLAY,
            color: DP_C.ink,
          }}
        >
          <div className="flex items-center justify-between">
            <button
              type="button"
              aria-label={view === "days" ? `${heading}, choose month and year` : `${heading}, back to days`}
              onClick={() => {
                focusPending.current = true;
                setView(view === "days" ? "months" : "days");
              }}
              // #F3F4F6 = DP_C.canvas · #680058 = DP_C.primary
              className="-ml-1 inline-flex h-11 items-center gap-1 rounded-full pl-2.5 pr-2 text-[15px] font-semibold transition-colors hover:bg-[#F3F4F6] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#680058]"
            >
              {heading}
              <ChevronRight
                className={`h-4 w-4 transition-transform ${view === "days" ? "rotate-90" : "-rotate-90"}`}
                style={{ color: DP_C.muted }}
                aria-hidden="true"
              />
            </button>
            <div className="-mr-1.5 flex items-center">
              <button
                type="button"
                aria-label={view === "days" ? "Previous month" : "Previous year"}
                aria-disabled={prevOff || undefined}
                onClick={() => step(-1)}
                className={DP_ICON_BTN}
              >
                <ChevronLeft className="h-[18px] w-[18px]" aria-hidden="true" />
              </button>
              <button
                type="button"
                aria-label={view === "days" ? "Next month" : "Next year"}
                aria-disabled={nextOff || undefined}
                onClick={() => step(1)}
                className={DP_ICON_BTN}
              >
                <ChevronRight className="h-[18px] w-[18px]" aria-hidden="true" />
              </button>
            </div>
          </div>

          {/* Announces the month as keys move through it; also the grid's name. */}
          <div id={monthLabelId} aria-live="polite" className="sr-only">
            {format(focusDate, "MMMM yyyy")}
          </div>

          {/* Both views are the same height, so switching never moves the panel. */}
          <div className="mt-1 h-[16rem]">
            {view === "days" ? (
              <table
                role="grid"
                aria-labelledby={monthLabelId}
                className="w-full table-fixed border-collapse"
                onKeyDown={onDayKey}
              >
                <thead>
                  <tr>
                    {DP_WEEKDAYS.map(([short, long]) => (
                      <th
                        key={short}
                        scope="col"
                        abbr={long}
                        className="h-7 p-0 text-center text-[12px] font-medium"
                        style={{ color: DP_C.muted }}
                      >
                        {short}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {weeks.map((row, w) => (
                    <tr key={w}>
                      {row.map((d, i) => {
                        const isSel = !!selected && dpKey(d) === dpKey(selected);
                        const isToday = dpKey(d) === dpKey(today);
                        const inMonth = d.getMonth() === focusDate.getMonth();
                        const ok = dpAllowed(d, minD, maxD);
                        const active = dpKey(d) === dpKey(focusDate);
                        const tone = isSel
                          ? DP_DAY_SELECTED
                          : !ok
                            ? DP_DAY_OFF
                            : isToday
                              ? DP_DAY_TODAY
                              : inMonth
                                ? DP_DAY_IN
                                : DP_DAY_OUT;
                        return (
                          // Keyed by position, so a month change keeps the focused button in the DOM.
                          <td key={i} role="gridcell" aria-selected={isSel} className="p-0 py-px text-center">
                            <button
                              type="button"
                              tabIndex={active ? 0 : -1}
                              data-dp-active={active ? "true" : undefined}
                              disabled={!ok}
                              aria-label={format(d, "EEEE, MMMM d, yyyy")}
                              aria-current={isToday ? "date" : undefined}
                              onClick={() => pick(d)}
                              className={`${DP_DAY} ${tone}`}
                              // Today: a 1px primary ring, inline so it does not rest on Tailwind's ring variables.
                              style={isToday && !isSel && ok ? { boxShadow: `inset 0 0 0 1px ${DP_C.primary}` } : undefined}
                            >
                              {d.getDate()}
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div
                role="grid"
                aria-label={`Months of ${year}`}
                className="flex h-full flex-col justify-center gap-3"
                onKeyDown={onMonthKey}
              >
                {[0, 1, 2, 3].map((r) => (
                  <div key={r} role="row" className="grid grid-cols-3 gap-x-2">
                    {[0, 1, 2].map((c) => {
                      const m = r * 3 + c;
                      const first = new Date(year, m, 1);
                      const last = addDays(addMonths(first, 1), -1);
                      const ok = (!minD || dpKey(last) >= dpKey(minD)) && (!maxD || dpKey(first) <= dpKey(maxD));
                      const isSel = !!selected && selected.getFullYear() === year && selected.getMonth() === m;
                      const isNow = today.getFullYear() === year && today.getMonth() === m;
                      const active = focusDate.getMonth() === m;
                      const tone = isSel ? DP_DAY_SELECTED : !ok ? DP_DAY_OFF : isNow ? DP_DAY_TODAY : DP_DAY_IN;
                      return (
                        <div key={m} role="gridcell" aria-selected={isSel}>
                          <button
                            type="button"
                            tabIndex={active ? 0 : -1}
                            data-dp-active={active ? "true" : undefined}
                            disabled={!ok}
                            aria-label={format(first, "MMMM yyyy")}
                            aria-current={isNow ? "date" : undefined}
                            onClick={() => chooseMonth(m)}
                            className={`${DP_MONTH} ${tone}`}
                            style={isNow && !isSel && ok ? { boxShadow: `inset 0 0 0 1px ${DP_C.primary}` } : undefined}
                          >
                            {format(first, "MMM")}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="mt-2 flex items-center justify-between border-t pt-2" style={{ borderColor: DP_C.divider }}>
            <button
              type="button"
              disabled={todayOff}
              onClick={() => pick(today)}
              // #680058 = DP_C.primary · #F5EAF3 = DP_C.primaryTint
              className="-ml-1 inline-flex h-10 items-center rounded-full px-3 text-[14px] font-semibold text-[#680058] transition-colors hover:bg-[#F5EAF3] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#680058] disabled:cursor-default disabled:opacity-40 disabled:hover:bg-transparent"
            >
              Today
            </button>
            {clearable ? (
              <button
                type="button"
                onClick={() => {
                  onChange("");
                  closePicker(true);
                }}
                // #6B7280 = DP_C.muted · #F3F4F6 = DP_C.canvas · #030712 = DP_C.ink · #680058 = DP_C.primary
                className="-mr-1 inline-flex h-10 items-center rounded-full px-3 text-[14px] font-medium text-[#6B7280] transition-colors hover:bg-[#F3F4F6] hover:text-[#030712] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#680058]"
              >
                Clear
              </button>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
```

</details>

## Checklist before shipping a date field

- [ ] No `<input type="date">`, `datetime-local` or `month` in the block (source grep, then the DOM count)
- [ ] The kit pasted verbatim between its markers, at module scope; `kit-sync.py check` passes
- [ ] Block-specific code (wrapper, imports, `textClass`) outside the markers
- [ ] No clipping class between the field and its scroller
- [ ] Trigger text size matches the block's inputs (`textClass` where containers are named)
- [ ] Escape closes only the calendar; the second Escape reaches the modal
- [ ] Backdrop click with a calendar open: closes only the calendar, or asks to discard
- [ ] A modal's focus fix-up deferred with `setTimeout(…, 0)`; Tab out of the calendar reaches the next field
- [ ] Values are `"yyyy-MM-dd"` strings; compared as strings; displayed through a local date
- [ ] The saved payload is the same string the native field sent

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
| `DatePicker` (below) | Local DOM, brand-styled, keyboard grid, min / max, Today and Clear, clip-aware placement that shrinks to fit a short screen, `"yyyy-MM-dd"` in and out. |

The kit picks a day. A time of day or a month-only value has no kit yet; build one on the same
rules before adding the native field back.

**Where it comes from.** On 2026-10-07 the LCDB app (a Softr Database app with Softr's sidebar
navigation) set out to replace all 21 native date fields across 12 blocks, after the browser
calendar was flagged on the Reports page and again on Inventory's transaction history.
The component was built once, checked in a React 18.2 shadow-root harness (22 checks, Chromium and
macOS Firefox), pushed into the Reports and Volunteer Detail blocks first and checked there in a
browser with saves blocked, then rolled out block by block, each reviewed before its push. The
reviews produced the eight lessons below. Two of them (2 and 3) were faults in the component
itself, fixed once in the kit and synced into every block; that sync is why the kit sits between
markers.

A second round on 2026-10-08 (QA of those 12 blocks on short screens) found the calendar overrunning
a 392px dialog body at 1280×600, losing a third of its day buttons on a 568×320 landscape phone, and
ending under Softr's tab bar at the end of a short page on a phone. The first rework failed its
review (Today and Clear still out of reach at the end of a short page, and a Firefox Tab stop), the
second failed on Softr's smooth scrolling, which no harness had, and the third was approved after a
49-case matrix in Chromium, Firefox and WebKit. That is the kit below.
[Short screens](#short-screens) says what it does now, and
[Verifying a change to the kit](#verifying-a-change-to-the-kit) says what the round taught.

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

No prop controls how the panel fits a short screen. That is automatic, on open: see [Short screens](#short-screens).
Nor is there a prop or constant for Softr's sticky top bar: the kit's strip starts at the top of the window, so an app that shows the bar needs the one-line edit in [Re-skinning the kit](#re-skinning-the-kit).

```tsx
// A labelled field. The label keeps htmlFor: a click on it opens the calendar, as it focused the native field.
<label id="start-label" htmlFor="start" className="mb-1.5 block text-[13px] font-medium">Start date</label>
<DatePicker id="start" labelledBy="start-label" value={start} onChange={setStart} max={end} clearable />
```

Most blocks wrap it once, as they wrap their text inputs (a `DateField` with the label, or a
`type="date"` branch in the block's own field component that renders `DatePicker` instead of an
`<input>`). The wrapper lives outside the kit's markers, below.

## Short screens

On open, the kit measures the strip of screen the panel can paint into: the window, minus Softr's
phone tab bar below 768px, cut down by every ancestor that clips (`dpClipBox`). The strip starts at
the top of the window, so Softr's sticky top bar (56px, from 768px up) is not taken off it; an app
that shows the bar needs the one-line edit in [Re-skinning the kit](#re-skinning-the-kit). Then the
kit takes the first of items 1 to 4 that works; items 5 and 6 apply on top of whichever wins.
Nothing here is a prop.

1. **Down when it fits below, else up when it fits above.** The panel keeps 4px from the trigger
   and 8px from the strip's edges.
2. **Scroll the box that clips it.** When it fits neither way, that one box is scrolled by the
   smaller amount that makes room: up, only as far as the box is already scrolled down, or down.
   A scroll down stops at the trigger's **bottom** edge, with no 8px margin kept, so in a
   scrolling dialog body the trigger may scroll fully out of view. Closing the calendar scrolls it
   back, so focus never returns to a hidden field. The measured case is a dialog body 392px high at
   1280×600. With the margin kept, the panel ended 6.5 to 7px past the body's edge and its bottom
   padding was cut. Without it the panel fits, with 0.5 to 1px to spare. Down is the fallback
   because what hangs past a scroller's bottom extends its scroll range, and what hangs past its
   top never does.
3. **The compact grid.** If it still does not fit, the panel is measured again as a compact
   calendar: 32px days with 13px text (36px and 14px at full size), 36px header buttons and month
   pills (44px), 8px padding (12px), a 13.5rem grid (16rem), 32px Today and Clear (40px).
4. **A capped panel.** If even that does not fit (a landscape phone, 568×320), the panel is cut to
   the room there is, never below 153px (`DP_CAP_MIN`: header, footer, weekday row and one row of
   days), and its day grid scrolls inside it, with the weekday row stuck at the top. The scroll box
   has `tabIndex={-1}`: Firefox, unlike Chromium, makes a scroll box a Tab stop, and the order
   became heading, arrows, grid box, day, Today, Clear. The box carries `data-dp-lip` so the
   keep-visible scroll leaves room for the stuck row, and that row's height is read, not assumed (a
   fixed 24px was right only at a 16px root font size).
5. **On a phone, opening down: a spacer.** The fixed tab bar covers the last 57px of the window, and
   an absolute panel's bottom edge is where the page ends, so at the end of a short page the page
   could not scroll Today and Clear clear of the bar. An invisible spacer under the panel (absolute,
   `aria-hidden`, `pointer-events-none`, 1px wide, 65px high: the bar plus the 8px edge) gives the
   page that room. It is not added when the panel opens up or sits in a scrolling box.
6. **A trigger under the tab bar.** Keyboard focus can leave the trigger there, and a turned phone
   can move it. A panel opening up from it is lifted until it ends 8px above the bar, not 2.5px
   inside it.

A window resize (a turned tablet or phone) places the open panel again from the full calendar. It
moves the panel and scrolls no box. The focused day is kept in view the same way as the panel:
scroll the one clipping box, never `scrollIntoView` (it scrolls every ancestor, the page included),
from a `setTimeout` (Hard Constraint 17), in up to three passes, because WebKit moves the body's
scroll when the month grid replaces the day grid.

**Every programmatic scroll says `behavior: "instant"`.** Softr sets `html { scroll-behavior:
smooth }`. The window rule, and why a smooth scroll breaks code that scrolls and then measures, are in
[common-patterns.md → Clear Softr's sticky bars](common-patterns.md#clear-softrs-sticky-bars). The kit
scrolls, measures, then scrolls again, so with smooth scrolling it measured mid-animation and the
calendar landed outside a landscape phone's strip. What this kit adds: the property is per scroll
container, so a box that has it animates writes to its `scrollTop` too. Use
`el.scrollBy({ top, behavior: "instant" })` for boxes as well as the window. In a stress run with
`scroll-behavior: smooth` on every box, fixing only the window calls left 4 of 6 dialog cases
failing. The kit calls no `scrollIntoView` or `scrollTo`, and every `focus()` passes `preventScroll`.
Block code that scrolls and then measures needs the same.

## The kit between markers

A Vibe block is one file and cannot import another (Hard Constraint 22), so every block that uses
the picker carries its own copy. Copies that are edited in place drift: a fix lands in the block
that showed the bug and in no other. So the copy is never edited in a block. The convention:

1. **One kit file in the project** holds the component, e.g. `Assets/Softr App/Shared/DatePicker.tsx`.
   It is the only place the component is edited.
2. **Each block pastes it verbatim, at module scope, between two marker lines.** The start line names
   the kit file and the first 12 hex of its sha256. That is the sha of the kit file the project keeps,
   whatever that file holds: saved unchanged, the kit below gives the sha in the example, and a
   project that re-skins it gets another number.

   ```tsx
   // ===== DatePicker: verbatim copy of Shared/DatePicker.tsx sha256 3bb0cdae9c91 - edit there, not here =====
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
   carries without diffing 800 lines.

**The hash method.** The marker's sha is the sha256 of the kit file's bytes with the final newline
counted (`shasum -a 256 Shared/DatePicker.tsx`, first 12 hex). The text between a block's markers
is those same bytes: every line after the start marker, through the newline that ends the last kit
line. Cut the region without that final newline and it hashes to another number, so a region hash
quoted without its method cannot be compared with anything. To hash a block's region by hand (a
block read back from Softr, say), print the lines between the markers, newline included:

```bash
awk '/^\/\/ ===== DatePicker: verbatim/{f=1;next} /^\/\/ ===== \/DatePicker =====/{f=0} f' block.jsx | shasum -a 256
```

It prints the kit file's full sha256 when the region is current. `kit-sync.py` refuses a kit file
that does not end in a newline, because the end marker would then join its last line.

`kit-sync.py` (stdlib Python, keep it beside the kit file; any component can use it — the first
argument is the marker name):

```python
#!/usr/bin/env python3
"""Keep a shared component pasted verbatim between marker lines in every block.

  cd "Assets/Softr App"
  python3 Shared/kit-sync.py check DatePicker Shared/DatePicker.tsx */*.jsx
  python3 Shared/kit-sync.py sync  DatePicker Shared/DatePicker.tsx */*.jsx

The kit's markers in a block (the start line names the kit file and the first 12 hex of its sha256):
  // ===== DatePicker: verbatim copy of Shared/DatePicker.tsx sha256 3bb0cdae9c91 - edit there, not here =====
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
skipped. Run again on 2026-10-08 against the kit below: `check` flagged a block carrying an old sha,
`sync` rewrote it, and the awk command above then printed the kit file's sha256 for its region.

The same convention fits any shared component, the Combo in
[searchable-dropdown.md](searchable-dropdown.md) included, whose "keep one canonical copy and port
changes from there" it makes mechanical.

It also fits shared text. Hard Constraint 22 asks that text which must match across blocks (a
definitions paragraph) be diffed word for word before a push. Markers make that mechanical: the text
sits in a module-scope constant between marker lines, and `check` does the diff. Not tried for text
yet. The script compares the bytes between the markers and does not care what they hold. A helper
behind a figure that must agree across blocks can sit between markers as code, like any shared
component.

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

**2. In a short modal body, the calendar may scroll its trigger partly out of view.** The first
version scrolled the box that cuts the panel off only as far as the trigger's top, to keep the whole
field in view. In the family page's Add child modal, whose body is short and sized by its content,
that left the calendar's Today / Clear row below the body's edge, cut off. Allowing the trigger to
scroll partly away fixed it: the limit is the trigger's **bottom** edge, not its top. The second
round took the 8px margin off that limit too and added the compact and capped panels; the whole
ladder is in [Short screens](#short-screens).

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
field of a modal body (a 392px body at 1280×600), a field low in a table scroller, near the window's
right edge, at phone width (375px, above Softr's tab bar), on a 568×320 landscape phone, and at the
end of a short page on a phone. Then hit-test points on the panel through the shadow root
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
`setTimeout`. A capped panel shows only part of its day grid on open, so for it run the reach test
in [Verifying a change to the kit](#verifying-a-change-to-the-kit) instead.

**3. Escape order.** With real key presses (`ab press Escape`), in a modal with something typed in
another field and the calendar open: the first Escape closes the calendar only (the modal is open,
no discard prompt, focus is on the date field's trigger); the second Escape reaches the modal
(it closes, or asks to discard). Then the backdrop case of lesson 5, and Tab out of the open calendar
inside the modal: focus lands on the next field, not on the modal panel (lesson 6). In Firefox as
well as Chromium, the Tab order in an open calendar is the heading, Previous month, Next month, the
active day, Today, Clear; an extra stop before the day is the capped grid's scroll box
([Short screens](#short-screens), item 4).

**4. The saved value is byte-identical to the native version's.** Block saves first
([browser-checks.md → Block saves before any click, and prove it](browser-checks.md#6-block-saves-before-any-click-and-prove-it)),
pick a day, save, and read the aborted request's payload: the field holds the same string the native
field sent for that day (`"2026-10-15"`, not a timestamp). Clear sends what an emptied native field
sent, unless the block deliberately changed it (one LCDB block now saves a cleared optional date as
`null`). When you read the native field before the swap, read its `.value`: the text it shows
follows the browser's locale ([browser-checks.md → 4](browser-checks.md#4-measuring-with-eval)).

**5. Keyboard walks stop at `min` and `max`.** A start calendar whose `max` is the end date stops at
that date: PageDown lands on the cap, not a month later, and the month arrows stop with it (`min`
does the same the other way). A test that presses PageDown and expects the same day next month
fails for the wrong reason. Walk the calendar by reading the focused day's `aria-label`
(`Thursday, October 15, 2026`) after each key, and compare it with where the cap says it should
land.

**6. A save-time check the picker makes unreachable.** With `max` set to today, no click reaches a
future day, so the block's own "The date can't be in the future" message cannot be shown from the
screen. Keep the check (a draft restored from storage, or a form left open past midnight, can still
hold such a date) and prove it another way: seed a row with a future date into storage and reload,
or move the page's clock back after the form has defaulted to today. Report it as proven in the
harness, not as untested.

**7. The live block carries this kit.** Softr serves the block's `index.js` with comments stripped,
so the marker's sha is not in it. Fetch that script, not the stylesheet beside it, as in
[browser-checks.md → 2](browser-checks.md#2-session-preview-cookie-page), and count a code-only
form that differs between kits. In this kit `"instant"` appears 6 times in the served code (7 in
the source, one of them a comment) and `scrollBy(0,` never; the earlier kits had 0 and 3. Look
through the rest of the block for look-alikes first: the Combo has its own `scrollTop +=`.

## Verifying a change to the kit

A change to the kit reaches every block, so it is checked harder than one block's change. These
come from the 2026-10-08 round, where the kit was built, reviewed three times and re-run until a
three-engine matrix passed.

**The harness**

- **Give it Softr's smooth scrolling and a tab-bar stand-in**, as in
  [qa-playbook.md → A local harness](qa-playbook.md#a-local-harness). Then prove the mode is live
  with a two-line probe: right after a plain `window.scrollBy(0, 100)`, `scrollY` still reads 0;
  after `scrollBy({ top: 100, behavior: "instant" })` it reads 100. Add a stress mode with
  `scroll-behavior: smooth` on every box in the shadow root, and make the harness's own scrolls
  instant too: one `scrollTop +=` in a hit test gave false misses (29 of 49 cases until it was
  fixed, 48 after).
- **Test at the end of a short page, not only with filler below.** All 48 of the builder's cases
  had 900px of content under the field. At the bottom of a short page Today and Clear landed under the
  phone tab bar, in the old kit and the new.
- **Build the approved version into the same harness** as a second bundle, and diff the placement
  per case: panel rect, trigger rect, page scroll, direction, day size, hit count and the Escape
  result. The diff separates the intended changes (the 6.5px cut gone, the invisible 65px phone
  spacer) from regressions; 9 of 13 ordinary layouts came out identical. Key the cases on index plus
  open mode: a click-opened and a keyboard-opened case share a name and overwrite each other in a
  dict.
- **Run three engines**: Chromium, Firefox and WebKit (a small macOS WKWebView runner; see
  [qa-playbook.md → Which engine ran](qa-playbook.md#which-engine-ran)). The Firefox keyboard walk
  found the grid's Tab stop, which Chromium never shows.
- **Walk keys at root font sizes 16, 20 and 24px.** The kit sizes in rem (the panel is 18.5rem wide,
  the weekday row 1.5rem). A modal body fixed in px fails at 20 and 24 through harness geometry: the
  rem-sized header and footer push it below a 320px window. Size the harness modal in rem, or record
  those failures as a baseline.
- **Dry-run the sync** on temp copies of every block, then run the compile gate on each, before the
  real sync.

**Reach and fit**

- **A reach test holds the page still.** Open the capped panel, then sweep the grid's own scroll
  (the box marked `data-dp-lip`) in 10px instant steps. For each day, Today and Clear, hit-test two
  ways: `document.elementFromPoint` must return the block's host, not Softr's tab bar, and the
  shadow root's `elementFromPoint` must return the button. Count the days hit at open (28 of 42 in
  one case) and the days reached by scrolling the grid (42 of 42) separately, and confirm the
  page's scroll stayed 0, so the result does not borrow the page's. A test that scrolls the window
  to each day passes a panel that opened off the strip, and a count of what is visible at open
  fails a good capped panel. ArrowDown from today stays put when later days are disabled, so test
  keyboard reach upward.
- **Measure against the tab bar's top, not `innerHeight`.** Below 768px the strip ends 57px above the
  bottom of the window. In a dialog, measure the panel against the body's padding box (top +
  `clientTop` to + `clientHeight`) and the panel's own bottom padding, then hit-test points in that
  padding. At 1280×600 the spare room was 1px in one dialog and 0.5px in another, and a screenshot
  cannot tell that from a 1px fail.
- **Probe before you call a 1px miss a regression.** Chromium opens a one-row capped grid at
  `scrollTop` 63 instead of 64 (568×320, a 165px dialog body), so 1px of the active day sits behind
  the grid's edge. Any arrow key corrects it, Firefox and WebKit pass, and both earlier reworks did
  the same (the kit from before the round has no capped grid at that size): a baseline entry, not a
  finding. Firefox can leave a panel 0.4 to 0.5px past its box through scroll rounding; the judge
  allows 0.5px.

**The pipeline around it**

- **Give the component's review a time box and a way back.** The kit's builder re-ran a three-engine
  matrix for about 100 minutes while 12 blocks waited. Time-box the review, build it on the
  builder's saved results, and decide the fallback first: revert to the approved version if it does
  not pass. The final review passed in under 30 minutes.
- **Name the kit as deferred in each block check's prompt.** While the kit is under review, or after
  it fails, blocks are pushed without the new copy on purpose. Mark it deferred, not failed, as in
  [qa-playbook.md → Running QA with several agents and skeptics](qa-playbook.md#running-qa-with-several-agents-and-skeptics).

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

Also: `DP_FONT_BODY` (the trigger's value, as the block's text inputs), `DP_FONT_DISPLAY` (the
calendar) and the trigger's height and radius in `DP_TRIGGER` (match the block's inputs). The layout
constants below drive the placement arithmetic; change them with care, and re-run the short-screen
cases after any change.

| Constant | Kit value | Sets |
|---|---|---|
| `DP_PANEL_REM` | `18.5` | Panel width in rem: 296px, fits a 343px phone column |
| `DP_GAP` | `4` | Trigger to panel, px |
| `DP_EDGE` | `8` | Room kept free at the edges of the strip the panel can paint into, px |
| `DP_CAP_MIN` | `153` | The least a capped panel is cut to, px: header, footer, weekday row and one row of days |
| `DP_SOFTR_TAB_BAR` | `57` | Softr's phone tab bar below 768px, measured, px. The phone spacer is this plus `DP_EDGE` |
| `DP_DAY_FULL`, `DP_DAY_DENSE` | `h-9 w-9 text-[14px]`, `h-8 w-8 text-[13px]` | Day size at full and at compact size |

**Softr's sticky top bar.** The kit does not clear it. `dpClipBox` starts the strip at
`let top = 0;`, which suits an app with no top bar. The skill's 2.16.0 copy of the 2026-10-07 kit had
a constant, `DP_SOFTR_TOP_BAR` (`0`, or `56` for an app that shows the bar). It is gone: the
approved short-screen kit, embedded below, has no such constant, so a project that had set it to 56
loses the setting when it takes this kit. For an app with the bar, change that one line in
`dpClipBox` to `let top = phone ? 0 : 56;` (`phone` is declared just above it; the bar shows from
768px up, and a phone has the tab bar instead). Without the edit, a calendar that opens up can land
under the bar. Untested at 56; the bar heights are in
[searchable-dropdown.md](searchable-dropdown.md#the-four-things-that-will-bite-you). Make the edit in
the project's kit file, and keep it there when you take a newer copy of the kit from this page.
After a re-skin, the kit file's sha changes; sync it into every block.

## The kit file

Below is the whole kit, ready to save as the project's kit file. It is the LCDB kit approved on
2026-10-08. Its code is the approved file's, byte for byte. Only comments differ, worded to make
sense outside the project: the one name in the first comment is "LCDB", and a block label, a
style-guide file name, a place name, a colour name and a note on the top bar are replaced by plain
wording. The project's own file keeps the original comments, so its sha256 is `7766c741b271…` and
its markers carry that. The text below is 807 lines and ends with one newline. Saved as a file it
has sha256 `3bb0cdae9c911fbfc21451c05e9c0802f3fafaf6713d10e2def676da28f863ec` (`shasum -a 256`,
final newline counted; the method is under
[The kit between markers](#the-kit-between-markers)).

The approved file passed a 49-case matrix (22 at the end of a short page, 12 with the trigger under
the tab bar, 6 in a 392px dialog body, 9 at ordinary sizes) with smooth scrolling off, on for the
page, and on for every box. Chromium 149 passed 48 of 49 each time (the miss is the 1px Chromium
case in [Verifying a change to the kit](#verifying-a-change-to-the-kit)), Firefox 157 and macOS
WebKit 49 of 49, and the low-field cases 11 of 11 in Chromium and Firefox. A reviewer then
re-measured it by hand in Chromium (40 of 41) and walked the keys in Firefox. Not tested: iPhone
Safari itself (only macOS WKWebView ran), the phone spacer on an inner Softr page whose document may
not scroll, and Safari releases older than the current WKWebView's handling of `behavior: "instant"`.

<details>
<summary>DatePicker.tsx (807 lines)</summary>

```tsx
/** DatePicker — brand-styled date field for Softr Vibe Coding blocks (LCDB), replacing native
 * <input type="date">: its calendar pop-up is browser UI that no CSS reaches, so this one is drawn in the block's own
 * DOM. Paste everything below this comment at MODULE scope (never inside Block()). Built 2026-10-07; 22 checks pass
 * in a React 18.2 shadow-root harness with Tailwind v4 (Chromium 149 and macOS Firefox 157, TZ America/Los_Angeles,
 * today fixed at 2026-10-07). Fixed the same day after the rollout checks: a calendar in a short modal body may now
 * scroll its trigger partly out of view rather than cut off the Today/Clear row (closing scrolls the trigger back into
 * view), and the text size is a prop. Short screens (2026-10-08): in a scrolling box the calendar may scroll its trigger
 * out of view down to the trigger's bottom edge (no 8px margin), so a 392px dialog body holds it; where even that is
 * not enough it switches to a compact grid (32px days, 13px text), and where the compact grid does not fit either it is
 * capped at the room there is and its day grid scrolls inside it (a landscape phone, 568x320). Review fixes (2026-10-08):
 * a panel opening down on a phone carries an empty spacer below it, so the page can scroll Today and Clear clear of the
 * fixed tab bar even at the end of a short page; a panel opening up from a trigger that sits under the tab bar is lifted
 * clear of it; the capped grid is not a Tab stop (Firefox made it one); the stuck weekday row is measured, not 24px; and
 * the keep-visible scroll makes up to three passes (WebKit moves the body's scroll when the month grid replaces the day grid).
 * Smooth scroll (2026-10-08): Softr's page sets html { scroll-behavior: smooth }, which animates every scrollBy and scrollTop
 * write and restarts each from where the page is at that moment, so every scroll here says behavior: "instant".
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
 * that sizes them by named containers passes its own (e.g. "text-[16px] @min-[48rem]/page:text-[14px] ...").
 * The label's htmlFor may stay: a click on the label opens the picker, as it focuses a native date field.
 * Nothing between the field and the scroller it belongs to may clip (overflow-hidden, truncate, line-clamp): the
 * calendar is an absolute panel in the block's DOM (softr-vibe-coding references/searchable-dropdown.md, rule 1).
 */

// Brand tokens this component uses: a copy, because blocks cannot import each other (Hard Constraint 22).
// The values match the blocks' C object. Tailwind class strings repeat some as literal hex; each says which.
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
const DP_CAP_MIN = 153; // the least a capped panel is cut to: header, footer, weekday row and one row of days
const DP_SOFTR_TAB_BAR = 57; // Softr's phone tab bar, window below 768px: measured 57px (this kit assumes no sticky top bar)
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
  "mx-auto flex items-center justify-center rounded-full leading-none transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#680058]";
const DP_DAY_FULL = "h-9 w-9 text-[14px]";
const DP_DAY_DENSE = "h-8 w-8 text-[13px]"; // the compact calendar: 32px days
const DP_DAY_SELECTED = "bg-[#680058] font-semibold text-white hover:bg-[#4E0042]";
const DP_DAY_TODAY = "font-semibold text-[#680058] hover:bg-[#F3F4F6]";
const DP_DAY_IN = "text-[#030712] hover:bg-[#F3F4F6]";
const DP_DAY_OUT = "text-[#6B7280] hover:bg-[#F3F4F6]";
const DP_DAY_OFF = "cursor-default text-[#C4C8CF]";
// Months in the month / year view: same states, as 44px pills (36px in the compact calendar).
const DP_MONTH =
  "flex w-full items-center justify-center rounded-full transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#680058]";
// Month arrows: 44px targets (36px in the compact calendar). aria-disabled (not disabled), so an arrow keeps focus when
// it reaches min or max.
const DP_ICON_BTN =
  "flex items-center justify-center rounded-full transition-colors hover:bg-[#F3F4F6] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#680058] aria-disabled:cursor-default aria-disabled:opacity-35 aria-disabled:hover:bg-transparent";
// The trigger is the blocks' text input: 44px. Its text size comes from the textClass prop: by default 16px below a
// 48rem container (stops iOS zoom) and 14px from it.
// #D1D5DB = DP_C.border · #680058 = DP_C.primary (focus border and ring; kept while the calendar is open)
const DP_TRIGGER =
  "flex h-11 w-full items-center justify-between gap-2 rounded-xl border border-[#D1D5DB] bg-white px-3 text-left transition-colors focus:border-[#680058] focus:outline-none focus:ring-2 focus:ring-[#680058]/25 aria-expanded:border-[#680058] aria-expanded:ring-2 aria-expanded:ring-[#680058]/25 disabled:cursor-not-allowed disabled:opacity-60";

type DpPlace = { up: boolean; x: number; maxW: number | null; capH: number | null; pad: number; lift: number; ready: boolean };

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

// The strip of screen the panel can paint into: the window (minus Softr's phone tab bar), cut down by every ancestor
// that clips, as comboClipBox in searchable-dropdown.md. Also returns the boxes that set the top and bottom edges
// (null = the window), for the nudge in dpPlace.
function dpClipBox(node: HTMLElement) {
  const phone = window.innerWidth < 768;
  let top = 0;
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
  return { top, bottom, left, right, topEl, bottomEl, phone };
}

// Can this edge box (null = the window) be scrolled, and how far is it scrolled now?
function dpScrollable(el: HTMLElement | null) {
  return el
    ? /(auto|scroll)/.test(window.getComputedStyle(el).overflowY)
    : window.getComputedStyle(document.documentElement).overflowY !== "hidden";
}

// focus({ preventScroll: true }) does not reveal what it focuses. When the active day sits past the edge of the box
// that clips it (a short modal body), scroll that one box just far enough; never scrollIntoView, which scrolls every
// ancestor including the page. With a scroll box inside another (the capped day grid in a modal body) one pass may not
// be enough: WebKit resets the grid's scroll and moves the body's when the day grid becomes the month grid, so the box
// that cuts the element off nearest changes after the first scroll. Measure and scroll again, up to three passes.
function dpKeepVisible(el: HTMLElement) {
  for (let pass = 0; pass < 3; pass++) {
    const clip = dpClipBox(el);
    const r = el.getBoundingClientRect();
    // The stuck weekday row of a capped day grid, as tall as it is drawn (it follows the root font size).
    const lipRow = clip.topEl?.hasAttribute("data-dp-lip") ? clip.topEl.querySelector("th") : null;
    const lip = lipRow ? lipRow.getBoundingClientRect().height : 0;
    // The margin shrinks when the box is barely taller than the element and that row: the element must still fit.
    const m = Math.max(0, Math.min(DP_EDGE, (clip.bottom - clip.top - lip - r.height) / 2));
    if (r.bottom > clip.bottom - m && dpScrollable(clip.bottomEl)) {
      const by = r.bottom - (clip.bottom - m);
      // Instant, not the page's smooth scroll: the next pass measures where this one landed.
      if (clip.bottomEl) clip.bottomEl.scrollBy({ top: by, behavior: "instant" });
      else window.scrollBy({ top: by, behavior: "instant" });
    } else if (r.top < clip.top + m + lip && dpScrollable(clip.topEl)) {
      const by = clip.top + m + lip - r.top;
      if (clip.topEl) clip.topEl.scrollBy({ top: -by, behavior: "instant" });
      else window.scrollBy({ top: -by, behavior: "instant" });
    } else {
      return; // inside every box, or nothing left that can scroll
    }
  }
}

// Where a panel of height h goes. Down when it fits below, else up when it fits above. When it fits neither way (a short
// modal body, a small window), the box that cuts it off is nudged by the smaller scroll that makes it fit with the
// trigger still in view: up into room above (only as far as that box is scrolled down), or down into room below. When
// no nudge makes it fit: down, scrolled as far as the trigger allows, so the rest can be scrolled to (what hangs past
// a scroller's bottom extends its scroll range; past its top it never does); with no scroller at all, the larger side.
// fit says whether the whole panel then lies inside the box (the 8px margin may be spent when scrolling down).
function dpFit(clip: ReturnType<typeof dpClipBox>, r: DOMRect, h: number) {
  const below = clip.bottom - r.bottom - DP_GAP - DP_EDGE;
  // Up, the panel ends DP_GAP above the trigger, but never under the strip's bottom edge: a trigger can sit under the phone
  // tab bar (keyboard focus leaves it there, a turned phone moves it), and dpPlace then lifts the panel clear of the bar.
  const above = Math.min(r.top - DP_GAP, clip.bottom - DP_EDGE) - clip.top - DP_EDGE;
  let up = below < h && above >= h;
  let scroller: HTMLElement | Window | null = null;
  let scrollBy = 0; // positive scrolls down (the content moves up)
  let fit = true;
  if (below < h && above < h) {
    const needUp = h - above; // scroll the top box back this far to make room above
    const needDown = h - below; // scroll the bottom box on this far to make room below
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
      // Down to the trigger's bottom edge, with no margin: in a short modal body the whole calendar then fits, and the
      // trigger scrolls out of view (closing brings it back). The 8px margin below the panel is spent first.
      scrollBy = Math.max(0, Math.min(needDown, r.bottom - clip.top));
      fit = scrollBy + 0.5 >= needDown - DP_EDGE;
    } else {
      up = above > below;
      fit = false;
    }
  }
  return { up, scroller, scrollBy, fit, below, above };
}

// Where the panel goes (dpFit), and how tall it may be. canCap: the compact calendar is already on show, so a panel that
// still fits nowhere is cut to the most the box can show once scrolled to it (where nothing scrolls: to the larger
// side), never below DP_CAP_MIN, and its day grid scrolls inside it. Horizontally it hangs from the trigger's left edge
// and shifts left to stay inside the strip.
function dpPlace(wrapper: HTMLElement, panelH: number, canCap: boolean) {
  const clip = dpClipBox(wrapper);
  const r = wrapper.getBoundingClientRect();
  let a = dpFit(clip, r, panelH);
  let capH: number | null = null;
  if (!a.fit && canCap) {
    capH = Math.max(DP_CAP_MIN, Math.min(panelH, clip.bottom - clip.top - 2 * DP_EDGE - DP_GAP));
    a = dpFit(clip, r, capH);
    if (!a.fit) {
      capH = Math.max(DP_CAP_MIN, Math.min(capH, Math.max(a.below, a.above)));
      a = dpFit(clip, r, capH);
    }
    if (capH >= panelH) capH = null;
  }
  const remPx = parseFloat(window.getComputedStyle(document.documentElement).fontSize) || 16;
  const room = clip.right - clip.left - 2 * DP_EDGE;
  const w = Math.min(DP_PANEL_REM * remPx, Math.max(256, room));
  let x = 0;
  if (r.left + w > clip.right - DP_EDGE) x = clip.right - DP_EDGE - w - r.left;
  if (r.left + x < clip.left + DP_EDGE) x = clip.left + DP_EDGE - r.left;
  // Up from a trigger that sits within DP_GAP + DP_EDGE of the strip's bottom edge or past it (under the phone tab bar): the
  // panel is lifted until it ends DP_EDGE above that edge. dpFit has counted the room above from there.
  const lift = a.up ? Math.max(0, Math.ceil(r.top - DP_GAP - (clip.bottom - DP_EDGE))) : 0;
  return {
    up: a.up,
    x: Math.round(x),
    maxW: w < DP_PANEL_REM * remPx ? Math.floor(w) : null,
    scroller: a.scroller,
    scrollBy: a.scrollBy,
    fit: a.fit,
    capH,
    lift,
    // Down into the window on a phone: the page only scrolls as far as its own content, and an absolute panel reaches the
    // document's end at its own bottom edge, where the fixed tab bar covers the last 57px (Today and Clear). This much
    // empty room below the panel lets the page scroll it clear of the bar. Up, or in a scrolling box: not needed.
    pad: !a.up && !clip.bottomEl && clip.phone ? DP_SOFTR_TAB_BAR + DP_EDGE : 0,
  };
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
  const [place, setPlace] = useState<DpPlace>({ up: false, x: 0, maxW: null, capH: null, pad: 0, lift: 0, ready: false });
  const [dense, setDense] = useState(false); // the compact calendar: for a strip too short for the full one
  const [tick, setTick] = useState(0); // a window resize starts the placement over, from the full calendar
  const resized = useRef(false); // that placement moves the panel only; it scrolls no box

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
    setPlace({ up: false, x: 0, maxW: null, capH: null, pad: 0, lift: 0, ready: false });
    setDense(false);
    focusPending.current = true;
    setOpen(true);
  }
  function closePicker(refocus: boolean) {
    setOpen(false);
    setView("days");
    focusPending.current = false;
    if (refocus) {
      triggerRef.current?.focus({ preventScroll: true });
      // The open calendar may have scrolled its box until the trigger sat partly out of view: bring it back once the
      // panel is gone, so focus never lands on a hidden trigger. Only this one box scrolls (Hard Constraint 17).
      window.setTimeout(() => {
        const t = triggerRef.current;
        if (t && t.isConnected) dpKeepVisible(t);
      }, 0);
    }
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

  // Place the panel before it paints: measured hidden, then shown up or down, shifted to stay inside the strip. A panel
  // that fits nowhere is measured again as the compact calendar; one that still fits nowhere is capped (dpPlace).
  useLayoutEffect(() => {
    if (!open) return;
    const wrap = rootRef.current;
    const panel = panelRef.current;
    if (!wrap || !panel) return;
    const p = dpPlace(wrap, panel.offsetHeight, dense);
    if (!p.fit && !dense) {
      setDense(true);
      return;
    }
    setPlace({ up: p.up, x: p.x, maxW: p.maxW, capH: p.capH, pad: p.pad, lift: p.lift, ready: true });
    const moveOnly = resized.current;
    resized.current = false;
    if (!moveOnly && p.scroller && p.scrollBy !== 0) {
      const sc = p.scroller;
      const by = p.scrollBy;
      // Hard Constraint 17: programmatic scrolls go through setTimeout. Only this one box scrolls (no scrollIntoView).
      window.setTimeout(() => {
        // Instant: dpKeepVisible measures next, and a smooth scroll would still be moving.
        if (sc === window) window.scrollBy({ top: by, behavior: "instant" });
        else (sc as HTMLElement).scrollBy({ top: by, behavior: "instant" });
      }, 0);
    }
  }, [open, dense, tick]);

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

  // A window resize (a turned tablet) re-places the open panel, from the full calendar again.
  useEffect(() => {
    if (!open) return;
    const onResize = () => {
      resized.current = true;
      setDense(false);
      setPlace((p) => ({ ...p, capH: null }));
      setTick((n) => n + 1);
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
  const capped = place.capH !== null; // the compact calendar, cut to the room there is: its day grid scrolls

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
          className={`absolute z-40 w-[18.5rem] rounded-xl border bg-white outline-none ${dense ? "p-2" : "p-3"} ${
            capped ? "flex flex-col" : ""
          } ${place.up ? "bottom-full mb-1" : "top-full mt-1"}`}
          style={{
            left: place.x,
            maxWidth: place.maxW ?? undefined,
            maxHeight: place.capH ?? undefined,
            marginBottom: place.up && place.lift ? DP_GAP + place.lift : undefined,
            visibility: place.ready ? "visible" : "hidden",
            borderColor: DP_C.border,
            boxShadow: DP_SHADOW_MENU,
            fontFamily: DP_FONT_DISPLAY,
            color: DP_C.ink,
          }}
        >
          {place.pad ? (
            <div aria-hidden="true" className="pointer-events-none absolute left-0 top-full w-px" style={{ height: place.pad }} />
          ) : null}
          <div className="flex shrink-0 items-center justify-between">
            <button
              type="button"
              aria-label={view === "days" ? `${heading}, choose month and year` : `${heading}, back to days`}
              onClick={() => {
                focusPending.current = true;
                setView(view === "days" ? "months" : "days");
              }}
              // #F3F4F6 = DP_C.canvas · #680058 = DP_C.primary
              className={`-ml-1 inline-flex ${
                dense ? "h-9 text-[14px]" : "h-11 text-[15px]"
              } items-center gap-1 rounded-full pl-2.5 pr-2 font-semibold transition-colors hover:bg-[#F3F4F6] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#680058]`}
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
                className={`${DP_ICON_BTN} ${dense ? "h-9 w-9" : "h-11 w-11"}`}
              >
                <ChevronLeft className="h-[18px] w-[18px]" aria-hidden="true" />
              </button>
              <button
                type="button"
                aria-label={view === "days" ? "Next month" : "Next year"}
                aria-disabled={nextOff || undefined}
                onClick={() => step(1)}
                className={`${DP_ICON_BTN} ${dense ? "h-9 w-9" : "h-11 w-11"}`}
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
          <div
            className={
              !dense
                ? "mt-1 h-[16rem]"
                : capped
                  ? "mt-0.5 min-h-0 shrink overflow-y-auto overscroll-contain"
                  : "mt-0.5 h-[13.5rem]"
            }
            // A scroll box is a Tab stop in Firefox (not in Chromium): tabIndex -1 keeps it out of the order. Its mousedown is
            // already cancelled by the panel, so a press on it takes no focus either.
            tabIndex={capped ? -1 : undefined}
            data-dp-lip={capped && view === "days" ? "" : undefined}
          >
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
                        className={`${dense ? "h-6" : "h-7"} p-0 text-center text-[12px] font-medium ${
                          capped ? "sticky top-0 z-[1] bg-white" : ""
                        }`}
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
                          <td key={i} role="gridcell" aria-selected={isSel} className={dense ? "p-0 text-center" : "p-0 py-px text-center"}>
                            <button
                              type="button"
                              tabIndex={active ? 0 : -1}
                              data-dp-active={active ? "true" : undefined}
                              disabled={!ok}
                              aria-label={format(d, "EEEE, MMMM d, yyyy")}
                              aria-current={isToday ? "date" : undefined}
                              onClick={() => pick(d)}
                              className={`${DP_DAY} ${dense ? DP_DAY_DENSE : DP_DAY_FULL} ${tone}`}
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
                className={`flex flex-col justify-center ${dense ? "gap-2" : "gap-3"} ${capped ? "h-[13.5rem]" : "h-full"}`}
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
                            className={`${DP_MONTH} ${dense ? "h-9 text-[13px]" : "h-11 text-[14px]"} ${tone}`}
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

          <div
            className={`${dense ? "mt-1 pt-1" : "mt-2 pt-2"} flex shrink-0 items-center justify-between border-t`}
            style={{ borderColor: DP_C.divider }}
          >
            <button
              type="button"
              disabled={todayOff}
              onClick={() => pick(today)}
              // #680058 = DP_C.primary · #F5EAF3 = DP_C.primaryTint
              className={`-ml-1 inline-flex ${
                dense ? "h-8 text-[13px]" : "h-10 text-[14px]"
              } items-center rounded-full px-3 font-semibold text-[#680058] transition-colors hover:bg-[#F5EAF3] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#680058] disabled:cursor-default disabled:opacity-40 disabled:hover:bg-transparent`}
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
                className={`-mr-1 inline-flex ${
                  dense ? "h-8 text-[13px]" : "h-10 text-[14px]"
                } items-center rounded-full px-3 font-medium text-[#6B7280] transition-colors hover:bg-[#F3F4F6] hover:text-[#030712] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#680058]`}
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
- [ ] Short screens: the whole calendar, or every day by scrolling a capped grid, plus Today and Clear, can be hit in a 392px dialog body at 1280×600, on a 568×320 landscape phone and at the end of a short page at 375×812
- [ ] Trigger text size matches the block's inputs (`textClass` where containers are named)
- [ ] Escape closes only the calendar; the second Escape reaches the modal
- [ ] Backdrop click with a calendar open: closes only the calendar, or asks to discard
- [ ] A modal's focus fix-up deferred with `setTimeout(…, 0)`; Tab out of the calendar reaches the next field
- [ ] Values are `"yyyy-MM-dd"` strings; compared as strings; displayed through a local date
- [ ] The saved payload is the same string the native field sent
- [ ] A save-time check that `max` makes unreachable (a future date) is proven another way
- [ ] The served block carries the current kit: a code-only count, not the marker

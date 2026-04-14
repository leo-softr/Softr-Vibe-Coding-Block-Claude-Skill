# Softr Vibe Coding — UI/UX Design Guidelines

These guidelines apply to every Softr Vibe Coding block. Follow them when building any user-facing component.

## Table of Contents

1. [Core Philosophy: Don't Make Me Think](#1-core-philosophy-dont-make-me-think)
2. [Design Direction Before Code](#2-design-direction-before-code)
3. [Visibility of Interactive Elements](#3-visibility-of-interactive-elements)
4. [Visual Hierarchy](#4-visual-hierarchy)
5. [Color Usage](#5-color-usage)
6. [Typography](#6-typography)
7. [Spacing: The 4pt Scale](#7-spacing-the-4pt-scale)
8. [Cards: Use with Restraint](#8-cards-use-with-restraint)
9. [Motion Design](#9-motion-design)
10. [Buttons and Interactive Controls](#10-buttons-and-interactive-controls)
11. [Forms and Input Fields](#11-forms-and-input-fields)
12. [Loading States](#12-loading-states)
13. [Empty States](#13-empty-states)
14. [Feedback and Microinteractions](#14-feedback-and-microinteractions)
15. [Error Prevention and Destructive Actions](#15-error-prevention-and-destructive-actions)
16. [Progressive Disclosure](#16-progressive-disclosure)
17. [Navigation and Orientation](#17-navigation-and-orientation)
18. [Data Tables and Lists](#18-data-tables-and-lists)
19. [KPI / Metric Cards and Dashboards](#19-kpi--metric-cards-and-dashboards)
20. [Accessibility Baseline](#20-accessibility-baseline)
21. [Mobile-First Responsive Design](#21-mobile-first-responsive-design)
22. [UX Writing (Microcopy)](#22-ux-writing-microcopy)
23. [Conventions and Consistency](#23-conventions-and-consistency)
24. [Calculator and Utility Tool Polish](#24-calculator-and-utility-tool-polish)
25. [AI Slop Anti-Pattern Checklist](#25-ai-slop-anti-pattern-checklist)
26. [Finishing Touches](#26-finishing-touches)
- [Appendix A: Quick Reference](#appendix-a-quick-reference)
- [Appendix B: Motion and Spacing Tokens](#appendix-b-motion-and-spacing-tokens)
- [Appendix C: Design Brief Template](#appendix-c-design-brief-template)

---

## 1. Core Philosophy: Don't Make Me Think

The overriding principle of every interface is **eliminate question marks**. Every element on a screen should be self-evident — the user should never have to wonder what something is, whether it is clickable, or what will happen if they interact with it.

**Apply this by asking:** *"Would a first-time user of this interface understand what to do within 3 seconds, without reading any instructions?"*

Key implications:
- Use clear, literal labels. Avoid clever or internal names. "First Name" beats "Display Identifier". "Save" beats "Commit Changes."
- Every interactive element must *look interactive*. Buttons must look like buttons. Links must look like links.
- If something is not clickable, it must not look clickable.
- The most important action on any screen should be the most visually prominent element.

---

## 2. Design Direction Before Code

Most AI-generated UIs fail because of skipped thinking, not bad code. Jumping to "here's a card grid" without asking "what is the user trying to accomplish?" produces generic output every time.

**Before writing any block, establish:**
- **Target audience**: Who uses this? Role, context, frequency, emotional state when they arrive.
- **Primary user action**: The single most important thing a user should do or understand.
- **Brand personality**: Pick a clear direction — 3 concrete brand voice words (NOT "modern" or "elegant"; those are dead categories). Think of the brand as a *physical object*: a museum exhibit caption, a hand-painted shop sign, a 1970s mainframe manual.
- **Anti-goals**: What should this NOT be? What's the biggest risk of getting this wrong?

This context cannot be inferred from the codebase. Ask the user.

---

## 3. Visibility of Interactive Elements

**Never hide interactive controls behind hover-only states for primary or frequently used actions.**

A faint pencil icon that only appears on hover is one of the most common UX failures. Users who do not know to hover will never discover the action.

### Rules:
- **Always-visible edit triggers:** Show edit icons permanently visible (not only on hover). Use `text-muted-foreground` for subtlety, but always render in the DOM.
- **Hover enhancement, not hover-only reveal:** Enhance on hover (e.g., increase opacity from 70% to 100%, change to `text-primary`), but the control must be visible *before* hover.
- **Touch devices have no hover.** Any action hidden behind a hover state is invisible to all mobile and tablet users.

### Correct pattern (editable field):
```jsx
<div className="flex items-center gap-2 group">
  <span className="text-foreground">{value}</span>
  <button
    onClick={function() { setEditing(true); }}
    className="text-muted-foreground hover:text-primary transition-colors"
    aria-label="Edit field"
  >
    <Pencil className="w-4 h-4" />
  </button>
</div>
```

### Editing state:
```jsx
<div className="flex items-center gap-2">
  <Input value={draft} onChange={function(e) { setDraft(e.target.value); }} autoFocus />
  <button onClick={handleSave} aria-label="Save"><Check className="w-4 h-4 text-primary" /></button>
  <button onClick={handleCancel} aria-label="Cancel"><X className="w-4 h-4 text-muted-foreground" /></button>
</div>
```

---

## 4. Visual Hierarchy

Every screen must have a clear visual hierarchy that tells the user what is most important without thinking.

### Hierarchy tools (use multiple together):

| Tool | Strong Hierarchy | Weak Hierarchy |
|---|---|---|
| **Size** | 3:1 ratio or more between heading and body | < 2:1 ratio — looks flat |
| **Weight** | Bold vs Regular with clear contrast | Medium vs Regular — indistinguishable |
| **Color** | High contrast foreground vs muted | Similar tones throughout |
| **Position** | Critical info top-left (LTR), secondary below | Everything center-aligned |
| **Space** | Surrounded by generous white space | Crowded, uniform padding |

### The Squint Test

Blur your eyes or apply a blur filter to a screenshot. Can you still identify the most important element? The second most important? Clear groupings? If everything looks the same weight blurred, there is a hierarchy problem.

### Rules:
- **No flat design:** Not everything can be the same visual weight. Pick one primary action per screen and make it stand out.
- **Limit contrast levels to 3:** Primary content, secondary content, disabled/muted. More than 3 creates visual chaos.
- **Bold only key values**, not labels. Users scan for numbers and data, not label text.
- Group related elements visually (`Card` wrappers, `gap` spacing, or `Separator` components). Spatial proximity signals relationship.
- The most critical information belongs in the **top-left quadrant** of the screen where the eye naturally lands.

---

## 5. Color Usage

### The 60-30-10 Rule (Visual Weight, Not Pixel Count)

| Proportion | Role | Tailwind tokens |
|---|---|---|
| **60%** | Dominant / Background | `bg-background`, `bg-card` |
| **30%** | Secondary / Structure | `bg-muted`, `bg-secondary`, navigation, sidebars |
| **10%** | Accent / CTAs / Highlights | `bg-primary`, `text-primary`, `bg-destructive` |

Accents work *because* they are rare. Overuse kills their power.

### Tinted Neutrals

When using custom colors via inline styles, avoid pure gray. Add a tiny tint toward the brand hue for subconscious cohesion:
- Pure gray feels lifeless next to brand color
- Tint neutrals very slightly toward the brand hue (e.g., a blue-brand app gets slightly blue-tinted grays)
- The tint should be imperceptible consciously but create warmth

### Dark Mode Considerations

When building blocks with dark backgrounds:
- Depth comes from **surface lightness**, not shadow. Higher elevations = slightly lighter surfaces.
- Reduce body text font weight slightly (light text on dark reads heavier).
- Reduce chroma in colors at extreme lightness to avoid garish tones.
- Test all status colors on dark backgrounds — gray text washes out on color.

### Color Rules:
- **Reserve `bg-primary` for the single most important action per screen.**
- **Use `text-muted-foreground`** for secondary labels, placeholders, helper text, timestamps.
- **Never communicate information by color alone.** Always pair with an icon, label, or shape.
- **Status badges**: distinct background + matching text — success (green), warning (amber), error (destructive), info (blue).

### Absolute Color Bans (AI Slop Tells)
- **DO NOT** use cyan-on-dark, purple-to-blue gradients, or neon accents on dark backgrounds.
- **DO NOT** use pure black (`#000`) or pure white (`#fff`) for large areas.
- **DO NOT** use dark backgrounds with colored `box-shadow` glows.
- **DO NOT** use gradient text (`background-clip: text` with a gradient).
- **DO NOT** use gray text on any colored background — use a darker shade of the background hue instead.

---

## 6. Typography

### Type Scale:

| Role | Tailwind class | Min size | Use |
|---|---|---|---|
| Page/block title | `text-2xl` | 22-24px | Single H1 per screen |
| Section headings | `text-lg` / `text-xl` | 18-20px | Major sections |
| Body / default | `text-base` | 16px | Primary readable content |
| Secondary / helper | `text-sm` | 14px | Labels, descriptions |
| Captions / badges | `text-xs` | 12px | Badges, footnotes only |

Aim for at least **1.25x ratio** between adjacent scale steps. Sizes only 1-2px apart create muddy hierarchy.

### Rules:
- **Never go below 14px** for readable content (12px only for badges, footnotes).
- **Line height:** `leading-relaxed` (1.625) for body paragraphs. `leading-snug` for headings.
- **Max line length:** 60-75 characters. Use `max-w-prose` or `max-w-xl`.
- **Left-align body text.** Centered text is harder to scan for multi-line content.
- Use `font-medium` or `font-semibold` for label emphasis. Do not bold everything.
- Use `text-foreground`, not pure black. The theme token is calibrated for comfortable contrast.
- **Use tabular numbers** in data tables for column alignment: add `style={{ fontVariantNumeric: "tabular-nums" }}` to numeric cells.

### Typography Anti-Patterns:
- **DO NOT** use monospace typography as lazy shorthand for "technical/developer" vibes.
- **DO NOT** place large rounded icons above every heading — they rarely add value and look templated.
- **DO NOT** set long body passages in uppercase. Reserve all-caps for short labels.
- **DO NOT** use only one font family with no hierarchy contrast.

---

## 7. Spacing: The 4pt Scale

All spacing uses **multiples of 4px**. The critical step that pure 8pt systems miss is **12px** — you frequently need it between 8 and 16.

### Standard values:

| Value | Use |
|---|---|
| `p-1` / `gap-1` (4px) | Micro-spacing (icon + badge) |
| `p-2` / `gap-2` (8px) | Tight internal padding (icon buttons, badges) |
| `p-3` (12px) | Compact form field padding |
| `p-4` / `gap-4` (16px) | Standard card padding, button padding |
| `p-6` / `gap-6` (24px) | Section padding, card body |
| `p-8` (32px) | Large section gaps |
| `p-12` (48px) | Major page section separators |

### Rules:
- **Vary spacing for hierarchy.** A heading with extra space above reads as more important. Uniform padding everywhere feels monotonous.
- **Internal spacing <= external spacing:** Padding *inside* a component must be smaller than the margin *between* components.
- **Button height:** 40px (`h-10`) or 48px (`h-12`) — touch-friendly.
- **Never use arbitrary values** like `p-[13px]`. Always use the Tailwind scale.
- **Generous whitespace** reduces cognitive load — it is not wasted space.

### Depth and Elevation:
- Use semantic z-index levels: dropdown (100) > sticky (200) > modal-backdrop (300) > modal (400) > toast (500) > tooltip (600).
- Shadows should be subtle. If you can clearly see it, it is probably too strong.

---

## 8. Cards: Use with Restraint

Cards are powerful containers but easily overused. Wrapping everything in cards ("cardocalypse") flattens hierarchy.

### When to use cards:
- Content is truly distinct and actionable
- Items need visual comparison in a grid
- Content needs clear interaction boundaries (clickable surfaces)

### When NOT to use cards:
- Spacing and alignment already create sufficient grouping
- Content is inside another card (never nest cards inside cards)
- Identical card grids repeated endlessly (icon + heading + text) — this is a recognizable AI template

### Card anatomy:
1. **Header:** `CardTitle` + optional `CardDescription` + optional right-aligned action
2. **Body:** Primary content with clear visual hierarchy
3. **Footer (optional):** Secondary actions or metadata

---

## 9. Motion Design

### The 100/300/500 Rule

Timing matters more than easing:

| Duration | Use Case |
|---|---|
| **100-150ms** | Instant feedback: button press, toggle, color change |
| **200-300ms** | State changes: menu open, tooltip, hover states |
| **300-500ms** | Layout changes: accordion, modal, drawer |
| **500-800ms** | Entrance animations: page load, hero reveals |

Exit animations should be ~75% of enter duration.

### Easing

**Do not use the generic `ease` curve.** Use purpose-specific curves:

| Curve | Use For | CSS |
|---|---|---|
| **ease-out** | Elements entering view | `cubic-bezier(0.16, 1, 0.3, 1)` |
| **ease-in** | Elements leaving view | `cubic-bezier(0.7, 0, 0.84, 0)` |
| **ease-in-out** | State toggles (expand/collapse) | `cubic-bezier(0.65, 0, 0.35, 1)` |

Default recommendation: **ease-out-expo** — snappy, confident, feels natural.

### What to Animate

**Only animate `transform` and `opacity`** — everything else causes layout recalculation and dropped frames. For height animations (accordions), use `grid-template-rows: 0fr -> 1fr` instead of animating `height` directly.

### Staggered List Animations

Cap total stagger time — 10 items x 50ms = 500ms total. For many items, reduce per-item delay or cap the staggered count.

### Reduced Motion (Required)

Vestibular disorders affect ~35% of adults over 40. Always respect `prefers-reduced-motion`:
- Replace motion with crossfade or instant transitions
- Never remove feedback entirely — just the movement

### Motion Anti-Patterns:
- **DO NOT** use bounce or elastic easing. They feel amateurish and dated.
- **DO NOT** animate layout properties (width, height, padding, margin) — use transform.
- **DO NOT** use > 500ms for standard UI feedback.
- **DO NOT** add `will-change` to everything preemptively.

---

## 10. Buttons and Interactive Controls

### Button states (all required):

| State | Purpose | Implementation |
|---|---|---|
| **Default** | Ready to use | Standard `Button` component |
| **Hover** | Cursor over it | Handled by shadcn `Button` |
| **Focus** | Keyboard-selected | `focus-visible:ring-2` — never remove |
| **Active** | Being pressed | Pressed in, darker |
| **Loading** | Action in progress | Replace label with `<Spinner />` + disable |
| **Disabled** | Not available | `disabled` prop — `opacity-50` |
| **Success** | Completed | Brief `Check` icon swap, 1-2 seconds |
| **Destructive** | Dangerous action | `variant="destructive"` — always with confirmation |

### Button Label Formula:

| Bad | Good | Why |
|---|---|---|
| OK | Save changes | Says what will happen |
| Submit | Create account | Outcome-focused |
| Yes | Delete message | Confirms the action |
| Cancel | Keep editing | Clarifies what "cancel" means |
| Click here | Download PDF | Describes the destination |

### Rules:
- **Primary action = one per screen.** Use `variant="default"` only for the primary CTA.
- **Touch target minimum:** 44x44px. Use `min-h-[44px] min-w-[44px]` for icon-only buttons.
- **Icon-only buttons must have `aria-label`.**
- **Never disable without explaining why.** Show tooltip or helper text.
- **Destructive buttons** must: use `variant="destructive"`, be positioned away from primary actions, trigger confirmation for irreversible actions.
- **DO NOT make every button primary.** Use ghost, outline, and secondary styles for hierarchy.

---

## 11. Forms and Input Fields

### Label placement:
- **Always place labels above input fields**, never inside (placeholder only).
- Use `<label>` with `htmlFor` matching the input `id`.
- **Placeholder text** should be an example value, not a repeated label: "you@company.com" not "Enter email".

### Validation:
- **Validate on blur**, not on every keystroke.
- **Error messages:** Always inline, directly below the field. Write as instruction: "Enter a valid email address" not "Invalid email."
- **Success states:** Show green check icon on validated fields.
- **Required fields:** Mark explicitly.

### Error Message Formula:

| Situation | Template |
|---|---|
| Format error | "[Field] needs to be [format]. Example: [example]" |
| Missing required | "Please enter [what's missing]" |
| Permission denied | "You don't have access to [thing]. [What to do instead]" |
| Network error | "We couldn't reach [thing]. Check your connection and [action]." |
| Server error | "Something went wrong on our end. [Alternative action]" |

**Never blame the user.** "Please enter a date in MM/DD/YYYY format" not "You entered an invalid date."

### Layout:
- **Single-column forms** are easier to complete than multi-column.
- **Group related fields** under labeled sections.
- **Submit button** at the bottom, full-width or right-aligned, primary variant.

---

## 12. Loading States

| Duration | Recommended Pattern |
|---|---|
| < 300ms | No indicator needed (feels instant) |
| 300ms - 1s | `<Spinner />` component inline |
| 1s - 3s | Skeleton screen (preferred) |
| > 3s | Progress indicator + cancel option |

### Skeleton screens:
- Use `<Skeleton />` from shadcn/ui matching the final layout shape.
- Pulsing animation is included by default.
- Replace content progressively as data arrives.

### Perceived Performance:
- **Optimistic UI**: Update the interface immediately, handle failures gracefully. Use for low-stakes actions (likes, filters); avoid for payments or destructive operations.
- **Skeleton over spinner** for data loading — it previews content shape and feels faster.

### Implementation:
- Check `status === 'pending'` and render skeleton.
- Check `status === 'error'` and render error state with retry.
- Never render an empty block.

---

## 13. Empty States

Empty states are a critical UX moment — not an afterthought. They are onboarding opportunities.

### Required structure:
1. **Icon or illustration** relevant to the content type
2. **Clear heading**: "No records yet" or "No results found"
3. **Explanation sentence**: "You haven't added any items yet."
4. **Primary CTA**: `<Button>Add your first item</Button>`

### Rules:
- Do not say "No data" — be specific and human. "You don't have any projects yet."
- If empty due to search/filter, offer to clear the filter.
- Center-align with generous `py-16` or `py-24` padding.

---

## 14. Feedback and Microinteractions

| Interaction type | Duration |
|---|---|
| Button hover color change | 150ms |
| Form validation message | Instant (< 100ms after blur) |
| Success toast fade in | 200ms |
| Modal open/close | 200-300ms |
| Skeleton to content | Progressive (no delay) |

### Rules:
- **Mutations:** Always show `toast.success()` or `toast.error()`.
- **Call `refetch()` before showing success toast** so UI reflects new state.
- **Button loading states:** Disable and show spinner while pending.
- **Form submission:** Disable submit, show spinner inside button.

---

## 15. Error Prevention and Destructive Actions

### Confirmation dialogs:
- **Use before any irreversible action.** Restate what will be deleted, warn it cannot be undone.
- **Cancel button should be default focused** — keyboard users should not accidentally confirm.
- For **reversible soft-deletes**, skip the modal. Show undo toast for 5-8 seconds.

### Spacing:
- Never place Delete/Remove adjacent to Save/Confirm.
- Use `variant="destructive"` to visually distinguish.

### Prevent data loss:
- Prompt "You have unsaved changes. Discard them?" when dismissing with unsaved edits.
- Never silently discard user input.

---

## 16. Progressive Disclosure

Show users what they need now, reveal more on demand.

### When to apply:
- Form has 5+ fields (collapse advanced under an accordion)
- List items have secondary details (expand or open a side sheet)
- Dashboard has summary and drill-down views

### Patterns:

| Pattern | Use case | Component |
|---|---|---|
| **Accordion** | FAQ, settings, advanced fields | `Accordion` |
| **Sheet** | Full record details, edit forms | `Sheet` |
| **Dialog** | Confirmation, focused input | `Dialog` |
| **Tooltip** | Brief explanation (one sentence max) | `Tooltip` |
| **Tabs** | Multiple views of same data | `Tabs` |

### Rules:
- Primary actions and data always on screen.
- Always make it obvious more content exists (chevron, "Show more", count badge).
- **DO NOT** use modals as a reflex — consider if there is a better place for the interaction first.

---

## 17. Navigation and Orientation

Users always need to know: *Where am I? Where can I go? How do I get back?*

- **Highlight the active state** clearly (`bg-accent` or `text-primary` + left border).
- Page/section headings must match navigation labels exactly.
- **Breadcrumbs** for any block with 3+ levels of depth.
- Provide a **clear back action** for sub-views.
- Navigation in the same position across all views.

---

## 18. Data Tables and Lists

### Column rules:
- **Left-align text. Right-align numbers.** This dramatically improves scanning.
- **Use tabular numbers** (`style={{ fontVariantNumeric: "tabular-nums" }}`) for all numeric columns.
- Limit to **5-7 visible columns** on desktop; fewer on mobile.
- **Column headers clickable** for sorting with arrow indicators.

### Row design:
- **Alternating row colors** (`bg-muted/30` on odd rows) for dense tables.
- Row actions in last column — always visible or in a `DropdownMenu` via `MoreHorizontal` icon.
- **Action buttons** must use `variant="ghost"` or `variant="outline"`, not primary.

### Mobile adaptation:
- Transform table rows into **stacked card layouts** on small screens.
- `hidden md:block` on the table, `block md:hidden` on mobile cards.
- Never require horizontal scrolling for important data.

---

## 19. KPI / Metric Cards and Dashboards

### KPI cards:
- **Large, bold number** for the primary metric (`text-3xl font-bold`)
- **Clear label** below or above (`text-sm text-muted-foreground`)
- **Trend indicator** with icon + percentage

### Dashboard rules:
- Place most important KPIs at the top.
- Limit visible metrics to **4-6 on primary view**. Use tabs for more.
- Every chart needs: title, axis labels, legend (if multi-series), hover tooltip.
- **Bar charts** for comparisons, **line charts** for trends, **pie/donut charts** sparingly.
- **Avoid 3D charts** — they distort values.

### Dashboard Anti-Pattern:
Avoid the "hero metric layout template" — big number, small label, supporting stats, gradient accent strip. This is the most recognizable AI design template and should be avoided unless intentionally chosen.

---

## 20. Accessibility Baseline

### Touch targets:
- All interactive elements: **44x44px** minimum tappable area.
- Space interactive elements at least **8px apart**.

### Color contrast:
- Body text: **4.5:1** minimum (WCAG AA).
- Large text (18px+ bold or 24px+): **3:1** minimum.
- Use semantic tokens (`text-foreground` on `bg-background`) — pre-calibrated.
- **Never use light gray text that fails the 4.5:1 ratio.**

### Keyboard and screen reader:
- All interactive elements reachable by keyboard (Tab, Enter, Space, Escape).
- `aria-label` on all icon-only buttons.
- Semantic HTML: `<button>` for actions, `<a>` for navigation, `<input>` for data.
- **Focus rings:** Never `outline: none` without replacement. Always keep `focus-visible:ring-2`. Focus ring must be 2-3px thick, high contrast, offset from the element.
- Tables: proper `<thead>`, `<tbody>`, `<th scope="col">`.

---

## 21. Mobile-First Responsive Design

### Rules:
- **Start with `flex-col`**, stack to `md:flex-row` or grid layouts at larger screens.
- **No horizontal overflow.** Use `overflow-x-hidden` as safety net.
- **Touch targets: 44px minimum.**
- **Hover states are desktop-only.** Never depend on `:hover` for essential actions.
- Form fields: `w-full` on mobile.
- Navigation: collapse to hamburger or bottom nav on small screens.

### Breakpoint strategy:
```
Mobile first: default -> sm (640px) -> md (768px) -> lg (1024px) -> xl (1280px)
```

### Beyond screen size:
Consider pointer and hover capabilities, not just viewport width. A laptop with touchscreen and a tablet with keyboard both exist. Touch devices need larger targets and always-visible controls.

---

## 22. UX Writing (Microcopy)

### Core rules:
- **Labels:** Noun phrases. "First Name", "Due Date"
- **Buttons:** Verb + noun. "Save Changes", "Delete Record"
- **Error messages:** Plain language + solution.
- **Tooltips:** One sentence max. Explain what, not what it is.
- **Empty states:** Speak directly. "You don't have any projects yet."
- **Confirmation dialogs:** State the consequences.
- **Placeholders:** Example values ("you@company.com"), not repeated labels.

### Voice vs Tone:

| Moment | Tone |
|---|---|
| Success | Celebratory, brief: "Done! Your changes are live." |
| Error | Empathetic, helpful: "That didn't work. Here's what to try..." |
| Loading | Reassuring: "Saving your work..." |
| Destructive | Serious, clear: "Delete this project? This can't be undone." |

**Never use humor for errors.** Users are already frustrated.

### Consistency Glossary

Pick one term and stick with it across the entire block:

| Inconsistent | Choose one |
|---|---|
| Delete / Remove / Trash | **Delete** |
| Settings / Preferences / Options | **Settings** |
| Sign in / Log in / Enter | **Sign in** |
| Create / Add / New | **Create** |

### Writing for Translation:
German text is ~30% longer than English. Allocate space. Keep numbers separate ("New messages: 3" not "You have 3 new messages").

---

## 23. Conventions and Consistency

### Universal conventions:

| Convention | Rule |
|---|---|
| Logo / app name | Top-left |
| Search | Top-center or top-right, magnifying glass icon |
| Settings | Top-right, gear icon |
| Red = danger | Errors and destructive actions only |
| Checkmark | Confirmation / success |
| X icon | Close / cancel / remove |
| Pencil | Edit |
| Trash | Delete |
| Plus | Add / create |
| Chevron right | Navigate deeper |
| Chevron down | Expand in-place / dropdown |

### Internal consistency:
- Same component for same pattern throughout a block.
- Same action always triggers same result.
- Button labels consistent — don't say "Save" in one place and "Update" for the same action.
- Spacing consistent — if cards have `p-6`, all cards in that block have `p-6`.

---

## 24. Calculator and Utility Tool Polish

1. **Clear section grouping:** Separate Inputs from Results using Cards, Separator, or background shift.
2. **Results prominently displayed:** Primary output `text-3xl font-bold text-primary`.
3. **Real-time calculation:** Update as user types. No "Calculate" button for simple calculations.
4. **Input labels with units:** Show unit next to label or inside input suffix.
5. **Formatted numbers:** Use `toLocaleString()` for all outputs.
6. **Reset button:** `variant="ghost"` or `variant="outline"`.
7. **Visual result card:** Wrap primary result in `Card` with subtle `bg-primary/5` accent.
8. **Edge case handling:** Helpful messages for impossible inputs, not NaN or Infinity.

---

## 25. AI Slop Anti-Pattern Checklist

Actively check for and reject these fingerprints of generic AI-generated interfaces:

### Typography:
- NOT using only one font family with no hierarchy contrast
- NOT using a flat type hierarchy where sizes are < 1.25x ratio apart
- NOT placing large rounded icons above every heading
- NOT using monospace as lazy shorthand for "technical"
- NOT setting long body passages in uppercase

### Color:
- NOT using cyan-on-dark, purple-to-blue gradients, neon accents
- NOT using gray text on colored backgrounds
- NOT using pure black/white for large areas
- NOT using dark mode with glowing colored box-shadows
- NOT using gradient text (`background-clip: text`)

### Layout:
- NOT wrapping everything in cards (cardocalypse)
- NOT nesting cards inside cards
- NOT using identical card grids repeated endlessly
- NOT using the hero metric template (big number, label, stats, gradient)
- NOT center-aligning everything — prefer left-aligned with asymmetric layouts
- NOT using the same spacing everywhere — vary for hierarchy

### Motion:
- NOT using bounce or elastic easing
- NOT animating layout properties (width, height, padding)
- NOT ignoring `prefers-reduced-motion`
- NOT using > 500ms for standard UI feedback

### Structure:
- NOT using colored left/right border stripes as decoration (use sparingly only for active/selected state indicators)
- NOT using glassmorphism everywhere (blur effects, glass cards, glow borders as decoration)
- NOT using sparklines as decoration that convey nothing
- NOT using modals by reflex
- NOT making every button primary

---

## 26. Finishing Touches

- **Smooth transitions:** `transition-all duration-200` on cards and rows
- **Hover states on rows/cards:** `hover:bg-muted/50` for interactivity indication
- **Auto-focus first field** when form opens (`autoFocus`)
- **Escape to cancel** any modal, dialog, or inline edit
- **Confirmation animation:** Brief `Check` icon in save button after success
- **Badge counts:** Show filtered item count ("3 active projects")
- **Relative timestamps:** "2 hours ago" via `date-fns/formatDistanceToNow`
- **Truncate long text** with `truncate` or `line-clamp-2`, full value in `Tooltip`
- **Sticky headers** for long tables

---

## Appendix A: Quick Reference

| Need | Use |
|---|---|
| Primary CTA | `Button variant="default"` — one per screen |
| Secondary action | `Button variant="outline"` |
| Danger / delete | `Button variant="destructive"` |
| Edit a field | Always-visible `Pencil` icon + inline `Input` |
| Complex edit form | `Sheet` (slides from side) |
| Confirmation | `Dialog` with Cancel focused by default |
| Brief helper text | `Tooltip` (one sentence max) |
| Status values | `Badge` with color + text (never color alone) |
| Long lists | `Accordion` for secondary details |
| Multiple data views | `Tabs` |
| Loading data | `Skeleton` matching content structure |
| Empty collection | Icon + heading + explanation + CTA |
| Error state | Icon + message + retry button |

## Appendix B: Motion and Spacing Tokens

```css
/* Timing (100/300/500 rule) */
--duration-instant: 100ms;
--duration-fast: 200ms;
--duration-normal: 300ms;
--duration-slow: 500ms;
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);       /* elements entering */
--ease-in: cubic-bezier(0.7, 0, 0.84, 0);         /* elements leaving */
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);    /* state toggles */

/* Z-index semantic scale */
--z-dropdown: 100;
--z-sticky: 200;
--z-modal-backdrop: 300;
--z-modal: 400;
--z-toast: 500;
--z-tooltip: 600;
```

## Appendix C: Design Brief Template

Before building any complex Vibe Coding block, produce a brief:

1. **Feature Summary** (2-3 sentences): What, who, why.
2. **Primary User Action**: The single most important thing.
3. **Design Direction**: 3 brand voice words. The aesthetic approach.
4. **Layout Strategy**: What gets emphasis, how information flows.
5. **Key States**: Default, empty, loading, error, success, edge cases.
6. **Interaction Model**: What happens on click, hover, scroll.
7. **Content Requirements**: Labels, error messages, microcopy, realistic data ranges.
8. **Anti-Goals**: What this should NOT look like.

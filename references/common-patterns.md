# Common Patterns

Small reusable patterns that come up across Vibe Coding blocks but don't warrant their own reference file. Each is a copy-pasteable snippet using the skill's preferred style (`var`, `function() {}`).

## Table of Contents

- [Cross-Page State with localStorage + URL Parameters](#cross-page-state-with-localstorage--url-parameters)
- [Clipboard Copy Button](#clipboard-copy-button)
- [Navigation Blocker for Unsaved Changes](#navigation-blocker-for-unsaved-changes)

## Cross-Page State with localStorage + URL Parameters

When a block needs to remember user state across pages (currently selected record, last filter, last viewed dashboard), `localStorage` works inside Vibe Coding blocks just like in any browser context. Pair with a URL parameter so deep links also work:

```jsx
import { useState, useEffect } from "react";

export default function Block() {
  var fromUrl = new URLSearchParams(window.location.search).get("eventId");
  var saved = localStorage.getItem("softr_myapp_selected_event_id");
  var initialId = fromUrl || saved || null;

  var [selectedId, setSelectedId] = useState(initialId);

  useEffect(function() {
    if (selectedId) {
      localStorage.setItem("softr_myapp_selected_event_id", selectedId);
    }
  }, [selectedId]);

  /* ... rest of block ... */
}
```

Why both:

- **`localStorage`** survives page navigation and refresh. Depending on the browser, it may also survive logout.
- **URL parameter** makes the state shareable -- a user can paste a link and the destination page lands on the same record.
- **URL wins** over localStorage so explicit links override stored state.

### Namespacing

Always namespace your keys: `softr_<app>_<resource>_<key>`. Without a namespace, two Vibe Coding blocks on the same domain can stomp on each other's state:

```jsx
/* Good */
localStorage.setItem("softr_acme_pursuits_filter", JSON.stringify(filter));

/* Bad -- collides with anything else using "filter" */
localStorage.setItem("filter", JSON.stringify(filter));
```

### Clearing on logout

If state should NOT survive logout (e.g. it references record IDs the next user shouldn't see), clear it explicitly when the user signs out, or scope keys to the current user's email:

```jsx
var currentUser = useCurrentUser();
var key = "softr_myapp_selected_event_" + ((currentUser && currentUser.email) || "anon");
```

## Clipboard Copy Button

Standard browser `navigator.clipboard.writeText` works inside Vibe Coding blocks. Softr-published apps run on HTTPS, which is the only requirement for the Clipboard API, so no fallback is needed.

```jsx
import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

function CopyButton(props) {
  var [copied, setCopied] = useState(false);

  function handleClick() {
    navigator.clipboard.writeText(props.value).then(function() {
      setCopied(true);
      toast.success("Copied " + (props.label || "value"));
      setTimeout(function() { setCopied(false); }, 1500);
    });
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={handleClick}
      aria-label={"Copy " + (props.label || "value")}
    >
      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
    </Button>
  );
}
```

Usage:

```jsx
<CopyButton value={record.fields.invoiceUrl} label="invoice URL" />
<CopyButton value={getFieldValue(record.fields.email)} label="email" />
```

The `aria-label` is required because the button has no visible text, only an icon. Without it the button is not screen-reader accessible.

## Navigation Blocker for Unsaved Changes

Softr apps use SPA-mode client-side navigation — when a user clicks a link in Softr's nav bar, sidebar, or any `<NavigationAction>`, the route changes without a full page reload. The browser's standard `beforeunload` event only fires for tab close / refresh / browser back-forward / external nav, so the classic dirty-form warning misses every internal Softr click.

Softr's `useNavigationBlocker` hook intercepts BOTH internal SPA navigation AND browser-level unload with a single API. Import it from `@/lib/use-navigation-blocker`.

**Boolean form — simplest case:**

```jsx
import { useState } from "react";
import { useNavigationBlocker } from "@/lib/use-navigation-blocker";

export default function Block() {
  var [isDirty, setIsDirty] = useState(false);

  useNavigationBlocker(isDirty);

  function handleFieldChange(newValue) {
    setIsDirty(true);
    /* ... update form state ... */
  }

  /* ... form rendering ... */
}
```

**Callback form — when you need to read a ref without re-running on every render:**

```jsx
import { useRef } from "react";
import { useNavigationBlocker } from "@/lib/use-navigation-blocker";

export default function Block() {
  var dirtyRef = useRef(false);

  useNavigationBlocker(function() { return dirtyRef.current; });

  function handleFieldChange() {
    dirtyRef.current = true;
    /* ... update local state without re-rendering the hook ... */
  }

  /* ... rest ... */
}
```

The hook automatically handles:

- Browser's "Leave site?" dialog on tab close / refresh / external nav.
- Softr's in-app confirmation modal when the user clicks an internal Softr link or `<NavigationAction>`.
- Letting navigation through if the user confirms; cancelling if they decline.

**Most form blocks don't need to wire this manually** — Softr's Vibe Coding bundler often adds the blocker automatically when it detects form dirty state. You only need to add it explicitly for advanced cases:

- Multi-step forms where the dirty state spans several panels.
- Manual dirty tracking that doesn't go through standard form-state hooks.
- Blocks where you want to block on something other than form dirtiness (e.g., a pending background upload).

**Asking Softr to add the blocker automatically:** when generating or refining a form block in the Vibe Coding editor, you can prompt with "Block the navigation when the form is dirty" and Softr will wire `useNavigationBlocker` for you — useful when you don't want to write the import + hook call yourself.

# Advanced Integrations

Patterns for embedding third-party libraries that ship their own global CSS inside a Softr Vibe Coding block without style bleed.

## CSS Isolation via Shadow DOM

**Problem:** Third-party libraries ship CSS with generic selectors like `.marker`, `.editor`, `.btn`. Inside a Softr page, those selectors bleed into the rest of the page or get clobbered by Softr's own styles. Scoping manually is impractical.

**Solution:** Mount the library inside a **Shadow DOM** attached to a host element. The shadow root is a fully isolated DOM subtree -- the library's CSS cannot leak out, and Softr's styles cannot leak in. React renders the host wrapper; the library lives inside the shadow.

```jsx
import { useEffect, useRef } from "react";

export default function Block() {
  var hostRef = useRef(null);

  useEffect(function() {
    var host = hostRef.current;
    if (!host || host.shadowRoot) return; /* already initialized */

    var shadow = host.attachShadow({ mode: "open" });

    /* Inject the library's CSS inside the shadow */

    /* Option A: external stylesheet from CDN */
    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://cdn.example.com/somelib/style.css";
    shadow.appendChild(link);

    /* Option B: inline <style> for custom overrides */
    var style = document.createElement("style");
    style.textContent = ".marker { color: red; }";
    shadow.appendChild(style);

    /* Create the container where the library mounts */
    var innerDiv = document.createElement("div");
    innerDiv.id = "lib-root";
    innerDiv.style.width = "100%";
    innerDiv.style.height = "500px";
    shadow.appendChild(innerDiv);

    /* Initialize the library against innerDiv */
    // var map = L.map(innerDiv).setView([0, 0], 2);
    // var editor = new TinyMCE({ target: innerDiv });
  }, []);

  /* To query elements inside the shadow later: */
  // var el = hostRef.current.shadowRoot.getElementById("lib-root");

  return <div ref={hostRef} style={{ width: "100%" }} />;
}
```

## Key Points

- Use `attachShadow({ mode: "open" })`. The `open` mode lets you access the shadow later via `host.shadowRoot`. Always use `open`.
- **Guard against double-initialization.** React re-renders (and StrictMode) can fire the effect twice. Check `if (host.shadowRoot) return;` before calling `attachShadow` -- it throws if called on an element that already has a shadow root.
- **Query inside the shadow** via `host.shadowRoot.getElementById(...)` or `.querySelector(...)`. `document.getElementById` will NOT find elements inside a shadow root.
- **CSS is fully isolated in both directions.** Softr's fonts, resets, and utility classes do not reach inside. If you need Softr's font inside the shadow, redeclare it in the injected `<style>`.
- **Events bubble out** of the shadow root normally (click, input, etc.), so React event handling on the host still works for most libraries.

## When NOT to Use Shadow DOM

If the library is React-native (shadcn, Recharts, lucide-react) and uses inline styles or scoped classes, skip the shadow -- it adds complexity for no benefit. Reserve this pattern for libraries that inject global CSS.

## Libraries Where This Pattern Saves Hours

Leaflet, Mapbox GL, TinyMCE, Quill, CKEditor, FullCalendar, Grapesjs, Froala, and any CDN-distributed widget from a non-React world.

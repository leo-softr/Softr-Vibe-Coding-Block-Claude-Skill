#!/usr/bin/env python3
"""Check every relative Markdown link in this repo: the target file exists and,
when the link has a #fragment pointing into a .md file, that file has a heading
(or <a name/id>) producing that anchor under GitHub's slug rules.

External links (http:, https:, mailto: ...) are not checked. Links inside fenced
code blocks and inline code spans are ignored. CHANGELOG.md is skipped (it is
generated from commit subjects).

Run from anywhere:   python3 .github/scripts/check-links.py
Exit code 0 when every link resolves, 1 otherwise. Under GitHub Actions each
broken link is also printed as an error annotation on its file and line.
"""
import os
import re
import sys
import unicodedata

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IN_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"
SKIP_DIRS = (".git", ".claude", "node_modules")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
HTML_ANCHOR_RE = re.compile(r'<a\s+(?:name|id)="([^"]+)"')
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)\)")
SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)


def md_files():
    for d, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(d, ROOT)
        if rel != "." and rel.split(os.sep)[0] in SKIP_DIRS:
            dirs[:] = []
            continue
        for f in files:
            if f.endswith(".md") and f != "CHANGELOG.md":
                yield os.path.join(d, f)


def slugify(text):
    """GitHub's heading slug: lower-case, drop markup and punctuation, spaces to hyphens."""
    t = text.strip().lower()
    t = re.sub(r"<[^>]+>", "", t)                      # inline HTML
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)     # [text](url) -> text
    out = []
    for ch in t:
        if ch.isalnum() or ch in "-_ ":
            out.append(ch)
        else:
            cat = unicodedata.category(ch)
            if cat.startswith("L") or cat.startswith("N") or cat == "Mn":
                out.append(ch)
    return "".join(out).replace(" ", "-")


_anchor_cache = {}


def anchors(path):
    if path in _anchor_cache:
        return _anchor_cache[path]
    found, counts, fence = set(), {}, False
    with open(path, encoding="utf-8") as fh:
        for line in fh.read().split("\n"):
            if FENCE_RE.match(line):
                fence = not fence
                continue
            if fence:
                continue
            m = HEADING_RE.match(line)
            if m:
                base = slugify(m.group(2))
                n = counts.get(base, 0)
                found.add(base if n == 0 else f"{base}-{n}")   # duplicate headings get -1, -2 ...
                counts[base] = n + 1
            found.update(HTML_ANCHOR_RE.findall(line))
    _anchor_cache[path] = found
    return found


def report(src, lineno, kind, target):
    rel = os.path.relpath(src, ROOT)
    print(f"{kind} {rel}:{lineno} -> {target}")
    if IN_ACTIONS:
        print(f"::error file={rel},line={lineno}::{kind.lower()}: {target}")


def main():
    total = broken = 0
    for src in sorted(md_files()):
        fence = False
        with open(src, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        for lineno, line in enumerate(lines, 1):
            if FENCE_RE.match(line):
                fence = not fence
                continue
            if fence:
                continue
            for target in LINK_RE.findall(re.sub(r"`[^`]*`", "", line)):
                if SCHEME_RE.match(target):
                    continue
                total += 1
                path, _, anchor = target.partition("#")
                dest = os.path.normpath(os.path.join(os.path.dirname(src), path)) if path else src
                if not os.path.exists(dest):
                    broken += 1
                    report(src, lineno, "MISSING FILE", target)
                elif anchor and dest.endswith(".md") and anchor not in anchors(dest):
                    broken += 1
                    report(src, lineno, "BAD ANCHOR", target)
    print(f"checked {total} relative links, {broken} broken")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())

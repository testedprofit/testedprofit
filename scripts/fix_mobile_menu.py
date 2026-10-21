#!/usr/bin/env python3
"""Move #mobile-menu out of a backdrop-blur header.

A position:fixed menu inside a header that uses backdrop-filter is trapped
in that header's box, so the overlay only covers the nav bar. The Rock Paper
Scissors sculpture page keeps the menu as a sibling after the header.

Does not edit the homepage or app/wallet pages.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_PREFIXES = (
    "pages/algoflow/",
    "pages/nfts/",
    "pages/inspector/",
    "pages/launchpad/",
    "superbowlLX/",
    "pages/multisend/",
    "CheckIP/",
    "Crypto Tax-Loss Harvester/",
    "Impermanent Loss Visualizer/",
    "pages/genesis/",
    "pages/Security Lab/",
    "pages/PNET/pnetleaderboard/",
    "conservation-fund/",
    "Algohub/",
    "scam-scan/",
)

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


def excluded(rel: str) -> bool:
    if rel == "index.html":
        return True
    return any(rel == prefix.rstrip("/") or rel.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def element_end(html: str, start: int, tag: str) -> int | None:
    """Return the index just after the matching end tag. start points at '<'."""
    n = len(html)
    i = start
    depth = 0
    tag = tag.lower()
    while i < n:
        if html[i] != "<":
            i += 1
            continue
        if html.startswith("<!--", i):
            j = html.find("-->", i + 4)
            i = n if j < 0 else j + 3
            continue
        if html.startswith("<!", i) or html.startswith("<?", i):
            j = html.find(">", i + 2)
            i = n if j < 0 else j + 1
            continue
        close = html.startswith("</", i)
        k = i + (2 if close else 1)
        name_end = k
        while name_end < n and html[name_end].isalnum():
            name_end += 1
        name = html[k:name_end].lower()
        quote = ""
        p = name_end
        while p < n:
            ch = html[p]
            if quote:
                if ch == quote:
                    quote = ""
            elif ch in "\"'":
                quote = ch
            elif ch == ">":
                break
            p += 1
        if p >= n:
            return None
        self_closing = (not close) and (html[p - 1] == "/" or name in VOID)
        if name == tag:
            if close:
                depth -= 1
                if depth == 0:
                    return p + 1
            elif not self_closing:
                depth += 1
                if depth == 0:
                    return None
        i = p + 1
    return None


def opening_tag_has_blur(opening: str) -> bool:
    low = opening.lower()
    return "backdrop-blur" in low or "backdrop-filter" in low


def find_id_element(html: str, el_id: str):
    needle_dq = f'id="{el_id}"'
    needle_sq = f"id='{el_id}'"
    pos = html.find(needle_dq)
    if pos < 0:
        pos = html.find(needle_sq)
    if pos < 0:
        return None
    start = html.rfind("<", 0, pos)
    if start < 0:
        return None
    name_end = start + 1
    while name_end < len(html) and html[name_end].isalnum():
        name_end += 1
    tag = html[start + 1:name_end].lower()
    end = element_end(html, start, tag)
    if end is None:
        return None
    return start, end, tag


def containing_header(html: str, start: int, end: int):
    i = 0
    low = html.lower()
    found = None
    while True:
        j = low.find("<header", i)
        if j < 0:
            break
        nxt = html[j + 7:j + 8]
        if nxt and (nxt.isalnum() or nxt in "-_:"):
            i = j + 7
            continue
        hend = element_end(html, j, "header")
        if hend is None:
            break
        if j < start and end <= hend:
            opening_end = html.find(">", j)
            opening = html[j:opening_end + 1] if opening_end != -1 else ""
            if opening_tag_has_blur(opening):
                found = (j, hend)
        i = hend
    return found


def bump_z(menu: str) -> str:
    gt = menu.find(">")
    if gt < 0:
        return menu
    opening, rest = menu[:gt], menu[gt:]
    if "z-[60]" in opening:
        return menu
    if "z-40" in opening:
        opening = opening.replace("z-40", "z-[60]", 1)
    elif "class=\"" in opening:
        opening = opening.replace("class=\"", "class=\"z-[60] ", 1)
    elif "class='" in opening:
        opening = opening.replace("class='", "class='z-[60] ", 1)
    return opening + rest


def fix_file(path: Path) -> bool:
    html = path.read_text(encoding="utf-8")
    found = find_id_element(html, "mobile-menu")
    if not found:
        return False
    start, end, _tag = found
    header = containing_header(html, start, end)
    if not header:
        return False
    _hstart, hend = header
    menu = bump_z(html[start:end].strip())
    comment = (
        "<!-- Mobile menu sits outside the header so backdrop-blur does not trap the fixed overlay. -->"
    )
    new_html = html[:start] + html[end:]
    # The header end shifts if the menu was before it, which it is.
    shift = end - start
    insert_at = hend - shift
    block = "\n\n    " + comment + "\n    " + menu + "\n"
    new_html = new_html[:insert_at] + block + new_html[insert_at:]
    if new_html == html:
        return False
    path.write_text(new_html, encoding="utf-8")
    return True


def main():
    changed = []
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT).as_posix()
        if any(part.startswith(".") or part in {".git", "node_modules"} for part in path.parts):
            continue
        if excluded(rel):
            continue
        if fix_file(path):
            changed.append(rel)
    print(f"Moved mobile menu on {len(changed)} pages")
    for rel in changed:
        print(rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())

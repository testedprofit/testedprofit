#!/usr/bin/env python3
"""Crawl every HTML file and report site-health issues.

Read-only. Exit status is 1 when any internal link target is missing, otherwise 0.

Checks:
- broken internal links (path does not resolve to a file in this repo)
- broken local asset, stylesheet, and script references
- missing or duplicate <title> and meta description values
- missing <h1> or more than one <h1>
- missing canonical
- indexable pages absent from sitemap.xml
- sitemap <loc> values that do not exist on disk
- images with no alt attribute
- #mobile-menu nested inside a backdrop-blur header
- inline scripts likely to throw (missing DOM nodes, AOS/lucide/jQuery)
- http:// URLs in href, src, or CSS url() (XML namespaces are ignored)

Usage:
    python3 scripts/site_health_audit.py
    python3 scripts/site_health_audit.py --json /tmp/site-health.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generate_sitemap import collect_sitemap_entries  # noqa: E402

SITE_HOSTS = {"testedprofit.com", "www.testedprofit.com"}
NS_PREFIXES = (
    "http://www.w3.org/",
    "http://schema.org",
    "https://schema.org",
    "http://www.sitemaps.org/",
    "https://www.sitemaps.org/",
)
SKIP_WALK = {".git", "node_modules", ".github"}
ASSET_ATTRS = {
    "img": ("src",),
    "script": ("src",),
    "source": ("src",),
    "video": ("src", "poster"),
    "audio": ("src",),
    "track": ("src",),
    "iframe": ("src",),
    "embed": ("src",),
    "object": ("data",),
}
URL_RE = re.compile(r"url\(\s*([\"']?)(.*?)\1\s*\)", re.I)
GET_ID_CHAIN = re.compile(
    r"""getElementById\(\s*(['"])([^'"]+)\1\s*\)\s*\??\.\s*(\w+)"""
)
GET_ID_ASSIGN = re.compile(
    r"""(?:const|let|var)\s+(\w+)\s*=\s*document\.getElementById\(\s*(['"])([^'"]+)\2\s*\)"""
)


def iter_html_files():
    for path in ROOT.rglob("*.html"):
        if any(part in SKIP_WALK or part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        yield path


def page_url(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "https://testedprofit.com/"
    if rel.endswith("/index.html"):
        return "https://testedprofit.com/" + rel[: -len("index.html")]
    return "https://testedprofit.com/" + rel


def attr_map(attrs):
    out = {}
    for key, value in attrs:
        if key is None:
            continue
        out[key.lower()] = "" if value is None else value
    return out


def looks_namespaced(url: str) -> bool:
    return url.startswith(NS_PREFIXES)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.titles = []
        self.h1 = []
        self.descriptions = []
        self.canonicals = []
        self.robots = []
        self.anchors = []
        self.images = []
        self.assets = []
        self.ids = []
        self.duplicate_ids = []
        self.seen_ids = set()
        self.inline_scripts = []
        self.script_srcs = []
        self.style_chunks = []
        self.menu_inside_blur_header = False
        self._in_title = False
        self._in_h1 = False
        self._in_script = False
        self._in_style = False
        self._buf = []
        self._script_has_src = False

    def handle_starttag(self, tag, attrs):
        self._start(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self._start(tag, attrs, True)

    def _start(self, tag, attrs, self_closing):
        tag = tag.lower()
        am = attr_map(attrs)
        line = self.getpos()[0]
        el_id = am.get("id", "")
        if el_id:
            if el_id in self.seen_ids:
                self.duplicate_ids.append(el_id)
            self.seen_ids.add(el_id)
            self.ids.append(el_id)
        if el_id == "mobile-menu":
            for ancestor, aattrs in self.stack:
                classes = aattrs.get("class", "")
                style = aattrs.get("style", "")
                blurred = (
                    "backdrop-blur" in classes
                    or "backdrop-filter" in style
                    or "-webkit-backdrop-filter" in style
                )
                if ancestor == "header" and blurred:
                    self.menu_inside_blur_header = True
        if tag == "title":
            self._in_title = True
            self._buf = []
        elif tag == "h1":
            self._in_h1 = True
            self._buf = []
        elif tag == "script":
            self._in_script = True
            self._buf = []
            self._script_has_src = bool(am.get("src"))
            if am.get("src"):
                self.script_srcs.append(am["src"])
                self.assets.append(("script", am["src"], line))
        elif tag == "style":
            self._in_style = True
            self._buf = []
        elif tag == "meta":
            name = am.get("name", "").lower()
            prop = am.get("property", "").lower()
            if name == "description":
                self.descriptions.append(am.get("content", "").strip())
            elif name == "robots":
                self.robots.append(am.get("content", ""))
            if prop == "og:image" and am.get("content"):
                self.assets.append(("meta", am["content"], line))
        elif tag == "link":
            rel = am.get("rel", "").lower()
            href = am.get("href", "")
            if "canonical" in rel.split():
                self.canonicals.append(href)
            if href and ("stylesheet" in rel.split() or rel in {"icon", "apple-touch-icon", "preload", "prefetch"}):
                self.assets.append(("link", href, line))
            elif href and rel == "stylesheet":
                self.assets.append(("link", href, line))
        elif tag == "a":
            href = am.get("href", "")
            if href:
                self.anchors.append((href, line))
        elif tag == "img":
            self.images.append(
                {
                    "src": am.get("src", ""),
                    "alt_present": "alt" in am,
                    "alt": am.get("alt", ""),
                    "line": line,
                }
            )
            if am.get("src"):
                self.assets.append(("img", am["src"], line))
            if am.get("srcset"):
                self.assets.append(("srcset", am["srcset"], line))
        elif tag in ASSET_ATTRS:
            for key in ASSET_ATTRS[tag]:
                if am.get(key):
                    self.assets.append((tag, am[key], line))
        if am.get("style"):
            self.style_chunks.append(am["style"])
        if am.get("poster") and tag not in ASSET_ATTRS:
            self.assets.append((tag, am["poster"], line))
        if not self_closing and tag not in {"meta", "link", "img", "br", "hr", "input", "source", "track"}:
            self.stack.append((tag, am))

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title" and self._in_title:
            self.titles.append("".join(self._buf).strip())
            self._in_title = False
        elif tag == "h1" and self._in_h1:
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            self.h1.append(text)
            self._in_h1 = False
        elif tag == "script" and self._in_script:
            if not self._script_has_src:
                self.inline_scripts.append("".join(self._buf))
            self._in_script = False
        elif tag == "style" and self._in_style:
            self.style_chunks.append("".join(self._buf))
            self._in_style = False
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break

    def handle_data(self, data):
        if self._in_title or self._in_h1 or self._in_script or self._in_style:
            self._buf.append(data)


def resolve_local(page: str, raw: str):
    """Return a Path if raw is a same-site URL, else None. None also for skip."""
    if not raw or raw.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    if looks_namespaced(raw):
        return None
    absolute, _frag = urldefrag(urljoin(page, raw.strip()))
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https", ""}:
        return None
    host = parsed.netloc.lower()
    if host and host not in SITE_HOSTS:
        return None
    path = unquote(parsed.path)
    return path


def file_for_site_path(path: str):
    if path in {"", "/"}:
        candidate = ROOT / "index.html"
        return candidate if candidate.is_file() else None
    rel = path.lstrip("/")
    candidates = []
    if path.endswith("/"):
        candidates.append(ROOT / rel / "index.html")
    else:
        candidates.append(ROOT / rel)
        candidates.append(ROOT / rel / "index.html")
        if not rel.endswith(".html"):
            candidates.append(ROOT / f"{rel}.html")
    for candidate in candidates:
        try:
            candidate.relative_to(ROOT)
        except ValueError:
            continue
        if candidate.is_file():
            return candidate
    return None


def split_srcset(value: str):
    urls = []
    for part in value.split(","):
        bit = part.strip().split()
        if bit:
            urls.append(bit[0])
    return urls


def http_urls_in(value: str):
    found = []
    for match in re.finditer(r"https?://[^\s\"'<>)]+", value):
        url = match.group(0).rstrip(".,;")
        if url.startswith("http://") and not looks_namespaced(url):
            found.append(url)
    return found


def script_risks(parser: PageParser):
    issues = []
    inline = "\n".join(parser.inline_scripts)
    srcs = " ".join(parser.script_srcs).lower()
    ids = set(parser.ids)
    if re.search(r"\bAOS\s*\.\s*init\s*\(", inline) and "aos" not in srcs:
        issues.append("AOS.init() but aos.js is not loaded")
    if re.search(r"\blucide\s*\.\s*createIcons\s*\(", inline) and "lucide" not in srcs:
        issues.append("lucide.createIcons() but lucide is not loaded")
    if re.search(r"(?<![\w$])\$\s*\(", inline) and "jquery" not in srcs:
        issues.append("jQuery $() but jquery is not loaded")
    for match in GET_ID_CHAIN.finditer(inline):
        el_id = match.group(2)
        if "?" in match.group(0).split(el_id, 1)[-1][:3]:
            continue
        if el_id not in ids and not match.group(0).split(")")[0].endswith("?"):
            # The regex allows optional chaining via \?? so skip those.
            if "?." in match.group(0):
                continue
            issues.append(f"getElementById('{el_id}').{match.group(3)} but #{el_id} is missing")
    guarded = set()
    for var, _q, el_id in GET_ID_ASSIGN.findall(inline):
        if el_id in ids:
            continue
        if re.search(rf"\bif\s*\(\s*{var}\s*\)", inline) or re.search(rf"\b{var}\s*&&", inline):
            guarded.add(var)
            continue
        if re.search(rf"\b{var}\s*\.", inline) or re.search(rf"\b{var}\s*\[", inline):
            issues.append(f"{var} = getElementById('{el_id}') is used, but #{el_id} is missing")
    for el_id in parser.duplicate_ids:
        if el_id in ids and re.search(rf"getElementById\(\s*['\"]{re.escape(el_id)}['\"]", inline):
            issues.append(f"duplicate id '{el_id}' used by getElementById")
    return issues


def audit():
    pages = []
    titles = defaultdict(list)
    descriptions = defaultdict(list)
    broken_links = []
    broken_assets = []
    missing_title = []
    missing_description = []
    multi_title = []
    missing_h1 = []
    multi_h1 = []
    missing_canonical = []
    missing_alt = []
    menu_bugs = []
    script_issues = []
    http_links = []

    for path in sorted(iter_html_files(), key=lambda p: str(p)):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        parser = PageParser()
        try:
            parser.feed(text)
        except Exception as exc:  # malformed HTML still gets a partial report
            script_issues.append({"file": rel, "issue": f"HTML parse error: {exc}"})
        url = page_url(path)
        title = parser.titles[0] if parser.titles else ""
        description = parser.descriptions[0] if parser.descriptions else ""
        record = {
            "file": rel,
            "url": url,
            "title": title,
            "description": description,
            "h1": parser.h1,
            "canonical": parser.canonicals[0] if parser.canonicals else "",
        }
        pages.append(record)
        if not parser.titles or not title:
            missing_title.append(rel)
        elif len(parser.titles) > 1:
            multi_title.append(rel)
        else:
            titles[re.sub(r"\s+", " ", title)].append(rel)
        if not parser.descriptions or not description:
            missing_description.append(rel)
        elif len(parser.descriptions) > 1:
            # Still index the first; extra tags are a duplicate-on-page issue.
            descriptions[re.sub(r"\s+", " ", description)].append(rel)
            multi_title.append(rel + " (multiple meta descriptions)")
        else:
            descriptions[re.sub(r"\s+", " ", description)].append(rel)
        if not parser.h1:
            missing_h1.append(rel)
        elif len(parser.h1) > 1:
            multi_h1.append({"file": rel, "h1s": parser.h1})
        if not parser.canonicals:
            missing_canonical.append(rel)
        if parser.menu_inside_blur_header:
            menu_bugs.append(rel)
        for issue in script_risks(parser):
            script_issues.append({"file": rel, "issue": issue})
        for img in parser.images:
            if not img["alt_present"]:
                missing_alt.append({"file": rel, "line": img["line"], "src": img["src"]})
        for href, line in parser.anchors:
            for http in http_urls_in(href):
                http_links.append({"file": rel, "line": line, "url": http, "kind": "href"})
            site_path = resolve_local(url, href)
            if site_path is None:
                continue
            if file_for_site_path(site_path) is None:
                broken_links.append({"file": rel, "line": line, "href": href, "path": site_path})
        for kind, raw, line in parser.assets:
            values = split_srcset(raw) if kind == "srcset" else [raw]
            for value in values:
                for http in http_urls_in(value):
                    http_links.append({"file": rel, "line": line, "url": http, "kind": kind})
                site_path = resolve_local(url, value)
                if site_path is None:
                    continue
                # Directory URLs and HTML documents are links, not assets.
                if site_path.endswith("/") or site_path.endswith(".html") or site_path in {"", "/"}:
                    if file_for_site_path(site_path) is None:
                        broken_assets.append({"file": rel, "line": line, "ref": value, "path": site_path, "kind": kind})
                    continue
                if file_for_site_path(site_path) is None:
                    broken_assets.append({"file": rel, "line": line, "ref": value, "path": site_path, "kind": kind})
        for chunk in parser.style_chunks:
            for _q, inner in URL_RE.findall(chunk):
                for http in http_urls_in(inner):
                    http_links.append({"file": rel, "url": http, "kind": "css"})
                site_path = resolve_local(url, inner)
                if site_path is None:
                    continue
                if file_for_site_path(site_path) is None:
                    broken_assets.append({"file": rel, "ref": inner, "path": site_path, "kind": "css"})

    duplicate_titles = {k: v for k, v in titles.items() if len(v) > 1}
    duplicate_descriptions = {k: v for k, v in descriptions.items() if len(v) > 1}

    indexable, skipped = collect_sitemap_entries()
    indexable_locs = {}
    for loc, _lastmod, _priority, rel in indexable:
        indexable_locs[unquote(urlparse(loc).path)] = rel or "index.html"

    sitemap_text = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_locs = [unescape(loc) for loc in re.findall(r"<loc>\s*(.*?)\s*</loc>", sitemap_text)]
    sitemap_paths = {unquote(urlparse(loc).path): loc for loc in sitemap_locs}

    missing_from_sitemap = []
    for path, rel in sorted(indexable_locs.items()):
        if path not in sitemap_paths:
            missing_from_sitemap.append({"path": path, "file": rel})

    sitemap_missing_files = []
    for path, loc in sorted(sitemap_paths.items()):
        if file_for_site_path(path) is None:
            sitemap_missing_files.append({"loc": loc, "path": path})

    report = {
        "html_files": len(pages),
        "counts": {
            "broken_internal_links": len(broken_links),
            "broken_assets": len(broken_assets),
            "missing_title": len(missing_title),
            "multiple_title_tags_or_descriptions": len([x for x in multi_title if "meta" not in x]) + len([x for x in multi_title if "meta" in x]),
            "duplicate_titles": len(duplicate_titles),
            "missing_description": len(missing_description),
            "duplicate_descriptions": len(duplicate_descriptions),
            "missing_h1": len(missing_h1),
            "multiple_h1": len(multi_h1),
            "missing_canonical": len(missing_canonical),
            "missing_alt": len(missing_alt),
            "mobile_menu_inside_blurred_header": len(menu_bugs),
            "script_risks": len(script_issues),
            "http_links": len(http_links),
            "indexable_pages": len(indexable),
            "missing_from_sitemap": len(missing_from_sitemap),
            "sitemap_entries": len(sitemap_locs),
            "sitemap_entries_missing_files": len(sitemap_missing_files),
            "sitemap_skipped": len(skipped),
        },
        "broken_internal_links": broken_links,
        "broken_assets": broken_assets,
        "missing_title": missing_title,
        "multiple_title_notes": multi_title,
        "duplicate_titles": duplicate_titles,
        "missing_description": missing_description,
        "duplicate_descriptions": duplicate_descriptions,
        "missing_h1": missing_h1,
        "multiple_h1": multi_h1,
        "missing_canonical": missing_canonical,
        "missing_alt": missing_alt,
        "mobile_menu_inside_blurred_header": menu_bugs,
        "script_risks": script_issues,
        "http_links": http_links,
        "missing_from_sitemap": missing_from_sitemap,
        "sitemap_entries_missing_files": sitemap_missing_files,
    }
    return report


def print_summary(report):
    print(f"HTML files crawled: {report['html_files']}")
    print("Counts:")
    for key, value in report["counts"].items():
        print(f"  {key}: {value}")
    sections = [
        ("Broken internal links", "broken_internal_links"),
        ("Broken assets", "broken_assets"),
        ("Mobile menu inside blurred header", "mobile_menu_inside_blurred_header"),
        ("Missing title", "missing_title"),
        ("Missing description", "missing_description"),
        ("Missing h1", "missing_h1"),
        ("Missing canonical", "missing_canonical"),
        ("Script risks", "script_risks"),
        ("HTTP links", "http_links"),
        ("Missing from sitemap", "missing_from_sitemap"),
        ("Sitemap entries with no file", "sitemap_entries_missing_files"),
    ]
    for label, key in sections:
        rows = report[key]
        if not rows:
            continue
        print(f"\n{label} ({len(rows)}):")
        shown = rows[:40]
        for row in shown:
            if isinstance(row, str):
                print(f"  {row}")
            else:
                print(f"  {json.dumps(row, ensure_ascii=False)}")
        if len(rows) > len(shown):
            print(f"  ... {len(rows) - len(shown)} more")
    if report["duplicate_titles"]:
        print(f"\nDuplicate titles ({len(report['duplicate_titles'])}):")
        for title, files in list(report["duplicate_titles"].items())[:20]:
            print(f"  {title!r} -> {len(files)} pages")
    if report["duplicate_descriptions"]:
        print(f"\nDuplicate descriptions ({len(report['duplicate_descriptions'])}):")
        for desc, files in list(report["duplicate_descriptions"].items())[:15]:
            print(f"  {desc[:80]!r} -> {len(files)} pages")
    if report["multiple_h1"]:
        print(f"\nMultiple h1 ({len(report['multiple_h1'])}):")
        for row in report["multiple_h1"][:20]:
            print(f"  {row['file']}: {len(row['h1s'])}")
    if report["missing_alt"]:
        print(f"\nMissing alt ({len(report['missing_alt'])}):")
        for row in report["missing_alt"][:20]:
            print(f"  {row['file']}:{row['line']} {row['src'][:80]}")


def main():
    parser = argparse.ArgumentParser(description="Audit testedprofit.com HTML health")
    parser.add_argument("--json", help="Write the full report to this path")
    args = parser.parse_args()
    report = audit()
    print_summary(report)
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nWrote {args.json}")
    return 1 if report["counts"]["broken_internal_links"] else 0


if __name__ == "__main__":
    sys.exit(main())

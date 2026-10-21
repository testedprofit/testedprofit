#!/usr/bin/env python3
"""Add landmark structure, fix canonicals, and leave the homepage untouched.

Safe to re-run. Does not modify /index.html.
"""

import hashlib
import html
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HOME = ROOT / "index.html"
HOME_HASH = hashlib.sha256(HOME.read_bytes()).hexdigest()

STATES = {
    "AL": "Alabama",
    "CO": "Colorado",
    "HI": "Hawaii",
    "IA": "Iowa",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MI": "Michigan",
    "OR": "Oregon",
    "WV": "West Virginia",
    "WY": "Wyoming",
}

# /pages/ articles that are landmarks, with state and optional city group.
PAGE_LANDMARKS = {
    "pages/eagle-statue": ("CO", "Denver metro"),
    "pages/albert-einstein-statue-vail-co": ("CO", "Vail"),
    "pages/bronco-buster-statue": ("CO", "Denver"),
    "pages/the-lady-doctor-statue": ("CO", "Denver"),
    "pages/man-and-woman": ("CO", "Denver"),
    "pages/madre-e-hijo-sculpture": ("CO", "Denver"),
    "pages/the-newsboy-statue": ("CO", "Denver metro"),
    "pages/goldens-vibrant-triceratops": ("CO", "Denver metro"),
    "pages/torii-square-park-westminster": ("CO", "Denver metro"),
    "pages/sensory-park": ("CO", "Denver metro"),
    "pages/sunset-park": ("CO", "Denver metro"),
    "pages/central-square-park": ("CO", "Denver metro"),
    "pages/cowboy-in-pajamas": ("CO", ""),
    "pages/james-dalton-trumbo-statue": ("CO", ""),
    "pages/bear-statue": ("CO", ""),
    "pages/lowell-ponds-state-wildlife-area": ("CO", ""),
    "pages/rocky-flats-national-wildlife-refuge-south-entrance": ("CO", ""),
    "pages/martin-luther-king-memorial": ("CO", ""),
    "pages/honey-rock-dogs-boarding-kennels": ("CO", ""),
    "pages/things-to-do-in-vail-colorado": ("CO", "Vail"),
    "pages/things to do in vail colorado": ("CO", "Vail"),
    "pages/Woodbury Park": ("CO", ""),
    "pages/Oakhurst Park II": ("CO", ""),
    "pages/worlds-tallest-kachina-doll": ("AZ", ""),
    "rotary-park": ("CO", ""),
    "Captain James Cook Statue": ("HI", ""),
}

GUIDES = [
    "pages/earnapp",
    "pages/honeygain",
    "pages/honeygain-content-delivery",
    "pages/bubblecash",
    "pages/top-gig-apps-to-make-money-fast-in-2025",
    "pages/how-to-start-a-vending-machine-business-a-beginners-passive-income-journey",
    "pages/student-loan-delinquency-tips",
    "pages/contenthub",
    "pages/the-ai-powered-kdp-revolution",
    "pages/free-ai-paraphrasing-tool",
    "pages/smart-financial-dashboard",
    "pages/of-calculator",
    "pages/pokemon-card-profit-calculator-track-roi-resale-value",
    "pages/data-sharing-opt-out",
]

# Shown first in "related" modules so the high-impression pages link to each other.
FEATURED_CO = [
    "pages/eagle-statue",
    "pages/albert-einstein-statue-vail-co",
    "pages/bronco-buster-statue",
    "pages/the-lady-doctor-statue",
    "pages/man-and-woman",
    "pages/worlds-tallest-kachina-doll",
]

REDIRECTS = {
    # Canonical tag used to point here, and the URL 404s.
    "pages/earnapp-definitive-review-philippines": "/pages/earnapp/",
    "pages/cedar-mountain-craig-co-local-guide": "/CO/Landmarks/Cedar-Mountain/",
    # Same document as an existing directory, wrong slug.
    "pages/rotary-park": "/rotary-park/",
    "pages/woodbury-park": "/pages/Woodbury%20Park/",
    "tokenomics": "/pages/tokenomics/",
    # Exact duplicate of /pages/bear-statue/. Content stays on that URL.
    "CO/Landmarks/Bear-Statue": "/pages/bear-statue/",
    # Old Shopify blog index. Guides are the current editorial section.
    "blogs/news": "/pages/guides/",
}

CANONICAL_FIXES = {
    "pages/earnapp": "https://testedprofit.com/pages/earnapp/",
    "pages/honeygain": "https://testedprofit.com/pages/honeygain/",
    "pages/honeygain-content-delivery": "https://testedprofit.com/pages/honeygain-content-delivery/",
    "pages/bulldog-towing-recovery": "https://testedprofit.com/pages/bulldog-towing-recovery/",
    "pages/how-to-start-a-vending-machine-business-a-beginners-passive-income-journey": "https://testedprofit.com/pages/how-to-start-a-vending-machine-business-a-beginners-passive-income-journey/",
    "pages/the-ai-powered-kdp-revolution": "https://testedprofit.com/pages/the-ai-powered-kdp-revolution/",
    "CO/Landmarks/Cedar-Mountain": "https://testedprofit.com/CO/Landmarks/Cedar-Mountain/",
    "conservation-fund/contracts/rework_archive/frontend/algopool": "https://testedprofit.com/conservation-fund/contracts/rework_archive/frontend/algopool/",
    "conservation-fund/contracts/rework_archive/frontend/crowdfund": "https://testedprofit.com/conservation-fund/contracts/rework_archive/frontend/crowdfund/",
    "conservation-fund/contracts/rework_archive/frontend/profitlock": "https://testedprofit.com/conservation-fund/contracts/rework_archive/frontend/profitlock/",
}

NOINDEX_SELF = [
    "conservation-fund/contracts/rework_archive/frontend/algopool",
    "conservation-fund/contracts/rework_archive/frontend/crowdfund",
    "conservation-fund/contracts/rework_archive/frontend/profitlock",
]

TITLE_FIXES = {
    "pages/eagle-statue": (
        "Eagle Sculpture at Denver West Plaza | Lakewood, CO Public Art",
        "American Eagle Statue at Denver West Plaza, Lakewood CO",
    ),
    "pages/albert-einstein-statue-vail-co": (
        "Albert Einstein Statue | Profitnet Landmarks",
        "Albert Einstein Statue in Vail, Colorado | Bronze Bench",
    ),
    "pages/bronco-buster-statue": (
        "The Bronco Buster Statue | Denver Public Art",
        "Bronco Buster Statue in Denver Civic Center Park",
    ),
    "pages/the-lady-doctor-statue": (
        "Dr. Justina L. Ford | Denver, CO Directory",
        "The Lady Doctor Statue: Dr. Justina Ford in Denver",
    ),
    "pages/landmarks": (
        "Profitnet | The Digital Archive",
        "Statues and Landmarks by State | TestedProfit",
    ),
    "pages/parks": (
        "Profitnet | The Digital Archive",
        "About the Landmark Archive | TestedProfit",
    ),
}

DESCRIPTION_FIXES = {
    "pages/eagle-statue": (
        "Who made the eagle statue at Denver West Plaza in Lakewood, CO? Explore the history, artist attribution, and symbolism of this iconic public sculpture.",
        "American eagle statue at Denver West Plaza in Lakewood, Colorado: where it stands, how it differs from the Nicolosi eagle on Denver's City and County Building, and what the sculpture symbolizes.",
    ),
    "pages/albert-einstein-statue-vail-co": (
        "An interactive guide to the Albert Einstein statue in Vail, Colorado. A beloved bronze bench by sculptor Gary Lee Price inviting visitors to sit with genius.",
        "Visit the Albert Einstein statue in Vail Village, Colorado. Gary Lee Price's bronze bench lets you sit with Einstein — location, artist, and what to know before you go.",
    ),
    "pages/bronco-buster-statue": (
        "Explore the history, artistry, and legacy of the Bronco Buster statue in Denver's Civic Center Park. A masterpiece of Western realism.",
        "The Bronco Buster statue in Denver's Civic Center Park is Alexander Phimister Proctor's Western bronze — not the Denver Broncos horse at the stadium. Artist, history, and how to visit.",
    ),
    "pages/the-lady-doctor-statue": (
        "A biography of Dr. Justina L. Ford, Colorado's first licensed African American female physician. Explore her legacy in Five Points and beyond.",
        "The Lady Doctor statue honors Dr. Justina Ford, Colorado's first licensed Black woman physician. Find the Denver sculpture, her Five Points house, and her story.",
    ),
    "pages/landmarks": (
        "TestedProfit builds the digital infrastructure for public art and landmarks, ensuring accurate data integration for the AI era.",
        "Directory of public statues, sculptures, and parks by state, plus Denver and Vail city pages. Earning-app reviews live in a separate guides section.",
    ),
    "pages/parks": (
        "TestedProfit builds the digital infrastructure for public art and landmarks, ensuring accurate data integration for the AI era.",
        "About TestedProfit's landmark archive. Browse the statue directory by state, or open the separate earning-app guides.",
    ),
}

STYLE = """
<style id="tp-seo-style">
.tp-seo-crumbs{list-style:none;display:flex;flex-wrap:wrap;gap:.35rem .45rem;margin:0 0 1.25rem;padding:.55rem .9rem;font:500 .82rem/1.4 Inter,system-ui,sans-serif;background:rgba(15,23,42,.72);border:1px solid rgba(148,163,184,.28);border-radius:999px}
.tp-seo-crumbs a{color:#5eead4;text-decoration:none}
.tp-seo-crumbs a:hover{text-decoration:underline}
.tp-seo-crumbs li{color:#e5e7eb}
.tp-seo-crumbs li+li::before{content:"/";color:#94a3b8;margin-right:.45rem}
.tp-seo-related{margin:2rem 0 0;padding:1rem 1.1rem;border:1px solid rgba(148,163,184,.28);border-radius:16px;background:rgba(15,23,42,.55);font-family:Inter,system-ui,sans-serif}
.tp-seo-related h2{margin:0 0 .6rem;font-size:1rem;color:#fff}
.tp-seo-related ul{margin:0;padding-left:1.1rem}
.tp-seo-related a{color:#5eead4}
.tp-seo-related p{margin:.75rem 0 0;color:#cbd5e1;font-size:.92rem}
</style>
""".strip()


def public_path(rel):
    if not rel:
        return "/"
    parts = [quote(part, safe="-._~()'ʻ’–—") for part in rel.split("/")]
    return "/" + "/".join(parts) + "/"


def read(rel):
    return (ROOT / rel / "index.html").read_text(encoding="utf-8", errors="replace")


def write(rel, text):
    path = ROOT / rel / "index.html" if rel else HOME
    if path.resolve() == HOME.resolve():
        raise SystemExit("refusing to write the homepage")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def esc(value):
    return html.escape(value, quote=True)


def strip_tags(value):
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def title_label(text, fallback):
    match = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    if match:
        label = strip_tags(match.group(1)).split("|")[0].strip()
        if label:
            return label[:110]
    return label_of(text, fallback)


def label_of(text, fallback):
    match = re.search(r"<h1\b[^>]*>(.*?)</h1>", text, re.I | re.S)
    if match:
        label = strip_tags(match.group(1))
        if 0 < len(label) <= 90:
            return label
    match = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    if match:
        label = strip_tags(match.group(1)).split("|")[0].strip()
        if label:
            return label[:90]
    return fallback


def _attr(tag, name):
    match = re.search(rf"{name}\s*=\s*([\"'])(.*?)\1", tag, re.I | re.S)
    return match.group(2).strip() if match else ""


def description_of(text):
    for tag in re.findall(r"<meta\b[^>]*>", text, re.I):
        if _attr(tag, "name").lower() == "description":
            return _attr(tag, "content")
    return ""


def replace_exact(text, old, new, where):
    if old == new:
        return text
    if old not in text:
        if new in text:
            return text
        raise SystemExit(f"missing expected copy in {where}: {old[:90]}")
    return text.replace(old, new)


def set_canonical(text, url):
    def repl_link(match):
        tag = match.group(0)
        if not re.search(r"rel=[\"']canonical[\"']", tag, re.I):
            return tag
        if re.search(r"href=[\"'][^\"']*[\"']", tag, re.I):
            return re.sub(r"href=[\"'][^\"']*[\"']", f'href="{url}"', tag, count=1)
        return tag[:-1] + f' href="{url}">'

    updated = re.sub(r"<link\b[^>]*>", repl_link, text, flags=re.I)
    if not re.search(r"rel=[\"']canonical[\"']", updated, re.I):
        updated = updated.replace(
            "</head>",
            f'    <link rel="canonical" href="{url}">\n</head>',
            1,
        )

    def repl_meta(match):
        tag = match.group(0)
        if not re.search(r"property=[\"']og:url[\"']", tag, re.I):
            return tag
        if re.search(r"content=[\"'][^\"']*[\"']", tag, re.I):
            return re.sub(r"content=[\"'][^\"']*[\"']", f'content="{url}"', tag, count=1)
        return tag

    return re.sub(r"<meta\b[^>]*>", repl_meta, updated, flags=re.I)


def ensure_noindex(text):
    if re.search(r'name=["\']robots["\']', text, re.I):
        def repl(match):
            tag = match.group(0)
            return re.sub(
                r'content=["\'][^"\']*["\']',
                'content="noindex, follow"',
                tag,
                count=1,
            )
        return re.sub(r"<meta\b[^>]*name=[\"']robots[\"'][^>]*>", repl, text, count=1, flags=re.I)
    return text.replace(
        "</head>",
        '    <meta name="robots" content="noindex, follow">\n</head>',
        1,
    )


def redirect_html(target):
    safe = esc(target)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Redirecting | TestedProfit</title>
    <!-- tp-seo:redirect -->
    <link rel="canonical" href="https://testedprofit.com{safe}">
    <meta name="robots" content="noindex, follow">
    <meta http-equiv="refresh" content="0; url={safe}">
    <script>location.replace("{safe}");</script>
</head>
<body>
    <p>This page has moved. <a href="{safe}">Continue</a>.</p>
</body>
</html>
"""


def crumb_html(items):
    parts = ['<!-- tp-seo:breadcrumbs -->', '<nav aria-label="Breadcrumb"><ol class="tp-seo-crumbs">']
    for label, href in items[:-1]:
        parts.append(f'<li><a href="{esc(href)}">{esc(label)}</a></li>')
    parts.append(f'<li aria-current="page">{esc(items[-1][0])}</li>')
    parts.append("</ol></nav>")
    parts.append("<!-- /tp-seo:breadcrumbs -->")
    return "\n".join(parts)


def related_html(heading, links, note_href, note):
    items = "\n".join(
        f'<li><a href="{esc(href)}">{esc(label)}</a></li>' for label, href in links
    )
    return f"""<!-- tp-seo:related -->
<aside class="tp-seo-related" aria-label="{esc(heading)}">
    <h2>{esc(heading)}</h2>
    <ul>
        {items}
    </ul>
    <p><a href="{esc(note_href)}">{esc(note)}</a></p>
</aside>
<!-- /tp-seo:related -->"""


def strip_injections(text):
    text = re.sub(r"<!-- tp-seo:breadcrumbs -->.*?<!-- /tp-seo:breadcrumbs -->\n?", "", text, flags=re.S)
    text = re.sub(r"<!-- tp-seo:related -->.*?<!-- /tp-seo:related -->\n?", "", text, flags=re.S)
    text = re.sub(r"<style id=\"tp-seo-style\">.*?</style>\n?", "", text, flags=re.S)
    return text


def inject(text, crumbs, related):
    text = strip_injections(text)
    if "</head>" not in text.lower():
        return text
    text = re.sub(r"</head>", STYLE + "\n</head>", text, count=1, flags=re.I)
    block = "\n" + crumbs + "\n"
    main = re.search(r"<main\b[^>]*>", text, re.I)
    if main:
        text = text[: main.end()] + block + text[main.end() :]
        if related:
            close = re.search(r"</main>", text, re.I)
            if close:
                text = text[: close.start()] + "\n" + related + "\n" + text[close.start() :]
    else:
        body = re.search(r"<body\b[^>]*>", text, re.I)
        if not body:
            return text
        extra = block + (("\n" + related + "\n") if related else "")
        text = text[: body.end()] + extra + text[body.end() :]
    return text


def collect_pages():
    pages = {}
    for path in ROOT.rglob("index.html"):
        rel = str(path.parent.relative_to(ROOT))
        if rel == ".":
            rel = ""
        if any(part.startswith(".") or part in {".git", "node_modules", "preview", "scripts"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "<html" not in text.lower():
            continue
        pages[rel] = text
    return pages


def state_of(rel):
    if rel in PAGE_LANDMARKS:
        return PAGE_LANDMARKS[rel][0]
    top = rel.split("/")[0]
    if top in STATES:
        return top
    return ""


def city_of(rel):
    if rel in PAGE_LANDMARKS:
        return PAGE_LANDMARKS[rel][1]
    return ""


def is_landmark(rel):
    if rel in PAGE_LANDMARKS or rel in {"pages/landmarks", "pages/landmarks/denver", "pages/landmarks/vail"}:
        return True
    top = rel.split("/")[0]
    return top in STATES or rel == "Captain James Cook Statue" or rel == "rotary-park"


def landmark_records(pages):
    records = []
    for rel, text in pages.items():
        if "tp-seo:redirect" in text:
            continue
        if not is_landmark(rel):
            continue
        if rel in {"pages/landmarks", "pages/guides"}:
            continue
        records.append(
            {
                "rel": rel,
                "state": state_of(rel),
                "city": city_of(rel),
                "label": label_of(text, rel.split("/")[-1]),
                "href": public_path(rel),
            }
        )
    return records


def siblings(records, rel, limit=5):
    state = state_of(rel)
    city = city_of(rel)
    pool = [item for item in records if item["rel"] != rel and item["state"] == state and state]
    featured = []
    for name in FEATURED_CO:
        featured.extend(item for item in pool if item["rel"] == name)
    same_city = [item for item in pool if city and item["city"] == city and item not in featured]
    rest = sorted(
        [item for item in pool if item not in featured and item not in same_city],
        key=lambda item: item["label"].lower(),
    )
    ordered = []
    for item in featured + same_city + rest:
        if item["rel"] not in {entry["rel"] for entry in ordered}:
            ordered.append(item)
    return ordered[:limit]


def crumbs_for(rel, label):
    if rel in GUIDES:
        return [
            ("Home", "/"),
            ("Earning guides", "/pages/guides/"),
            (label, public_path(rel)),
        ]
    if rel == "pages/landmarks":
        return [("Home", "/"), ("Landmarks", "/pages/landmarks/")]
    if rel == "pages/guides":
        return [("Home", "/"), ("Earning guides", "/pages/guides/")]
    if rel == "pages/landmarks/denver":
        return [
            ("Home", "/"),
            ("Landmarks", "/pages/landmarks/"),
            ("Colorado", "/CO/"),
            ("Denver", "/pages/landmarks/denver/"),
        ]
    if rel == "pages/landmarks/vail":
        return [
            ("Home", "/"),
            ("Landmarks", "/pages/landmarks/"),
            ("Colorado", "/CO/"),
            ("Vail", "/pages/landmarks/vail/"),
        ]
    state = state_of(rel)
    items = [("Home", "/"), ("Landmarks", "/pages/landmarks/")]
    if state in STATES:
        items.append((STATES[state], public_path(state)))
    elif state == "AZ":
        items.append(("Arizona", "/pages/landmarks/"))
    if rel in STATES:
        return items
    items.append((label, public_path(rel)))
    return items


def apply_copy_fixes(pages):
    for rel, (old, new) in TITLE_FIXES.items():
        pages[rel] = replace_exact(pages[rel], old, new, rel + " title")
    for rel, (old, new) in DESCRIPTION_FIXES.items():
        pages[rel] = replace_exact(pages[rel], old, new, rel + " description")
    for rel, url in CANONICAL_FIXES.items():
        pages[rel] = set_canonical(pages[rel], url)
    for rel in NOINDEX_SELF:
        pages[rel] = ensure_noindex(pages[rel])


def patch_landmarks_hub(text):
    text = replace_exact(
        text,
        """            <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-bold tracking-wide uppercase mb-8">
                <span class="w-2 h-2 rounded-full bg-teal-400 animate-pulse"></span>
                Digital Preservation Initiative
            </div>""",
        """            <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-bold tracking-wide uppercase mb-8">
                <span class="w-2 h-2 rounded-full bg-teal-400 animate-pulse"></span>
                Statues and landmarks
            </div>""",
        "landmarks eyebrow",
    )
    text = replace_exact(
        text,
        """            <h1 class="text-5xl md:text-7xl font-bold text-white tracking-tight mb-8 leading-[1.1]">
                Bridging Physical Heritage <br class="hidden md:block" />
                <span class="gradient-text">with Digital Intelligence.</span>
            </h1>""",
        """            <h1 class="text-5xl md:text-7xl font-bold text-white tracking-tight mb-8 leading-[1.1]">
                Statues and landmarks, <br class="hidden md:block" />
                <span class="gradient-text">sorted by state.</span>
            </h1>""",
        "landmarks h1",
    )
    text = replace_exact(
        text,
        """            <p class="text-xl md:text-2xl text-gray-400 max-w-2xl mx-auto mb-12 font-light leading-relaxed">
                A structured directory of landmarks, art, and public spaces, optimized for discovery in the AI era.
            </p>
        </section>""",
        """            <p class="text-xl md:text-2xl text-gray-400 max-w-2xl mx-auto mb-8 font-light leading-relaxed">
                Public statues, sculptures, and parks. Earning-app reviews are a separate section and are not mixed into this directory.
            </p>
            <!-- tp-seo:hub-split -->
            <div class="grid md:grid-cols-2 gap-4 text-left max-w-3xl mx-auto">
                <a href="/pages/landmarks/" class="card-blur rounded-2xl p-5 block">
                    <span class="text-teal-300 text-xs font-bold uppercase tracking-widest">You are here</span>
                    <strong class="block text-white text-lg mt-1">Statues and landmarks</strong>
                    <span class="text-gray-400 text-sm">Browse by state, or open the Denver and Vail city pages.</span>
                </a>
                <a href="/pages/guides/" class="card-blur rounded-2xl p-5 block">
                    <span class="text-blue-300 text-xs font-bold uppercase tracking-widest">Separate section</span>
                    <strong class="block text-white text-lg mt-1">Earning-app guides</strong>
                    <span class="text-gray-400 text-sm">EarnApp, Honeygain, Bubble Cash, and other passive-income reviews.</span>
                </a>
            </div>
            <!-- /tp-seo:hub-split -->
        </section>""",
        "landmarks lede",
    )
    if "tp-seo:state-jump" not in text:
        jump = """
        <!-- tp-seo:state-jump -->
        <nav class="mb-10 flex flex-wrap gap-2" aria-label="States and cities">
            <a class="px-3 py-1 rounded-full border border-white/10 text-sm text-gray-200 hover:border-teal-400" href="/AL/">Alabama</a>
            <a class="px-3 py-1 rounded-full border border-white/10 text-sm text-gray-200 hover:border-teal-400" href="/CO/">Colorado</a>
            <a class="px-3 py-1 rounded-full border border-white/10 text-sm text-gray-200 hover:border-teal-400" href="/HI/">Hawaii</a>
            <a class="px-3 py-1 rounded-full border border-white/10 text-sm text-gray-200 hover:border-teal-400" href="/IA/">Iowa</a>
            <a class="px-3 py-1 rounded-full border border-white/10 text-sm text-gray-200 hover:border-teal-400" href="/IN/">Indiana</a>
            <a class="px-3 py-1 rounded-full border border-white/10 text-sm text-gray-200 hover:border-teal-400" href="/KS/">Kansas</a>
            <a class="px-3 py-1 rounded-full border border-white/10 text-sm text-gray-200 hover:border-teal-400" href="/KY/">Kentucky</a>
            <a class="px-3 py-1 rounded-full border border-white/10 text-sm text-gray-200 hover:border-teal-400" href="/LA/">Louisiana</a>
            <a class="px-3 py-1 rounded-full border border-white/10 text-sm text-gray-200 hover:border-teal-400" href="/MI/">Michigan</a>
            <a class="px-3 py-1 rounded-full border border-white/10 text-sm text-gray-200 hover:border-teal-400" href="/OR/">Oregon</a>
            <a class="px-3 py-1 rounded-full border border-white/10 text-sm text-gray-200 hover:border-teal-400" href="/WV/">West Virginia</a>
            <a class="px-3 py-1 rounded-full border border-white/10 text-sm text-gray-200 hover:border-teal-400" href="/WY/">Wyoming</a>
            <a class="px-3 py-1 rounded-full border border-teal-400/40 text-sm text-teal-200 hover:border-teal-300" href="/pages/landmarks/denver/">Denver</a>
            <a class="px-3 py-1 rounded-full border border-teal-400/40 text-sm text-teal-200 hover:border-teal-300" href="/pages/landmarks/vail/">Vail</a>
        </nav>
        <!-- /tp-seo:state-jump -->
"""
        text = text.replace(
            '        <!-- Directory Search & Header -->',
            jump + '        <!-- Directory Search & Header -->',
            1,
        )
    if "tp-seo:featured-co" not in text:
        featured = """
                    <!-- tp-seo:featured-co -->
                    <a href="/pages/eagle-statue/" class="link-item block py-2 px-3 -mx-3 rounded-lg text-sm text-gray-300">American Eagle Statue (Lakewood)</a>
                    <a href="/pages/albert-einstein-statue-vail-co/" class="link-item block py-2 px-3 -mx-3 rounded-lg text-sm text-gray-300">Albert Einstein Statue (Vail)</a>
                    <a href="/pages/bronco-buster-statue/" class="link-item block py-2 px-3 -mx-3 rounded-lg text-sm text-gray-300">Bronco Buster Statue (Denver)</a>
                    <a href="/pages/the-lady-doctor-statue/" class="link-item block py-2 px-3 -mx-3 rounded-lg text-sm text-gray-300">The Lady Doctor Statue (Denver)</a>
                    <a href="/pages/man-and-woman/" class="link-item block py-2 px-3 -mx-3 rounded-lg text-sm text-gray-300">Man and Woman (Denver)</a>
                    <a href="/pages/things-to-do-in-vail-colorado/" class="link-item block py-2 px-3 -mx-3 rounded-lg text-sm text-gray-300">Things to Do in Vail</a>
                    <a href="/pages/landmarks/denver/" class="link-item block py-2 px-3 -mx-3 rounded-lg text-sm text-teal-300">Denver city page</a>
                    <a href="/pages/landmarks/vail/" class="link-item block py-2 px-3 -mx-3 rounded-lg text-sm text-teal-300">Vail city page</a>
                    <!-- /tp-seo:featured-co -->
"""
        needle = '                <div class="flex-grow space-y-1 overflow-y-auto max-h-[400px] pr-2 custom-scrollbar">\n'
        text = text.replace(needle, needle + featured, 1)
    text = text.replace(
        'href="https://testedprofit.com/CO/Landmarks/Bear-Statue/"',
        'href="/pages/bear-statue/"',
    )
    text = text.replace(
        'href="https://testedprofit.com/superbowlsalesteam/" class="link-item block py-2 px-3 -mx-3 rounded-lg text-sm text-gray-300">Broncos Super Bowl LX Parade</a>',
        'href="/pages/guides/" class="link-item block py-2 px-3 -mx-3 rounded-lg text-sm text-gray-300">Earning-app guides</a>',
    )
    if 'href="/pages/guides/" class="text-xs font-bold uppercase tracking-widest text-white hover:text-emerald-300 transition-colors">Guides</a>' not in text:
        text = text.replace(
            '<a href="https://testedprofit.com/pages/landmarks/" target="_blank" class="text-xs font-bold uppercase tracking-widest text-emerald-400 hover:text-emerald-300 transition-colors">Landmarks</a>',
            '<a href="/pages/landmarks/" class="text-xs font-bold uppercase tracking-widest text-emerald-400 hover:text-emerald-300 transition-colors">Landmarks</a>\n                <a href="/pages/guides/" class="text-xs font-bold uppercase tracking-widest text-white hover:text-emerald-300 transition-colors">Guides</a>',
            1,
        )
        text = text.replace(
            '<a href="https://testedprofit.com/pages/landmarks/" class="text-xl font-black text-emerald-400 uppercase tracking-widest hover:text-emerald-300 transition-colors">Landmarks</a>',
            '<a href="/pages/landmarks/" class="text-xl font-black text-emerald-400 uppercase tracking-widest hover:text-emerald-300 transition-colors">Landmarks</a>\n            <a href="/pages/guides/" class="text-xl font-black text-white uppercase tracking-widest hover:text-emerald-300 transition-colors">Guides</a>',
            1,
        )
    return text


def patch_parks(text):
    needle = """            <p class="text-xl md:text-2xl text-gray-400 max-w-2xl mx-auto mb-12 font-light leading-relaxed">
                We construct the digital footprints for public sculptures and landmarks, ensuring our culture is recognized by the AI systems of tomorrow.
            </p>"""
    insert = """            <p class="text-xl md:text-2xl text-gray-400 max-w-2xl mx-auto mb-6 font-light leading-relaxed">
                We construct the digital footprints for public sculptures and landmarks, ensuring our culture is recognized by the AI systems of tomorrow.
            </p>
            <p class="text-base mb-12"><a href="/pages/landmarks/">Browse statues and landmarks by state</a> · <a href="/pages/guides/">Earning-app guides</a></p>"""
    if needle in text:
        text = text.replace(needle, insert, 1)
    elif "Browse statues and landmarks by state" not in text:
        raise SystemExit("parks lede not found")
    return text


def state_cards(pages):
    missing = ["AL", "IA", "MI", "KS"]
    colors = {
        "AL": ("rose", "Alabama"),
        "IA": ("amber", "Iowa"),
        "MI": ("cyan", "Michigan"),
        "KS": ("lime", "Kansas"),
    }
    cards = []
    for code in missing:
        links = []
        for rel, text in sorted(pages.items()):
            if "tp-seo:redirect" in text:
                continue
            if not (rel == code or rel.startswith(code + "/")):
                continue
            if rel == code:
                continue
            links.append(
                f'<a href="{esc(public_path(rel))}" class="link-item block py-2 px-3 -mx-3 rounded-lg text-sm text-gray-300">{esc(label_of(text, rel.split("/")[-1]))}</a>'
            )
        tone = colors[code][0]
        cards.append(
            f"""
            <!-- tp-seo:state-card-{code} -->
            <div class="state-card card-blur rounded-3xl p-8 flex flex-col h-full" data-state="{colors[code][1].lower()}">
                <div class="flex items-center gap-4 mb-6 border-b border-white/10 pb-4">
                    <div class="w-10 h-10 rounded-lg bg-{tone}-500/10 text-{tone}-300 flex items-center justify-center font-bold border border-{tone}-500/20">{code}</div>
                    <h3 class="font-display text-xl font-bold text-white"><a href="{public_path(code)}">{colors[code][1]}</a></h3>
                </div>
                <div class="flex-grow space-y-1 overflow-y-auto max-h-[400px] pr-2 custom-scrollbar">
                    {''.join(links)}
                </div>
            </div>
"""
        )
    block = "\n".join(cards)
    if "tp-seo:state-card-AL" in pages["pages/landmarks"]:
        return pages["pages/landmarks"]
    return pages["pages/landmarks"].replace(
        "            <!-- GENERAL & TOOLS -->",
        block + "\n            <!-- GENERAL & TOOLS -->",
        1,
    )


def shell(title, canonical, description, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{esc(title)}</title>
    <link rel="canonical" href="{esc(canonical)}">
    <meta name="description" content="{esc(description)}">
    <meta property="og:type" content="website">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(description)}">
    <meta property="og:url" content="{esc(canonical)}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; font-family: Inter, system-ui, sans-serif; background: #0A091B; color: #E5E7EB; }}
        a {{ color: #5eead4; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        header {{ display: flex; justify-content: space-between; gap: 1rem; align-items: center; padding: 1rem 1.25rem; border-bottom: 1px solid rgba(255,255,255,.08); }}
        header nav {{ display: flex; gap: 1rem; font-size: .8rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }}
        main {{ max-width: 960px; margin: 0 auto; padding: 1.5rem 1.25rem 3rem; }}
        h1 {{ font-size: clamp(1.8rem, 4vw, 2.7rem); line-height: 1.15; margin: 0 0 .75rem; }}
        .lede {{ color: #9CA3AF; font-size: 1.05rem; max-width: 42rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: .75rem; margin-top: 1.5rem; }}
        .card {{ display: block; padding: 1rem; border: 1px solid rgba(255,255,255,.08); border-radius: 14px; background: rgba(255,255,255,.03); color: inherit; }}
        .card:hover {{ border-color: rgba(45,212,191,.5); text-decoration: none; }}
        .card strong {{ display: block; color: white; margin-bottom: .25rem; }}
        .card span {{ color: #9CA3AF; font-size: .92rem; }}
        .crumbs {{ display: flex; flex-wrap: wrap; gap: .35rem .5rem; list-style: none; padding: 0; margin: 0 0 1.25rem; font-size: .85rem; }}
        .crumbs li + li::before {{ content: "/"; color: #64748b; margin-right: .5rem; }}
        footer {{ border-top: 1px solid rgba(255,255,255,.06); color: #64748b; font-size: .85rem; padding: 1.5rem; text-align: center; }}
    </style>
</head>
<body>
    <header>
        <a href="/" style="color:white;font-weight:800;">TestedProfit</a>
        <nav>
            <a href="/pages/landmarks/">Landmarks</a>
            <a href="/pages/guides/">Earning guides</a>
        </nav>
    </header>
    <main>
{body}
    </main>
    <footer>Statues and landmarks are catalogued separately from earning-app guides.</footer>
</body>
</html>
"""


def crumbs_nav(items):
    bits = ['<ol class="crumbs">']
    for label, href in items[:-1]:
        bits.append(f'<li><a href="{esc(href)}">{esc(label)}</a></li>')
    bits.append(f'<li aria-current="page">{esc(items[-1][0])}</li>')
    bits.append("</ol>")
    return "\n".join(bits)


def write_state_indexes(pages):
    for code, name in STATES.items():
        # Colorado, Hawaii, and Kentucky already have hand-built directories.
        if code in {"CO", "HI", "KY"}:
            continue
        cards = []
        for rel, text in sorted(pages.items(), key=lambda item: label_of(item[1], item[0]).lower()):
            if "tp-seo:redirect" in text:
                continue
            if rel == code or not rel.startswith(code + "/"):
                continue
            cards.append(
                f'<a class="card" href="{esc(public_path(rel))}"><strong>{esc(label_of(text, rel.split("/")[-1]))}</strong><span>{esc(description_of(text)[:140])}</span></a>'
            )
        body = f"""        <!-- tp-seo:state-index -->
        {crumbs_nav([("Home", "/"), ("Landmarks", "/pages/landmarks/"), (name, public_path(code))])}
        <h1>{esc(name)} statues and landmarks</h1>
        <p class="lede">Every {esc(name)} page already on this site. Nothing here was moved. Earning-app guides are listed separately.</p>
        <p><a href="/pages/landmarks/">All states</a> · <a href="/pages/guides/">Earning guides</a></p>
        <div class="grid">
            {''.join(cards) or '<p>No landmark pages in this state yet.</p>'}
        </div>
"""
        title = f"{name} Statues and Landmarks | TestedProfit"
        description = f"Public statues, sculptures, and parks in {name}, with links to each existing TestedProfit page."
        write(code, shell(title, f"https://testedprofit.com/{code}/", description, body))


def write_city_and_guides(pages):
    denver = [
        ("pages/eagle-statue", "Lakewood, at Denver West Plaza. Often confused with the Nicolosi eagle on the City and County Building."),
        ("pages/bronco-buster-statue", "Civic Center Park. Alexander Phimister Proctor's Bronco Buster, not the Denver Broncos stadium horse."),
        ("pages/the-lady-doctor-statue", "Dr. Justina Ford, the Lady Doctor, and her Five Points house."),
        ("pages/man-and-woman", "The Man and Woman sculpture in Denver."),
        ("pages/madre-e-hijo-sculpture", "Madre e Hijo, a Denver-area sculpture guide."),
        ("pages/the-newsboy-statue", "The Newsboy in Golden, west of Denver."),
        ("pages/goldens-vibrant-triceratops", "The triceratops sculpture in Golden."),
        ("pages/torii-square-park-westminster", "Torii Square Park in Westminster."),
        ("pages/sensory-park", "Sensory Park in Westminster."),
        ("pages/sunset-park", "Sunset Park in Westminster."),
    ]
    vail = [
        ("pages/albert-einstein-statue-vail-co", "Gary Lee Price's bronze Einstein bench in Vail Village."),
        ("pages/things-to-do-in-vail-colorado", "Visitor guide to things to do in Vail."),
        ("pages/things to do in vail colorado", "A second, budget-focused Vail guide. Kept at its own URL."),
    ]

    def cards(rows):
        out = []
        for rel, blurb in rows:
            text = pages.get(rel, "")
            label = label_of(text, rel) if text else rel
            out.append(
                f'<a class="card" href="{esc(public_path(rel))}"><strong>{esc(label)}</strong><span>{esc(blurb)}</span></a>'
            )
        return "".join(out)

    denver_body = f"""        {crumbs_nav([("Home", "/"), ("Landmarks", "/pages/landmarks/"), ("Colorado", "/CO/"), ("Denver", "/pages/landmarks/denver/")])}
        <h1>Denver statues and public art</h1>
        <p class="lede">The Denver metro pages people search for: the American eagle statue, the Bronco Buster, and the Lady Doctor statue, plus nearby Golden and Westminster stops.</p>
        <div class="grid">{cards(denver)}</div>
"""
    vail_body = f"""        {crumbs_nav([("Home", "/"), ("Landmarks", "/pages/landmarks/"), ("Colorado", "/CO/"), ("Vail", "/pages/landmarks/vail/")])}
        <h1>Vail statues and things to do</h1>
        <p class="lede">The Albert Einstein statue in Vail Village, and the existing Vail visitor guides.</p>
        <div class="grid">{cards(vail)}</div>
"""
    write(
        "pages/landmarks/denver",
        shell(
            "Denver Statues and Public Art | TestedProfit",
            "https://testedprofit.com/pages/landmarks/denver/",
            "Denver metro statues and public art on TestedProfit, including the American eagle statue, Bronco Buster, and Dr. Justina Ford.",
            denver_body,
        ),
    )
    write(
        "pages/landmarks/vail",
        shell(
            "Vail Statues and Things to Do | TestedProfit",
            "https://testedprofit.com/pages/landmarks/vail/",
            "The Albert Einstein statue in Vail, Colorado, plus the existing Vail visitor guides.",
            vail_body,
        ),
    )

    guide_cards = []
    for rel in GUIDES:
        text = pages.get(rel, "")
        if not text:
            continue
        guide_cards.append(
            f'<a class="card" href="{esc(public_path(rel))}"><strong>{esc(label_of(text, rel))}</strong><span>{esc(description_of(text)[:160])}</span></a>'
        )
    guides_body = f"""        {crumbs_nav([("Home", "/"), ("Earning guides", "/pages/guides/")])}
        <h1>Earning-app guides</h1>
        <p class="lede">Reviews and practical guides for EarnApp, Honeygain, Bubble Cash, and related passive-income topics. This section is separate from the statue directory. AlgoFlow tools stay on their existing pages.</p>
        <p><a href="/pages/landmarks/">Statues and landmarks</a> · <a href="/pages/algoflow/">AlgoFlow tools</a></p>
        <div class="grid">{''.join(guide_cards)}</div>
"""
    write(
        "pages/guides",
        shell(
            "Earning-App Guides | TestedProfit",
            "https://testedprofit.com/pages/guides/",
            "Separate from the statue directory: EarnApp, Honeygain, Bubble Cash, and other earning guides on TestedProfit.",
            guides_body,
        ),
    )


def write_preview(records):
    eagle = read("pages/eagle-statue")
    samples = []
    for rel in [
        "pages/eagle-statue",
        "pages/albert-einstein-statue-vail-co",
        "pages/bronco-buster-statue",
        "pages/the-lady-doctor-statue",
    ]:
        text = read(rel)
        samples.append(
            f"<tr><td><a href=\"{esc(public_path(rel))}\">{esc(rel)}</a></td><td>{esc(label_of(text, rel))}</td><td>{esc(description_of(text))}</td></tr>"
        )
    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Preview: TestedProfit SEO structure</title>
    <meta name="robots" content="noindex, nofollow">
    <style>
        body {{ margin: 0; font-family: Inter, system-ui, sans-serif; background: #f8fafc; color: #0f172a; }}
        main {{ max-width: 980px; margin: 0 auto; padding: 2rem 1.25rem 3rem; }}
        h1 {{ font-size: 2rem; margin-bottom: .25rem; }}
        a {{ color: #0f766e; }}
        .ok {{ background: #ecfdf5; border: 1px solid #6ee7b7; border-radius: 12px; padding: 1rem 1.1rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: .75rem; margin: 1rem 0 1.5rem; }}
        .card {{ display: block; background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; color: inherit; text-decoration: none; }}
        .card strong {{ display: block; margin-bottom: .3rem; }}
        table {{ width: 100%; border-collapse: collapse; background: white; }}
        th, td {{ border: 1px solid #e2e8f0; padding: .55rem .6rem; vertical-align: top; font-size: .92rem; }}
        code {{ font-size: .85rem; }}
    </style>
</head>
<body>
<main>
    <h1>Preview before merge</h1>
    <p>Open these pages from a local server at the repository root, or from GitHub's file view. GitHub Pages deploys only <code>main</code>, so this branch has no live preview URL on testedprofit.com.</p>
    <div class="ok">
        <strong>Homepage unchanged.</strong>
        <p>The AlgoFlow landing page at <a href="/">/</a> was not edited. SHA-256 of <code>index.html</code>:</p>
        <p><code>{HOME_HASH}</code></p>
    </div>
    <h2>New structure</h2>
    <div class="grid">
        <a class="card" href="/pages/landmarks/"><strong>Landmarks hub</strong><span>States, Denver, Vail, and a separate link to earning guides.</span></a>
        <a class="card" href="/AL/"><strong>Alabama category</strong><span>New state page. Existing statue URLs are linked, not moved.</span></a>
        <a class="card" href="/CO/"><strong>Colorado category</strong><span>Existing Colorado directory, now with breadcrumbs.</span></a>
        <a class="card" href="/pages/landmarks/denver/"><strong>Denver city page</strong><span>Eagle, Bronco Buster, Lady Doctor, and nearby statues.</span></a>
        <a class="card" href="/pages/landmarks/vail/"><strong>Vail city page</strong><span>Einstein statue and the Vail guides.</span></a>
        <a class="card" href="/pages/guides/"><strong>Earning-app guides</strong><span>EarnApp, Honeygain, Bubble Cash, and the other reviews.</span></a>
        <a class="card" href="/pages/eagle-statue/"><strong>Sample landmark</strong><span>New title, description, breadcrumb, and related links.</span></a>
    </div>
    <h2>Titles and descriptions on high-impression pages</h2>
    <table>
        <tr><th>Page</th><th>Title</th><th>Meta description</th></tr>
        {''.join(samples)}
    </table>
    <h2>Sample breadcrumb</h2>
    <p>On the eagle statue page the visible trail is Home / Landmarks / Colorado / American Eagle Statue at Denver West Plaza, Lakewood CO. Related links point at the Einstein statue, the Bronco Buster, and the Lady Doctor statue.</p>
    <p>Landmark pages with the new breadcrumb: {len(records)} existing pages, plus the new state and city pages.</p>
    <h2>Redirects added in this branch</h2>
    <ul>
        <li><a href="/pages/earnapp-definitive-review-philippines/">/pages/earnapp-definitive-review-philippines/</a> → /pages/earnapp/</li>
        <li><a href="/pages/cedar-mountain-craig-co-local-guide/">/pages/cedar-mountain-craig-co-local-guide/</a> → /CO/Landmarks/Cedar-Mountain/</li>
        <li><a href="/pages/rotary-park/">/pages/rotary-park/</a> → /rotary-park/</li>
        <li><a href="/pages/woodbury-park/">/pages/woodbury-park/</a> → /pages/Woodbury Park/</li>
        <li><a href="/tokenomics/">/tokenomics/</a> → /pages/tokenomics/</li>
        <li><a href="/CO/Landmarks/Bear-Statue/">/CO/Landmarks/Bear-Statue/</a> → /pages/bear-statue/ (exact duplicate)</li>
        <li><a href="/blogs/news/">/blogs/news/</a> → /pages/guides/</li>
    </ul>
</main>
</body>
</html>
"""
    preview = ROOT / "preview" / "index.html"
    preview.parent.mkdir(parents=True, exist_ok=True)
    preview.write_text(body, encoding="utf-8")
    # silence unused in case the eagle read is only for a future assertion
    if "American Eagle Statue" not in eagle:
        raise SystemExit("eagle title was not updated before preview")


def main():
    pages = collect_pages()
    apply_copy_fixes(pages)
    pages["pages/landmarks"] = patch_landmarks_hub(pages["pages/landmarks"])
    pages["pages/parks"] = patch_parks(pages["pages/parks"])
    pages["pages/landmarks"] = state_cards(pages)

    for rel, target in REDIRECTS.items():
        write(rel, redirect_html(target))
        pages.pop(rel, None)

    # Write edited existing pages except homepage before injections that need fresh labels.
    for rel, text in pages.items():
        if rel == "":
            continue
        write(rel, text)

    pages = collect_pages()
    records = landmark_records(pages)
    by_rel = {item["rel"]: item for item in records}

    for rel, text in list(pages.items()):
        if rel == "" or "tp-seo:redirect" in text:
            continue
        if rel.startswith("conservation-fund/"):
            continue
        kind = None
        if rel in GUIDES:
            kind = "guide"
        elif is_landmark(rel) and rel not in {"pages/landmarks/denver", "pages/landmarks/vail"}:
            kind = "landmark"
        if not kind:
            continue
        if rel in {"pages/guides"}:
            continue
        label = title_label(text, rel.split("/")[-1])
        crumbs = crumb_html(crumbs_for(rel, label))
        related = ""
        if rel not in {"pages/landmarks"} and rel not in STATES:
            if kind == "guide":
                others = []
                for other in GUIDES:
                    if other == rel or other not in pages:
                        continue
                    others.append((label_of(pages[other], other), public_path(other)))
                others = sorted(others, key=lambda item: item[0].lower())[:5]
                related = related_html(
                    "More earning guides",
                    others,
                    "/pages/landmarks/",
                    "Statues and landmarks are a separate section.",
                )
            else:
                links = [(item["label"], item["href"]) for item in siblings(records, rel)]
                if not links and rel in by_rel:
                    links = [("All landmarks", "/pages/landmarks/")]
                state = state_of(rel)
                note_href = public_path(state) if state in STATES else "/pages/landmarks/"
                note = f"All {STATES.get(state, 'landmark')} pages" if state in STATES else "All landmarks"
                if city_of(rel) == "Vail":
                    note_href = "/pages/landmarks/vail/"
                    note = "Vail city page"
                elif city_of(rel) in {"Denver", "Denver metro"}:
                    note_href = "/pages/landmarks/denver/"
                    note = "Denver city page"
                related = related_html("Related landmarks", links, note_href, note) if links else ""
        elif rel in STATES:
            others = [(STATES[code], public_path(code)) for code in STATES if code != rel][:6]
            related = related_html(
                "Other states",
                others,
                "/pages/guides/",
                "Earning-app guides are a separate section.",
            )
        pages[rel] = inject(text, crumbs, related)
        write(rel, pages[rel])

    pages = collect_pages()
    write_state_indexes(pages)
    write_city_and_guides(pages)
    from generate_sitemap import generate_sitemap

    generate_sitemap()
    pages = collect_pages()
    records = landmark_records(pages)
    write_preview(records)

    if hashlib.sha256(HOME.read_bytes()).hexdigest() != HOME_HASH:
        raise SystemExit("homepage hash changed")
    print(f"Homepage hash unchanged: {HOME_HASH}")
    print(f"Landmark records: {len(records)}")


if __name__ == "__main__":
    main()

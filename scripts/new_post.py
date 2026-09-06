#!/usr/bin/env python3
"""
new_post.py - turn a Markdown file with simple front matter into a
docs/blog/<slug>.html page, using the same template/classes as the hand-written
sample posts (docs/blog/*.html) and the "calm mode" reading theme
(docs/assets/css/blog.css).

This is an AUTHORING convenience run manually by hand when adding a post - it
does NOT run at serve time and does not require a build step for the site
itself. Standard library only, no pip packages.

------------------------------------------------------------------------------
USAGE

    python scripts/new_post.py path/to/post.md
    python scripts/new_post.py path/to/post.md --slug custom-slug
    python scripts/new_post.py path/to/post.md --no-listing
    python scripts/new_post.py path/to/post.md \
        --prev-slug hardening-air-gapped-kubernetes \
        --prev-title "A Practical Checklist for Hardening Air-Gapped Kubernetes" \
        --next-slug gitops-in-regulated-environments \
        --next-title "GitOps in Regulated Environments: What Actually Changes"

Run it from anywhere; paths are resolved relative to the repo root (this
script's parent directory), so it always writes into docs/blog/ regardless of
your current working directory.

------------------------------------------------------------------------------
FRONT MATTER FORMAT

The Markdown file must start with a '---' fenced block of "key: value" lines:

    ---
    title: A Practical Checklist for Hardening Air-Gapped Kubernetes
    date: 2026-07-18
    category: Technical
    tags: Kubernetes, Security
    description: A one-sentence summary used in <meta description>, the
      social card, and the blog listing excerpt.
    slug: hardening-air-gapped-kubernetes
    ---

    The Markdown body starts here...

Recognised keys:
    title        required
    date         required, YYYY-MM-DD
    description  required (used for SEO meta + listing excerpt)
    category     optional, single value, defaults to "Technical". Drives the
                 category label + data-category on the listing row and the
                 blog.html filter bar. Any new value "just works" (e.g.
                 "Astronomy", "Stories") - add a matching chip to blog.html's
                 .post-filter if you want it pinned in a fixed order.
    tags         optional, comma-separated, 0-3 recommended (fine-grained topic
                 chips on the post page; distinct from the single category)
    slug         optional - derived from the title if omitted

------------------------------------------------------------------------------
MARKDOWN SUPPORT

Deliberately minimal - just what this project's posts actually use:
headings (## / ###), paragraphs, **bold**, *italic*, `inline code`,
[links](url), fenced ``` code blocks ```, > blockquotes, - / 1. lists,
and --- horizontal rules. Nothing more exotic than that; if you need it,
write the HTML by hand for that one spot.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path
from string import Template

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
BLOG_DIR = DOCS / "blog"
BLOG_INDEX = DOCS / "blog.html"
SITE_URL = "https://sarthak044.github.io/sarthak-kul"
WORDS_PER_MINUTE = 200

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
MONTHS_SHORT = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

DEFAULT_CATEGORY = "Technical"


# ---------------------------------------------------------------------------
# Front matter
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def parse_front_matter(raw: str) -> tuple[dict, str]:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SystemExit("error: markdown file must start with a '---' front-matter block")
    meta: dict[str, str] = {}
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        line = lines[i]
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip().lower()] = value.strip()
        i += 1
    if i >= len(lines):
        raise SystemExit("error: front matter is missing its closing '---'")
    body = "\n".join(lines[i + 1:]).lstrip("\n")
    return meta, body


def parse_date(value: str) -> tuple[str, str, str]:
    """Return (iso, human_long, human_short).

    e.g. ('2026-07-18', 'July 18, 2026', 'Jul 18, 2026'). The reading page uses
    the long form (matching the hand-written sample posts); the compact listing
    row uses the short form (matching the hand-written rows in blog.html).
    """
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", value.strip())
    if not m:
        raise SystemExit(f"error: date '{value}' must be YYYY-MM-DD")
    year, month, day = (int(g) for g in m.groups())
    if not (1 <= month <= 12):
        raise SystemExit(f"error: date '{value}' has an invalid month")
    human_long = f"{MONTHS[month - 1]} {day}, {year}"
    human_short = f"{MONTHS_SHORT[month - 1]} {day}, {year}"
    return value.strip(), human_long, human_short


# ---------------------------------------------------------------------------
# A small, deliberately simple Markdown -> HTML converter — just the subset
# this project's posts actually use. Not a general-purpose parser.
# ---------------------------------------------------------------------------

def render_inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


BLOCK_START = re.compile(r"^(#{2,3}\s|```|>|[-*]\s|\d+\.\s|-{3,}$)")


def render_markdown(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i, n = 0, len(lines)

    def flush_list(items: list[str], ordered: bool) -> None:
        tag = "ol" if ordered else "ul"
        out.append(f"<{tag}>")
        for item in items:
            out.append(f"  <li>{render_inline(item)}</li>")
        out.append(f"</{tag}>")

    while i < n:
        stripped = lines[i].strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            code = html.escape("\n".join(code_lines), quote=False)
            out.append(f"<pre><code>{code}</code></pre>")
            continue

        m = re.match(r"^(#{2,3})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{render_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        if re.match(r"^-{3,}$", stripped):
            out.append("<hr />")
            i += 1
            continue

        if stripped.startswith(">"):
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f"<blockquote><p>{render_inline(' '.join(quote))}</p></blockquote>")
            continue

        if re.match(r"^[-*]\s+", stripped):
            items = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            flush_list(items, ordered=False)
            continue

        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            flush_list(items, ordered=True)
            continue

        para = [stripped]
        i += 1
        while i < n and lines[i].strip() and not BLOCK_START.match(lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{render_inline(' '.join(para))}</p>")

    return "\n        ".join(out)


def estimate_read_minutes(text: str) -> int:
    words = len(re.findall(r"\S+", text))
    return max(1, round(words / WORDS_PER_MINUTE))


# ---------------------------------------------------------------------------
# Templates (string.Template — $-substitution avoids brace-escaping the CSS
# selectors / JSON-LD braces that a str.format template would need)
# ---------------------------------------------------------------------------

POST_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en" class="no-js">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="color-scheme" content="dark" />
  <meta name="theme-color" content="#181a1e" />

  <title>$title — Sarthak Kulshrestha</title>
  <meta name="description" content="$description" />
  <meta name="author" content="Sarthak Kulshrestha" />

  <link rel="canonical" href="$canonical" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="Sarthak Kulshrestha" />
  <meta property="og:title" content="$title" />
  <meta property="og:description" content="$description" />
  <meta property="og:image" content="../assets/img/og-image.png" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:alt" content="Sarthak Kulshrestha — Senior DevSecOps Engineer" />
  <meta property="og:url" content="$canonical" />
  <meta property="article:published_time" content="$date_iso" />
  <meta property="article:author" content="Sarthak Kulshrestha" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="$title" />
  <meta name="twitter:description" content="$description" />
  <meta name="twitter:image" content="../assets/img/og-image.png" />
  <meta name="twitter:image:alt" content="Sarthak Kulshrestha — Senior DevSecOps Engineer" />

  <link rel="icon" href="../assets/img/favicon.svg" type="image/svg+xml" />
  <link rel="apple-touch-icon" href="../assets/img/favicon.svg" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Inter:wght@400;500;600&family=Share+Tech+Mono&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet" />

  <script>document.documentElement.classList.replace('no-js', 'js');</script>
  <link rel="stylesheet" href="../assets/css/style.css" />
  <link rel="stylesheet" href="../assets/css/blog.css" />

  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "headline": "$title_json",
    "description": "$description_json",
    "datePublished": "$date_iso",
    "author": { "@type": "Person", "name": "Sarthak Kulshrestha", "url": "$site_url/" },
    "publisher": { "@type": "Person", "name": "Sarthak Kulshrestha" },
    "mainEntityOfPage": "$canonical",
    "url": "$canonical"
  }
  </script>
</head>
<body class="calm">
  <a class="skip-link" href="#main">Skip to content</a>

  <header class="hud" id="top">
    <div class="hud-inner">
      <a class="sigil" href="../index.html" aria-label="Sarthak Kulshrestha — hub">
        <svg class="sigil-mark" viewBox="0 0 32 32" aria-hidden="true" focusable="false">
          <path d="M4 7 L16 2 L28 7 L28 21 L16 30 L4 21 Z" fill="none" stroke="currentColor" stroke-width="1.4"/>
          <path d="M12 11 H21 M12 11 V16 H20 M12 21 H21 M20 16 V21" fill="none" stroke="currentColor" stroke-width="2.4"/>
        </svg>
        <span class="sigil-text">SK<b>//</b>SYS</span>
      </a>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="hud-nav" aria-label="Open menu">
        <span></span><span></span><span></span>
      </button>
      <nav id="hud-nav" class="hud-nav" aria-label="Primary">
        <ul>
          <li><a href="../about.html">About</a></li>
          <li><a href="../experience.html">Experience</a></li>
          <li><a href="../skills.html">Skills</a></li>
          <li><a href="../certifications.html">Certs</a></li>
          <li><a href="../education.html">Education</a></li>
          <li><a href="../contact.html">Contact</a></li>
          <li><a href="../blog.html" aria-current="page">Blog</a></li>
        </ul>
      </nav>
      <p class="hud-readout" aria-hidden="true"><span class="hud-dot"></span> LINK OK <span class="hud-clock" data-clock>--:--</span></p>
    </div>
  </header>

  <main id="main">
    <article class="read">
      <header class="post-header">
        <p class="calm-kicker">Field notes</p>
        <h1>$title</h1>
        <p class="post-meta">
          <time datetime="$date_iso">$date_human</time>
          <span class="dot">&middot;</span> $read_minutes min read
          <span class="dot">&middot;</span> Sarthak Kulshrestha
          <span class="dot">&middot;</span> <span class="post-meta-cat">$category</span>
        </p>$tags_block
      </header>

      <div class="post-body">
        $body_html
      </div>

      <footer class="post-footer">
$post_nav_block        <a class="back-to-blog" href="../blog.html">&larr; Back to Blog</a>
      </footer>
    </article>
  </main>

  <footer class="dock">
    <div class="dock-inner">
      <p class="dock-copy">&copy; <span data-year>2026</span> Sarthak Kulshrestha &middot; field notes</p>
      <nav class="dock-links" aria-label="Profiles and résumé">
        <a href="../assets/sarthak-kulshrestha-resume.pdf" download>Résumé</a>
        <a href="https://www.linkedin.com/in/sarthak-kul/" target="_blank" rel="noopener noreferrer">LinkedIn</a>
        <a href="https://github.com/Sarthak044" target="_blank" rel="noopener noreferrer">GitHub</a>
        <a href="https://medium.com/@shinobishuuz" target="_blank" rel="noopener noreferrer">Medium</a>
      </nav>
      <a class="dock-top" href="#top">&#9650; TOP</a>
    </div>
  </footer>

  <script src="../assets/js/main.js" defer></script>
</body>
</html>
""")

LISTING_ITEM_TEMPLATE = Template(
    '        <li class="post-row" data-category="$category_slug">\n'
    '          <p class="post-row-date"><time datetime="$date_iso">$date_human_short</time></p>\n'
    '          <h2 class="post-row-title"><a href="blog/$slug.html">$title</a></h2>\n'
    '          <p class="post-row-desc">$description</p>\n'
    '          <p class="post-row-tail"><span class="post-row-cat">$category</span>'
    '<span class="post-row-read">$read_minutes min read</span></p>\n'
    "        </li>"
)


def json_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def build_post_nav(args: argparse.Namespace) -> str:
    if not args.prev_slug and not args.next_slug:
        return ""
    parts = ['        <nav class="post-nav" aria-label="More posts">\n']
    if args.prev_slug:
        title = args.prev_title or args.prev_slug
        parts.append(
            f'          <div class="post-nav-prev">\n'
            f'            <span>Previous</span>\n'
            f'            <a href="{args.prev_slug}.html">&larr; {html.escape(title, quote=False)}</a>\n'
            f'          </div>\n'
        )
    if args.next_slug:
        title = args.next_title or args.next_slug
        parts.append(
            f'          <div class="post-nav-next">\n'
            f'            <span>Next</span>\n'
            f'            <a href="{args.next_slug}.html">{html.escape(title, quote=False)} &rarr;</a>\n'
            f'          </div>\n'
        )
    parts.append("        </nav>\n")
    return "".join(parts)


def build_tags_block(tags: list[str]) -> str:
    if not tags:
        return ""
    items = "\n".join(f"          <li>{html.escape(t, quote=False)}</li>" for t in tags)
    return f'\n        <ul class="post-tags">\n{items}\n        </ul>'


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("markdown", type=Path, help="Path to the source .md file")
    parser.add_argument("--slug", help="Override the slug derived from the title")
    parser.add_argument("--no-listing", action="store_true", help="Don't touch docs/blog.html")
    parser.add_argument("--prev-slug", help="Slug of the previous post (for the post-footer pager)")
    parser.add_argument("--prev-title", help="Title of the previous post (defaults to its slug)")
    parser.add_argument("--next-slug", help="Slug of the next post (for the post-footer pager)")
    parser.add_argument("--next-title", help="Title of the next post (defaults to its slug)")
    parser.add_argument("--force", action="store_true", help="Overwrite the output file if it already exists")
    args = parser.parse_args()

    md_path: Path = args.markdown
    if not md_path.exists():
        raise SystemExit(f"error: {md_path} does not exist")

    raw = md_path.read_text(encoding="utf-8")
    meta, body_md = parse_front_matter(raw)

    for required in ("title", "date", "description"):
        if not meta.get(required):
            raise SystemExit(f"error: front matter is missing required field '{required}'")

    title = meta["title"]
    description = meta["description"]
    date_iso, date_human, date_human_short = parse_date(meta["date"])
    slug = args.slug or meta.get("slug") or slugify(title)
    tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    category = (meta.get("category") or DEFAULT_CATEGORY).strip() or DEFAULT_CATEGORY
    category_slug = slugify(category)

    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BLOG_DIR / f"{slug}.html"
    if out_path.exists() and not args.force:
        raise SystemExit(f"error: {out_path} already exists (use --force to overwrite)")

    body_html = render_markdown(body_md)
    read_minutes = estimate_read_minutes(body_md)
    canonical = f"{SITE_URL}/blog/{slug}.html"

    post_html = POST_TEMPLATE.substitute(
        title=html.escape(title, quote=True),
        title_json=json_escape(title),
        description=html.escape(description, quote=True),
        description_json=json_escape(description),
        canonical=canonical,
        site_url=SITE_URL,
        date_iso=date_iso,
        date_human=date_human,
        read_minutes=read_minutes,
        category=html.escape(category, quote=True),
        tags_block=build_tags_block(tags),
        body_html=body_html,
        post_nav_block=build_post_nav(args),
    )
    out_path.write_text(post_html, encoding="utf-8", newline="\n")
    print(f"wrote {out_path.relative_to(REPO_ROOT)}")

    if not args.no_listing:
        add_to_listing(slug, title, description, date_iso, date_human_short,
                       read_minutes, category, category_slug)


def add_to_listing(slug: str, title: str, description: str, date_iso: str,
                   date_human_short: str, read_minutes: int, category: str,
                   category_slug: str) -> None:
    if not BLOG_INDEX.exists():
        print(f"warning: {BLOG_INDEX} not found, skipping listing update", file=sys.stderr)
        return
    listing_html = BLOG_INDEX.read_text(encoding="utf-8")
    anchor = "<!-- scripts/new_post.py inserts new <li class=\"post-row\"> entries directly below this line -->"
    if anchor not in listing_html:
        print(f"warning: anchor comment not found in {BLOG_INDEX}, skipping listing update", file=sys.stderr)
        return
    item = LISTING_ITEM_TEMPLATE.substitute(
        slug=slug,
        title=html.escape(title, quote=True),
        date_iso=date_iso,
        date_human_short=date_human_short,
        read_minutes=read_minutes,
        description=html.escape(description, quote=True),
        category=html.escape(category, quote=True),
        category_slug=category_slug,
    )
    listing_html = listing_html.replace(anchor, f"{anchor}\n{item}", 1)
    BLOG_INDEX.write_text(listing_html, encoding="utf-8", newline="\n")
    print(f"updated {BLOG_INDEX.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

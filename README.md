# Sarthak Kulshrestha — Portfolio

A static, multi-page personal portfolio with a **HUD + neon-noir** theme (WayneTech / Arkham
influence): sharp interface panels, corner brackets, live readouts and an amber clearance
accent over a dark, rain-lit background with a bat-signal glow.

**Plain HTML / CSS / JS. No build step, no framework, no npm, no `node_modules`.**
Every page works by opening it directly (`file://`) and when served from the GitHub Pages
project subpath `https://sarthak044.github.io/sarthak-kul/`. All asset and link paths are
relative, and every HTML file is flat inside `docs/` (no nested folders, except one level
for blog posts — see below) so paths never break. The published site lives entirely in
`docs/`; the repo root holds only this README, config, and the optional authoring script
in `scripts/`.

There's also a **Blog** (`docs/blog.html` + `docs/blog/*.html`) with its own calm, distinctly
non-cyberpunk reading theme — infrastructure and security notes, the occasional personal
story, and some astronomy. See "The blog" below.

## Structure

```
docs/                         ← the published site (GitHub Pages serves this folder)
  index.html                  Hub — hero + 6 section portals (brief, atmospheric)
  about.html                  About
  experience.html             Experience — 5 roles, timeline
  skills.html                 Skills — 7 groups
  certifications.html         Certifications — Security + DevOps & Cloud
  education.html              Education — IIT Patna, JECRC University
  contact.html                Contact — email, LinkedIn, GitHub, Medium, résumé
  blog.html                   Blog listing — calm reading theme, compact archive
                               rows, most recent first, category filter bar
  blog/
    stargazing-from-a-light-polluted-city.html
    what-certifications-dont-teach-you.html
    why-i-started-writing-again.html
    gitops-in-regulated-environments.html
    hardening-air-gapped-kubernetes.html
  404.html                    Themed "Signal Lost" page (served for unknown URLs)
  .nojekyll                   Serve the folder as-is, no Jekyll (do not delete)
  assets/css/style.css        Shared HUD/neon-noir stylesheet — every page except the
                               blog's reading column loads only this
  assets/css/blog.css         Calm reading theme — loaded ONLY on blog.html and
                               docs/blog/*.html, in addition to style.css
  assets/js/main.js           One shared script for every page (nav toggle, HUD clock,
                               reduced-motion guards — reused as-is on blog pages)
  assets/img/favicon.svg      Angular "SK" system sigil
  assets/img/og-image.png     1200x630 social share card
  assets/sarthak-kulshrestha-resume.pdf   Downloadable résumé (phone-free)
scripts/
  new_post.py                 Turns a Markdown file into docs/blog/<slug>.html (see below)
```

Every page shares the same HUD top bar, footer dock, and per-page `<title>` / description /
absolute canonical + `og:url`. The active nav link is marked with `aria-current="page"`.
The 8 original pages additionally share the neon-noir ambient background layer; blog pages
deliberately do not (see below).

## The blog

`docs/blog.html` and `docs/blog/*.html` keep the shared HUD top bar (so navigation stays
consistent across the whole site) but everything below it uses a separate, calmer visual
system defined in `assets/css/blog.css` — built for actually reading long-form technical
writing, not for the portfolio's HUD effects:

- Soft charcoal background (`#181a1e`) rather than the neon-noir void, a warm ivory body
  color, and one muted dusty-teal accent used sparingly (links, tags, a thin rule) — no
  neon glow, no `box-shadow` text effects.
- "Source Serif 4" for headings and body copy (loaded only on blog pages), sized for long
  reads (~1.18rem, line-height ~1.78, a ~65–72ch measure).
- No animated grid/rain/scanline ambient layer, no page-enter wipe, no glitch or
  "decode-in" heading scramble — content renders directly. A minimal CSS-only fade-in is
  used on load, skipped entirely under `prefers-reduced-motion`.
- The footer is restyled to the calm palette too; only the HUD bar itself keeps the
  neon-noir look, for wayfinding continuity.
- The listing is a **compact archive**: one uniform-height row per post (short date,
  title link, one-line description, category label, read time) with thin dividers — built
  to stay scannable at 20–30 posts, not stacked cards.

### Categories & the filter bar

Every post has a single **`category`** (front-matter key, defaults to `Technical`) — this
is separate from the fine-grained `tags` that appear as topic chips on the post page. The
current set is **Technical**, **Stories**, and **Astronomy**, but it's data-driven: use a
new value in front matter and it just works — the listing row gets a `data-category` slug
and label, and `main.js` adds a matching chip to the filter bar automatically. (Add a
`<button class="filter-chip" data-filter="…">` to `.post-filter` in `blog.html` only if
you want the new category pinned in a fixed position.)

The filter bar is **progressive enhancement**:

- **JS off:** the bar is hidden; every row stays visible and shows its own category label,
  so the whole archive is still reachable.
- **JS on:** chips are keyboard-operable `<button>`s with `aria-pressed` inside a labelled
  group. Clicking one filters the rows (`hidden` toggled), updates a live count, syncs the
  URL hash (`blog.html#astronomy` is linkable and survives reload), and shows an
  empty-state line for a category with no posts.

### Adding a blog post

Write a Markdown file with a short front-matter block:

```
---
title: Your Post Title
date: 2026-09-01
category: Technical
tags: Kubernetes, Security
description: One sentence used in the meta tags and the listing excerpt.
---

Your Markdown body goes here — headings (## / ###), paragraphs, **bold**, *italic*,
`inline code`, [links](https://example.com), fenced ``` code blocks ```, > blockquotes,
- bullet lists, 1. numbered lists, and --- rules are all supported.
```

Then run:

```
python scripts/new_post.py path/to/your-post.md
```

This writes `docs/blog/<slug>.html` (slug derived from the title, or set `slug:` in the
front matter / pass `--slug`) using the same template as the sample posts, and prepends a
compact listing row (with `data-category`) to `docs/blog.html`. `category` defaults to
`Technical` if omitted. Pass `--no-listing` to skip the listing update, or
`--prev-slug/--prev-title/--next-slug/--next-title` to wire up the post-footer pager. It's
stdlib-only Python (no pip packages) and is an authoring convenience run by hand — it does
not run at serve time and does not introduce a build step. Run `python scripts/new_post.py
--help` for the full option list.

## Behaviour & accessibility

- Fully usable with JavaScript disabled. JS only adds: the HUD clock, the page-enter wipe,
  the mobile nav toggle, scroll reveals, heading "decode-in", and the hero typing effect.
  Blog pages simply don't include the wipe/decode/typing elements, so the shared script
  no-ops for those features there without any blog-specific JS. The one blog-specific
  behaviour in `main.js` is the category filter, which runs only when `blog.html`'s filter
  bar is present and degrades to "all posts visible" with JS off.
- Below ~760px the HUD nav collapses to a hamburger. The closed menu is `inert` and out of
  the tab order; `Esc` closes it and returns focus to the toggle.
- `prefers-reduced-motion: reduce` disables the wipe, decode scramble, ambient animation,
  hover glitch, and reveal transforms — everything becomes static and instantly visible.
- Skip link, semantic landmarks, one `<h1>` per page, visible focus rings, AA body contrast.
- No phone number anywhere (no `tel:` link, not in the PDF). External links use
  `target="_blank" rel="noopener noreferrer"`.

## Local preview

Open any file in `docs/` in a browser, or run a static server from `docs/`:

```
cd docs && python -m http.server 8000
# then visit http://localhost:8000
```

## Deploy to GitHub Pages

1. Push this repository to GitHub (`git@github.com:Sarthak044/sarthak-kul.git`).
2. In the repo: **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
4. Choose branch **`main`** and folder **`/docs`**, then **Save**.
5. The site publishes at `https://sarthak044.github.io/sarthak-kul/`.

Notes:
- Keep `docs/.nojekyll` — it stops GitHub from running the content through Jekyll
  (which would otherwise skip files it doesn't recognize) and makes `404.html` work.
- Canonical / `og:url` values are already the final published URLs. If the repo or username
  changes, update those in each HTML file's `<head>`.
- Google Fonts (Chakra Petch, Inter, Share Tech Mono; plus Source Serif 4 on blog pages
  only) load via `<link>`. There are no other external requests — no analytics, no trackers.

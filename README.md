# AP Bio Question Bank

**3,707 multiple-choice questions** extracted from
`vdoc.pub_campbell-biology-test-bank-11-edition.pdf` (Campbell Biology, 11e — Urry;
Test Bank, 1,243 pages), tagged by chapter and topic, with all **492 figures**
recovered — plus a static practice site.

> The source PDF is © 2017 Pearson Education, Inc. This repository is private;
> the extracted data carries the same copyright as the original and is not
> redistributable.

## The practice site

Open `site/index.html` — no build step and no server needed (the data loads as a
plain `<script>`, so `file://` works). To serve it instead:

```bash
cd site && python3 -m http.server 8000
```

One setup screen: pick chapters (or expand any chapter to pick individual topics),
choose how many questions, pick a mode, start.

- **Practice** — the answer is revealed the moment you pick one
- **Exam** — no feedback until the end, and you can change an answer before advancing

Questions are drawn at random from your selection. Answer choices are *not* shuffled,
because in figure questions the letters refer to labels printed in the image. Keyboard:
`A`–`D` or `1`–`4` to answer, `Enter`/`→` to advance. The site keeps no state — every
visit starts clean.

| Path | Description |
|---|---|
| `site/index.html`, `site/style.css`, `site/app.js` | The site — vanilla HTML/CSS/JS, no dependencies |
| `site/data/questions.js` | Site payload, 1.9 MB (449 KB gzipped) |
| `site/images/` | 492 figures (18 MB) |

### Hosting it on GitHub Pages

`.github/workflows/pages.yml` publishes `site/` to GitHub Pages on every push to
`main` that touches it, and can be run by hand from the Actions tab. Only `site/`
is uploaded — the source PDF, `data/` and `scripts/` are not part of the deploy.

To turn it on, once:

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
2. Merge this branch into `main` (or run *Deploy site to GitHub Pages* from the
   Actions tab with **Run workflow**).

The site then lives at `https://<user>.github.io/apbio-question-bank/`. Every path
in the site is relative, so it works unchanged under that subdirectory; `.nojekyll`
keeps Pages from running the files through Jekyll.

> **Two caveats, given the source material.** GitHub Pages sites are **public** —
> anyone with the URL can read them, even when the repository is private, unless
> you are on GitHub Enterprise Cloud with access control enabled. And Pages from a
> private repository requires GitHub Pro or higher; on the Free plan the repository
> has to be public before Pages will publish. Publishing puts 3,707 questions and
> 492 figures from a © 2017 Pearson test bank on the open web under your account.

## The dataset

| Path | Description |
|---|---|
| `data/questions.json` | Full question bank |
| `data/chapters.json` | Chapter/topic index with question counts |
| `scripts/` | The extraction pipeline (see *Reproducing*) |

### Tagging

Both tags come **verbatim from the PDF's own structure** — nothing is inferred from
outside the document.

- **Chapter** — from the `Chapter N <title>` headings. 56 chapters.
- **Topic** — from each question's `Section: N.N` field, the textbook section it maps
  to. 268 topics.

Questions under a chapter's *Student Edition End-of-Chapter Questions* heading carry no
`Section:` field in the source. They are tagged `topic.scope = "chapter_review"` with
`topic.section = null` rather than being assigned a section they don't claim.

**Topic names:** this test bank references sections by *number* only — section titles
(e.g. "1.1 The study of life reveals common themes") appear nowhere in the PDF. Adding
them would require the textbook's table of contents, which is not in this source.

### Record shape

```json
{
 "id": "ch01-mc-004",
 "chapter": { "number": 1, "title": "Evolution, the Themes of Biology, and Scientific Inquiry" },
 "topic": { "section": "1.1", "scope": "section" },
 "question_type": "multiple_choice",
 "number_in_section": 4,
 "stem": "To understand the chemical basis of inheritance, we must understand ...",
 "choices": { "A": "evolution", "B": "emergent properties", "C": "reductionism", "D": "feedback regulation" },
 "answer": "C",
 "answer_text": "reductionism",
 "bloom_taxonomy": "Application/Analysis",
 "source_page": 2,
 "images": [],
 "shared_images": [],
 "choice_images": {},
 "flags": { "references_figure": false, "choices_are_images": false, "has_image": false, "image_inherited": false }
}
```

`id` is stable and unique: `ch<chapter>-<mc|eoc>-<number>`. Question numbering restarts
within each subsection in the source, so the chapter and type prefixes are load-bearing.

### Contents

- **3,707** questions — 3,354 section-tagged multiple-choice, 353 chapter-review
- **56** chapters, **268** topics
- All 4-option multiple choice except 4 with five options and 4 with three
- `bloom_taxonomy` preserved from the source: `Knowledge/Comprehension`,
  `Application/Analysis`, or `Synthesis/Evaluation`

## Figures

All 493 embedded images were located by position and matched to the question whose text
region contains them (one — the cover — was discarded). They are cropped from the page at
150 DPI and saved as palette PNG, or JPEG where that is smaller. **458 questions carry at
least one image.**

Three fields, because a figure can belong to a question in three different ways:

- `images` — figures printed inside the question's own span. 376 questions.
- `choice_images` — the answer *options* are pictures, mapped `{"A": img, "B": img, …}`.
  18 questions. These are the ones whose `choices` text is empty, because none exists in
  the PDF.
- `shared_images` — a figure introduced above the question and shared across a group
  (a periodic table, a labeled cell membrane, a phylogenetic tree), or one belonging to
  a nearby question in the same section. 64 questions. Inheritance is bounded by
  chapter, type, and section, and flagged with `image_inherited: true`.

Each image entry is `{file, w, h, page}`; `file` resolves against `site/images/`.

26 questions mention a "figure", "table", or "graph" and have no image attached. These
were checked individually: nearly all are tables the PDF prints **as text**, so the data
is already in the stem (e.g. `ch48-mc-017`), or false positives on wording like "table
sugar". A handful in chapters 2–3 refer to a periodic table printed in an earlier
section.

## Shared stimulus blocks

Eleven preamble blocks introduce groups of questions at once (a passage, a matching key,
a figure reference). All are preserved verbatim in `shared_stimuli` at the top level of
`data/questions.json`. Which questions each governs is **inferred** — the grouping is
visually implied by figures that are images — so links are bounded by chapter, type, and
section and marked `shared_stimulus_link_inferred: true`. Treat it as a hint; the
authoritative grouping is the printed page.

## Verification

The parser produced exactly **3,707** questions against **3,707** `Answer:` lines in the
source — nothing dropped or invented. Also checked:

- A 400-question random sample round-trips: every stem and choice appears verbatim in the
  PDF text (0 mismatches)
- Every question's answer letter exists among its choices (3,707/3,707)
- Zero metadata leakage — no stem or choice contains `Answer:`, `Bloom's Taxonomy:`,
  `Section:`, or the running page title
- All 492 referenced image files exist on disk, with no orphans
- The site was driven end-to-end in headless Chromium: chapter and topic selection,
  filtering, partial-selection state, a full 68-question practice run, a full 61-question
  exam run, image and image-choice rendering, keyboard input, ending a run early, and the
  results review. No console or page errors.

## Reproducing

```bash
python3 -m venv venv && ./venv/bin/pip install pypdf pdfplumber pypdfium2
./venv/bin/python scripts/extract.py        # PDF    -> pages.json
./venv/bin/python scripts/parse.py          # pages  -> questions_raw.json + anomalies.json
./venv/bin/python scripts/build.py          # raw    -> data/questions.json + data/chapters.json
./venv/bin/python scripts/locate.py         # PDF    -> layout.json (question + image positions)
./venv/bin/python scripts/render.py         # crops  -> site/images/
./venv/bin/python scripts/merge_images.py   # images -> data/questions.json
./venv/bin/python scripts/make_site_data.py # bank   -> site/data/questions.js
```

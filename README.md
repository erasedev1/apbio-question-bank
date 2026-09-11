# AP Bio Question Bank

Structured extraction of **3,707 multiple-choice questions** from
`vdoc.pub_campbell-biology-test-bank-11-edition.pdf` (Campbell Biology, 11e — Urry;
Test Bank, 1,243 pages), tagged by chapter and topic.

> The source PDF is © 2017 Pearson Education, Inc. This repository is private;
> the extracted data carries the same copyright as the original and is not
> redistributable.

## Files

| Path | Description |
|---|---|
| `data/questions.json` | The full question bank (3.8 MB) |
| `data/chapters.json` | Chapter/topic index with question counts |
| `scripts/extract.py` | Dumps per-page text from the PDF to `pages.json` |
| `scripts/parse.py` | Parses `pages.json` into raw question records |
| `scripts/build.py` | Normalizes, tags, and emits the final JSON |

## Tagging

Both tags are taken **verbatim from the PDF's own structure** — nothing is inferred
from outside the document.

- **Chapter** — from the `Chapter N <title>` headings. 56 chapters.
- **Topic** — from each question's `Section: N.N` field, which is the textbook
  section the question maps to. 268 distinct topics.

Questions printed under a chapter's *Student Edition End-of-Chapter Questions*
heading carry no `Section:` field in the source. They are tagged
`topic.scope = "chapter_review"` with `topic.section = null`, rather than being
assigned a section they don't claim.

**Note on topic names:** this test bank references sections by *number* only —
section titles (e.g. "1.1 The study of life reveals common themes") appear nowhere
in the PDF. Topics are therefore identified by section number. Adding human-readable
titles would require the textbook's table of contents, which is not in this source.

## Record shape

```json
{
 "id": "ch01-mc-004",
 "chapter": { "number": 1, "title": "Evolution, the Themes of Biology, and Scientific Inquiry" },
 "topic": { "section": "1.1", "scope": "section" },
 "question_type": "multiple_choice",
 "number_in_section": 4,
 "stem": "To understand the chemical basis of inheritance, we must understand the molecular structure of DNA. This is an example of the application of which concept to the study of biology?",
 "choices": { "A": "evolution", "B": "emergent properties", "C": "reductionism", "D": "feedback regulation" },
 "answer": "C",
 "answer_text": "reductionism",
 "bloom_taxonomy": "Application/Analysis",
 "source_page": 2,
 "flags": {
  "references_figure": false,
  "choices_are_images": false,
  "shared_stimulus_id": null,
  "shared_stimulus_link_inferred": false
 }
}
```

`id` is stable and unique: `ch<chapter>-<mc|eoc>-<number>`. Question numbering restarts
within each subsection in the source, so the chapter and type prefixes are load-bearing.

## Contents

- **3,707** questions — 3,354 section-tagged multiple-choice, 353 chapter-review
- **56** chapters, **268** topics
- All questions are 4-option multiple choice except 4 with five options and 4 with three
- `bloom_taxonomy` is preserved from the source: `Knowledge/Comprehension`,
  `Application/Analysis`, or `Synthesis/Evaluation`

## Known limitations

These are properties of the source PDF, not extraction failures. Each is flagged in
the data so it can be filtered.

1. **Figures are not extracted** (`references_figure`, 345 questions). The PDF's
   diagrams, graphs, and micrographs are images. Question text is complete, but a
   question asking "which component in the accompanying figure…" cannot be answered
   from the JSON alone. Page numbers are recorded so the figure can be looked up.

2. **21 questions have image-only answer choices** (`choices_are_images`). Their
   options are pictures — e.g. "Which one of the atoms shown would be most likely to
   form a cation with a charge of +1?" Choice keys and the answer letter are correct,
   but choice *text* is empty because none exists in the source.

3. **Shared stimulus blocks** (`shared_stimuli`, 11 blocks). Some questions are
   introduced by a preamble covering several questions at once — a passage, a
   periodic-table reference, or a matching key. All 11 blocks are preserved verbatim
   at the top level of `questions.json`.

   Which questions each block governs is **inferred**, not stated by the PDF: the
   grouping is visually implied by figures we cannot read. Links are bounded by
   chapter, question type, section, and the next stimulus block, and every link is
   marked `shared_stimulus_link_inferred: true`. 76 questions carry a link. Treat it
   as a hint; the authoritative grouping is the printed page.

## Verification

The parser produced exactly **3,707** questions against **3,707** `Answer:` lines in
the source — no question was dropped or invented. Also checked:

- A 400-question random sample round-trips: every stem and choice appears verbatim in
  the PDF text (0 mismatches)
- Every question's answer letter exists among its choices (3,707/3,707)
- Zero metadata leakage — no stem or choice contains `Answer:`, `Bloom's Taxonomy:`,
  `Section:`, or the running page title
- All IDs unique; chapter index counts reconcile with the bank total

## Reproducing

```bash
python3 -m venv venv && ./venv/bin/pip install pypdf pdfplumber
./venv/bin/python scripts/extract.py   # PDF   -> pages.json
./venv/bin/python scripts/parse.py     # pages -> questions_raw.json + anomalies.json
./venv/bin/python scripts/build.py     # raw   -> data/questions.json + data/chapters.json
```

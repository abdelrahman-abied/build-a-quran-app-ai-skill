# Where the muṣḥaf comes from

A catalogue of the sources a muṣḥaf reader actually needs — text, pagination,
line breaks, glyph codes, typefaces — with what each publishes, how it is
obtained, what its terms say, and what was found wrong in it.

**Everything here was read on the dates given.** Terms change, mirrors are
re-cut, and pages 404. Re-read before you rely on any row, and treat the dates
as the shelf life of the claim rather than decoration.

**This repository ships none of these resources.** It tells you where they are.

---

## 1. The text

### Tanzil — `tanzil.net`

The usual primary source for the Uthmani text, the simple/clean text, and
several translations.

- **Serves files, not a repository.** There is no commit to pin, so **hash your
  download** and store the hash in your database's `meta`. That hash is the only
  thing standing between you and a silently re-cut text.
- **Terms** (carried in each file's own footer): the text may be used in any
  application **provided the source is indicated and linked**. So the reader
  must name the Tanzil Project and link `tanzil.net` — in the app, not only in
  a repo file.
- Carries a `<sajdas>` metadata block. **Read sajda positions from it**; do not
  transcribe them, and note that they are typed (recommended / obligatory).
- Glues the basmala onto the opening āyah of each sūra. **Split it off** — it
  is a header everywhere but 1:1, and 27:30 carries it mid-āyah.

### quran.com public API

Serves per-āyah `code_v1` and `code_v2` glyph codes with **no authentication**.

Its real value is as **the third source** (Law 1). In a reconciliation of the
1405H print across all 6,236 āyāt it was never itself the odd one out, and
every disagreement resolved 2-of-3 against it.

Note it also serves a *referer-gated* COLRv1 font cut. Anything behind a referer
check is not a source you can rely on in a build.

### QUL — `qul.tarteel.ai` (Quranic Universal Library)

An aggregator, run by Tarteel, publishing scripts, layouts, fonts, glosses and
segmented audio as SQLite/JSON exports.

- **The SQLite layout exports sit behind a free sign-in**; the font CDN does
  not. The download is a **one-time developer action** feeding a build tool —
  your app's runtime should never touch an authenticated path.
- **Its code repository is MIT. The resources are not covered by that.** See
  §5 and `licensing.md` — this is the single most consequential
  misunderstanding in the ecosystem.

Resources a muṣḥaf reader uses:

| # | What it is | Used for |
|---|---|---|
| script 47 | QPC V4 glyphs (with tajwīd) | glyph codes, 1441H print |
| script 57 | QPC V1 glyphs | glyph codes, 1405H print — and the **second source** for reconciliation |
| script 59 | IndoPak Nastaʿlīq word text | Unicode words for a Unicode edition |
| layout 12 | IndoPak 15-line (Qudratullah) | **610** pages, line breaks |
| layout 15 | KFGQPC v1 | 604 pages, line breaks (9,046 rows) |
| layout 19 | KFGQPC V4 (1441H) | 604 pages, line breaks (9,046 rows) |
| font 242 | "Indopak Nastaleeq" | ❌ see §5 |

Layout export schema, from QUL's own documentation:

```
pages(page_number, line_number, line_type[ayah|surah_name|basmallah],
      is_centered, first_word_id, last_word_id, surah_number)
words(word_index, word_key, surah, ayah, text)
```

`text` carries **glyph codes** for a glyph edition and the **Unicode string**
for a Unicode edition. That single column doing two jobs is why the two
rendering models look deceptively similar in the data and are not.

---

## 2. Typefaces

### `nuqayah/qpc-fonts` — the GitHub mirror of the KFGQPC page fonts

Offers two cuts. **Take v1; v2 is corrupt.**

| | v1 | v2 |
|---|---|---|
| Files | `mushaf.txt` + `mushaf/QCF_P###.TTF` | — |
| Integrity | 0 corrupt lines, perfectly monotonic, ends on page 604 | **20 `,None` glyph lines, two mis-tagged pages at page breaks** |
| Size | ~62 MB total, **80–160 KB per page** | ~190 MB |

**Pin one commit for the glyph layout AND the fonts**, so the two can never
drift. Then read Law 2 again: this mirror was pinned, and it was wrong — see
§4.

Upstream publishes **no release assets**, and GitHub cannot zip a subdirectory
(the full-repo zip is ~554 MB because it carries every other font set). So
there is no single-archive download for the muṣḥaf fonts unless someone
publishes one.

### QUL's font CDN

Serves the V4 tajwīd per-page fonts as `p{n}.ttf` — **unpadded**, unlike the
GitHub mirror's `QCF_P###.TTF`. Any filename filter you write must be derived
from the edition rather than hardcoded, or it silently rejects an entire print.

### Fonts that are clear

`Amiri`, `Amiri-Bold` and `AmiriQuran` declare **SIL OFL 1.1** in name ID 13.
An OFL Qurʾānic face is what makes fidelity level 2 free of licence risk, and
it is the reason level 2 is a viable permanent fallback rather than a
compromise.

---

## 3. Page counts, so nothing hardcodes 604

| Layout | Pages | Line rows | Model |
|---|---|---|---|
| KFGQPC v1 (Madani, 1405H) | 604 | 9,046 | glyph |
| KFGQPC V4 (1441H, tajwīd) | 604 | 9,046 | glyph |
| IndoPak 15-line (Qudratullah) | **610** | **9,131** | Unicode |

Read the page count from the **layout's own `info`**, never from a constant.
A pager whose item count says 604 makes a 610-page print's last six pages
unreachable, and nothing about the app looks broken.

---

## 4. Defects found, and how each was settled

*Reconciliation of three transcriptions of the 1405H print, all 6,236 āyāt,
2026-07-29. Nine disagreeing āyāt, every one settled 2-of-3, no three-way
split. All three sources converge on **88,246 glyphs** once each one's own
defect is repaired — that convergence is the result.*

| āyah | pinned mirror | script 57 | `code_v1` | wrong | how it was corroborated |
|---|---|---|---|---|---|
| **2:79** | 27 glyphs, one code **twice** | 26 | **26** | mirror | a page font gives every word slot its own codepoint, so one code twice draws one word twice |
| **13:37** | 21 | 22 | **21** | script 57 | it merges two codes into one word |
| **13:38–42** | — | all shifted +1 | **—** | script 57 | 13:37's miscount renumbers the rest of the page; it resynchronises at the page break, which is why nothing downstream would notice |
| **68:42** | ends `U+00FB` | ends `FC26` | **`FC26`** | mirror | raw bytes `\xc3\xbb` among three-byte neighbours; the page font inks `FC26` |
| **69:8** | 7 glyphs | 6 | **6** | mirror | the page font inks nothing at the extra codepoints |
| **83:35** | page **588** | page 589 | **589** | mirror | the layout's line 589:1 carries its words; page 588 ends at 83:34 |

**What they looked like on screen** — the reason this class of error is the one
to fear:

- **2:79** drew a word of the āyah twice, in perfect calligraphy.
- **68:42** ended on a Latin `û` the page font has no glyph for.
- **69:8** ended on a codepoint the font does not ink — a blank.
- **83:35 is the only one a reader could have reported**, because the page
  number is what "go to this āyah" jumps to, what a bookmark stores and what a
  khatmah counts. Filed on 588, the āyah is simply not on the leaf the app
  opens.

All of them shipped in every release for several versions.

**Two further rows carried a space inside a word** (36:52, 37:130) with correct
and contiguous codes either side — a stray in the export, not a disagreement
about the text. It is stripped, and **the build reports how many rows it
stripped** rather than absorbing it silently.

### The shortcut that was tried and must not be

Deriving the 1441H layout from the 1405H one by positional correspondence, since
each v4 page font's `cmap` enumerates that page's slots contiguously in reading
order and page 1 agrees exactly (36 and 36).

Over a 32-page sample: **22 pages match, 10 differ.**

| page | delta | note |
|---|---|---|
| 5, 100, 550 | **−1** | ordinary pages, one sūra, no header |
| 20, 101 | **+1** | same |
| 128, 350 | **−2** | a sūra starts on the page |
| 528 | **+2** | two sūras |
| 590 | **+10** | sūra header |
| 600 | **+24** | three sūras, two headers |

The large positive deltas are explainable — the v4 cmap carries header and
basmala glyphs the āyah rows do not. **The ±1 and ±2 on plain pages are not.**
The two prints genuinely split words differently, and a one-glyph divergence
shifts every glyph after it on the page while still rendering as beautiful
calligraphy.

---

## 5. What the terms actually say

*Read 2026-07-28. A survey of what the sources state — not legal advice, not a
clearance.*

| Resource | Ships as | What the source says |
|---|---|---|
| Tanzil text | text in the database | ✅ **Usable in any app if the source is indicated and linked.** |
| Amiri / AmiriQuran | bundled TTF | ✅ **SIL OFL 1.1**, stated in name ID 13. |
| `font 242` IndoPak Nastaʿlīq | bundled TTF | ❌ **Distribution prohibited without written notice** — in the font's own metadata. |
| `layout 12` IndoPak 15-line | page/line numbers | ⚠️ **Open, unstated.** Qudratullah's pagination; the aggregator is silent. |
| `script 59` IndoPak word text | Unicode text | ⚠️ **Open, unstated**, and shares the font's origin. |
| `layout 15` / `19`, `script 47` / `57` | page, line and glyph data | ⚠️ **Open** — the Complex's, and its terms URL is dead. |
| KFGQPC per-page fonts | fetched at runtime | ⚠️ **Open** — same. |

### The aggregator's silence

All the QUL resource pages above were read. **Not one states a licence.** Each
carries metadata and a footer link to a consumer app's Terms of Use that does
not mention developer resources, fonts or downloadable data. The documentation
site has no licence page. The GitHub repository is **MIT — for the codebase**.

The homepage says *"we've curated and open-sourced them"*. **That is a
description of curation, not a grant**, and the aggregator is not the rights
holder of any of them: the layouts belong to the Complex and to Qudratullah,
and the font to its author and, behind him, to two commercial foundries.

### The font that forbade what was already being done

`IndopakNastaleeq.ttf` was assumed to be the aggregator's font, whose page
states no terms. **It is not that, and the terms were never missing — they were
inside the file.** Its `name` table:

> **Family (ID 1):** `AlQuran IndoPak by QuranWBW`
>
> **Copyright (ID 0):** `© Al Qalam © Ghandhara © KFGQPC © Ayman Siddiqui`
>
> **Licence (ID 13):** *"…based on Al Qalam Quran Majeed and Al Qalam Quran
> Majeed Web fonts… The Ayah Numbers have been made using glyphs of Nastaleeq
> Font by King Fahad Glorious Quran Printing Complex… [Made only for
> Sadaqa-e-Jaria purposes. No Copyright infringement intended.]*
> ***NOT FOR SALE, NOT FOR MODIFICATION, NOT FOR DISTRIBUTION OR NOT FOR
> DEVELOPMENT WITHOUT WRITTEN NOTICE BY QURANWBW.COM***"

Bundling a TTF in an app package **is** distribution; shipping an app built on
it **is** development. Both are named.

Two facts make it worse rather than better:

- **"No copyright infringement intended" is not a licence, and the chain under
  it is commercial.** The face is a derivative of a *sold* typeface, so its
  author's own right to license onward is unestablished — meaning even a written
  grant from him clears the top link of a three-deep chain.
- **The āyah numerals are the Complex's glyphs**, by the font's own admission.
  So the font does not "add no licensor beyond the Complex"; it adds three.

### The Complex's own position

Its font download site carries only *«جميع الحقوق محفوظة لمجمع الملك فهد لطباعة
المصحف الشريف»* with no linked terms. The site-wide position is that its
contents are owned and protected *"with some exceptions for services and items
the Complex designates for public use."*

The one licence pointer the ecosystem had — `dm.qurancomplex.gov.sa/copyright-2/`
— **returns HTTP 404** (checked 2026-07-24). Third-party summaries describe a
free grant to use, copy and distribute alongside a prohibition on modifying or
reselling, which is *plausibly* the designation these fonts fall under, and
**plausibly is not a licence you ship on**.

This is worse than an open question, because a dead URL in a licence note
**looks closed**. Write to the rights holder and record the answer in place of
the URL.

### The lesson, which is not "read licences earlier"

Every licence hunt here went to the **distributor's web page** and stopped when
the page was silent. For a typeface, the authoritative record is usually
**inside the binary**, put there by the person who made it.

The `name` table was three IDs away in a file that had already been opened
closely enough to discover its private-use numerals.

→ `scripts/font_licence.py`, `licensing.md`

---

## 6. Beyond this skill's scope

Recitation audio, word-by-word glosses, tafsir and mutashabihāt exports come
from the same aggregator and carry the same silences — plus defects of their
own, including segmented-audio sets that **do not say which recording they
describe**. A timing set applied to the wrong performance by the same reciter
marks the wrong word for the entire muṣḥaf, renders perfectly, and says
nothing.

If you build those surfaces, apply Laws 1, 3, 5 and 6 unchanged.

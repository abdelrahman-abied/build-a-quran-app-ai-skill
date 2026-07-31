# Laying out the page

How a muṣḥaf page is actually built, per rendering model, with the fitting
algorithms and the failures each one was written to fix.

---

## The two models

An edition is one of two things. Deciding wrong means writing one component
with a conditional at every step — two algorithms wearing one name.

| | **Glyph edition** | **Unicode edition** |
|---|---|---|
| Examples | KFGQPC v1 (Madani), QPC v4 (tajwīd) | IndoPak Nastaʿlīq |
| Typeface | **one font per page** | **one face**, every page |
| Text in DB | private-use glyph codes | real Unicode words |
| Font delivery | downloaded on demand, ~62 MB total | bundled, ~300 KB |
| Page fills because | the page's own font is cut for it | line data + per-line fitting |
| Line breaks | **still need line data** | line data, always |
| Storage | per-āyah glyph rows **+** line rows | line rows |
| Renderer | **sibling** widget | **sibling** widget |
| Tap resolution | character range per āyah in the joined run | segment offsets within the line |

Build them as siblings. They share the pager, the chrome, the download UI and
the fit cache — and nothing about how a page becomes pixels.

---

## Part I — Glyph editions

### How the print works

The King Fahd Complex cuts a **separate font for each of the 604 pages**. A
page's font renders that page's words as pre-shaped calligraphic glyphs at
print-exact widths, which is why every leaf of the printed muṣḥaf fills to the
margins with the same fifteen lines.

So the pipeline is: **bundle the glyph layout** (which codes, which page) in
your database; **fetch the fonts per page** on first view; cache forever.

### The run has no break points

The glyph codes are contiguous — no spaces. A layout engine has nowhere to
wrap, so a page renders as one unbreakable run.

**Insert a separator between glyphs.** The print-exact glyph widths then make
ordinary justification fill each line the way the press does. This costs
nothing and is the single line of code that makes the whole model work.

It gets you a page that *fills* like the print. It does **not** get you the
print's fifteen lines — see Law 7 and Part III.

### Fit the page, do not fix the size

The print fills every leaf because every leaf has its own font. One global
glyph size cannot reproduce that. Measured in glyph units:

| page | units |
|---|---|
| al-Fātiḥa | ~36 |
| the closing pages | ~70 |
| average page | ~146 |

A size that fills the average page leaves the sparse ones short of the bottom;
a size that fills the sparse ones overflows the dense ones. No fixed size plus
leading gives both tight lines and full pages.

**The algorithm:**

```
fit(page):
  reserve = band_height + (basmala_height if page opens a sūra else 0)
  target  = page_height - reserve
  binary search size in [min_font, max_font]:
      lay out the page's runs at `size` with leading = LEADING (constant)
      keep the largest size whose laid-out height <= target
  return size
```

Three details that matter:

- **Leading is constant, size varies.** That is what makes the line rhythm
  identical across all 604 pages while a sparse page renders large and a dense
  one small. A tight ratio suits pre-shaped glyphs (their marks are baked in);
  a Unicode Qurʾānic face needs noticeably more air for its tall marks.
- **Measure with the same metrics you will draw with.** A fit computed against
  different constraints than the render is a fit for a different page.
- **Clamp the residue.** The band reserve is an estimate; a scale-down wrapper
  absorbs the few pixels of error, and centring absorbs the slack on a page too
  sparse to reach the target at maximum size.

**Cache the result**, keyed by `(edition, page, size constraints, font family)`.
Include the family: a dark-mode font variant is different bytes and must not
collide with the light one's key.

### Resolving a tap on one joined string

The page is a single run of private-use codepoints with no per-āyah spans to
hang a gesture on.

**Record each āyah's character range as you assemble the run** — in **code
units**, since these codepoints reach into supplementary planes — then map a
tap position back through it.

Two things verified on real pages rather than assumed:

- **The closing glyph of an āyah is its number.** Confirmed by rendering page 1
  and page 597; 597 because 96:19 is a place of prostration, and the ۩ turns
  out to come **before** the mark, so the rule holds where it could most easily
  have broken.
- **Hit-test the number against its painted box**, not by nearest character.
  The open leading above and below every number otherwise means a resting thumb
  opens commentary. Measured on a real page: 27 marks, ~40×40 px each — all
  reachable, none accidental.

### Delivering ~62 MB of fonts

- **Per page, on first view.** Bundling is not viable on top of an app's own
  size.
- **One keep-alive connection** for a bulk download — one TLS handshake, not
  604.
- **A bounded worker pool** (≈6) over one shared cursor.
- **Write-then-rename, always**, so a kill never leaves a truncated font on
  disk. Same for cache writes and archive extraction.
- **Bulk downloading must not register the typefaces.** Loading 604 faces into
  the engine to cache them wastes the entire ~62 MB in memory; write the bytes
  and register a page's font when the page is actually viewed.
- **gzip at rest** — measured −40% on v1 fonts and **−59%** on the v4 cut.
- **Resumable and cancellable**: cached pages skip, cancelled runs keep what
  they got.
- **Stamp the cache directory with the upstream commit**, so a re-pin can never
  mix two cuts of the same page.
- **Recount the cache when the download UI opens.** Pages cached by ordinary
  reading never went through the download controller, so its count goes stale.
- **Warm the neighbours.** A pager builds each new page on the first frame of a
  drag; a cold fit there is the whole stutter. Compute neighbours' fits ahead,
  under the exact keys the build will ask for, and fetch their fonts too, so a
  swipe lands on calligraphy rather than a spinner.

If you are tempted by a single archive instead of 604 requests: check that one
exists at the origin, and note that **self-hosting the bytes makes you a
redistributor** of fonts whose terms may be open. Fetching from upstream is one
posture; serving them yourself is a worse one.

---

## Part II — Unicode editions (IndoPak and its kin)

A different model, not a font swap. One Nastaʿlīq face across every page, plus
a line-layout database. Nothing about the face makes wrapping fall on the
printed lines — **an IndoPak page is typeset by the publisher's line data**,
where a KFGQPC page is typeset by its own font.

### The page count is not 604

The 15-line Qudratullah layout is **610 pages**, read from the layout's own
`info`. Every constant that said 604 becomes `edition.pageCount` — *including
the pager's item count*, which otherwise makes the last six pages unreachable
with no visible symptom.

### Lines stack; the block centres

The first attempt gave each of the fifteen lines an equal share of the page —
one flex child apiece, which is effectively what a glyph page does.

**It came out as fifteen stripes with gutters between them.** A line is scaled
to the measure's *width*, and a phone leaf is far taller than a muṣḥaf's, so
each line floated in the middle of a much taller row.

The fix: lines stack at **their own heights**, the block **centres**, and the
leftover goes to the top and bottom margins — where the press puts it too.

### `is_centered` chooses the fit

- Justified line → fit to **width**.
- Centred line → **scale down** only.

Otherwise a sūra's short closing line is stretched into a hand the printer
never used.

### The furniture is not decoration

Shown a scan of the muṣḥaf he reads, the user's note was *"this is the IndoPak
I know."* The text had been correct for an hour while the page was still
unrecognisable.

An IndoPak muṣḥaf sets its fifteen lines:

- inside a **double-ruled frame**, and
- **on ruled lines** — a rule under every line.

A reader who knows the print reads both as part of the muṣḥaf rather than as
chrome. Draw them.

> A report of *"there is line between lines"* was first read as a complaint
> about gaps, which produced a fix that closed the lines up and removed the
> very spacing the rules live in. The report was about what the **print has**,
> not about what the render got wrong. One look at the scan would have settled
> it before any code moved. When a user describes a muṣḥaf, ask for the scan.

### Paint the furniture; do not lay it out

A sūra header occupies **one of the page's fifteen line slots**.

A header panel built from a border, margin and padding ate about **half that
slot** before the name was measured — and the fit then shrank the name into
what was left. It read as a bad font choice and was not; enlarging the font
alone would have done nothing.

So: **the frame is painted, not laid out.** The header becomes a cartouche — a
double rule echoing the page's frame, a diamond at each corner, a rosette
flanking the name — painted rather than assembled from border and icon
widgets, because at one line's height these motifs are a few pixels across and
a widget layer cannot place them without stealing the space they need to sit
in.

### What the bundled face carries

The IndoPak face carries **āyah numerals and waqf marks in the private-use
area**. So substituting a different Nastaʿlīq loses the *numbering*, not merely
the hand. An OFL replacement must be checked for PUA coverage before it can be
called a replacement.

### Headers, and what not to draw

A `surah_name` row carries no āyah, so it answers nothing when pressed — which
is correct, not a gap.

The print's own sūra/page/juzʾ header can be **deliberately omitted** when the
reader already shows all three in its chrome. The same fact twice on one screen
is noise, not fidelity. Say so in a comment, or someone will "fix" it.

---

## Part III — Line data, for both models

**The premise that a glyph edition's per-page font already implies its line
breaks is false** (Law 7). The font reproduces the print's lines only when the
run is set at the print's measure; on a phone the engine breaks wherever it
fits.

Real counts: **9,046** line rows per 604-page Madani layout; **9,131** for the
610-page IndoPak one.

### The shortcut fails here too

A layout export that gives line breaks as **word ranges** invites deriving them
from word positions instead of importing them. Measured: that shortcut holds
for **56%** of the muṣḥaf. The other 44% needs the real data.

### Taking line data from a second source safely

When the line breaks come from a different export than the glyphs (Law 10.3):

- Take from the second source **only where one word ends and the next begins**.
- Cut the line's text from **your own** bundled glyphs.
- Assert the word boundaries **tile your string exactly** — over-run or fall
  short and the build stops.

A line can then never begin mid-word, and a disagreement in the second source's
own codes cannot reach your text.

---

## Part IV — Colour (tajwīd) editions

### The colours are the font's

Tajwīd prints colour their rules via `COLR`/`CPAL` layered glyphs. **A text
colour property cannot reach them.**

**Check the actual table version before designing around it.** One widely
described "COLRv1" font turned out to declare **COLR version 0** — layered
glyphs plus a palette — which is far more portable and far less likely to fail
on one device and not another.

### Dark mode is the trap, and the font already solved it

Palette 0 draws base (unruled) letters `#000000`. On a dark leaf **most of the
muṣḥaf disappears while the coloured rules stay** — the worst possible
half-failure, because it looks deliberate.

A typical `CPAL` carries several palettes, and the author usually shipped the
answer inside the file. Read out of one real page font, all six:

| palette | entry 0 (base letters) | character |
|---|---|---|
| **0** (default) | `#000000` | full colour, **light** ground |
| **1** | `#FFFFFF` | full colour, **dark** ground — accents lightened |
| 2 | `#000000` | a second colour convention, light |
| 3 / 4 | `#000000` / `#FFFFFF` | the same pairing in monochrome |
| 5 | `#000000` | monochrome cut of palette 2 |

### Selecting a palette when your framework cannot

Most UI frameworks expose no palette selector (a variable-font axis API is a
different mechanism and will not do it). So make the selection **in the bytes**:

**Repoint `CPAL.colorRecordIndices[0]` at the target palette's first record.**
It is a **two-byte write** — no table resized, no offset moved, file length
unchanged. Verified on a real page font: after the patch the default palette
re-reads `#FFFFFF`.

Then:

- **Register the patched bytes under a different font family name.** A family
  name is usually the only handle you have on "which bytes"; registering both
  cuts under one name leaves the engine choosing.
- **Keep one copy on disk.** Patch on the way into the engine, so switching
  theme costs no bytes and no network, and a re-pin never has to reconcile two
  variants.
- **Let the theme reach the font path as a cache key**, derived from the live
  theme rather than from a stored preference — otherwise a system-driven theme
  change does not re-resolve the font.
- The family suffix falls into the fit cache's key for free, which is exactly
  what you want.

---

## Part V — Fidelity levels, and choosing one

| Level | What it is | Cost | Offline |
|---|---|---|---|
| **1** | Flowing text, āyah cards | one Arabic face | ✅ |
| **2** | Justified Uthmani, real page numbers, page-turn pager | one OFL Qurʾānic face | ✅ |
| **3** | The printed muṣḥaf, page for page, in its own hand | tens of MB of fonts, download infrastructure, an open licence question | after download |

**Keep level 2 as a permanent offline fallback and make level 3 opt-in**, with a
first-run explainer that says what will be downloaded and why. Level 3 is the
only network-touching surface in an otherwise offline app; keeping that true is
worth designing for.

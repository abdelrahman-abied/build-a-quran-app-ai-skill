---
name: mushaf
description: Build a Qur'an muṣḥaf reader whose pages, lines and words match a real printed muṣḥaf — sourcing and verifying the text, choosing a fidelity level, per-page KFGQPC glyph fonts, IndoPak line layouts, tajwīd colour fonts, word numbering, and the font-licence gate. Use when building or reviewing any Qurʾān reading surface (مصحف، تطبيق قرآن، صفحة المصحف، ترقيم الآيات والكلمات، الرسم العثماني، مصحف إندوباك), when ingesting Qurʾānic text, layout, line-break or glyph exports from Tanzil, QUL, quran.com or KFGQPC, or when a rendered page has the wrong āyāt per page, the wrong words per line, or a highlight one word off. Data-and-typography guidance is framework-neutral; a Flutter appendix carries measured implementation patterns.
---

# The muṣḥaf, built to the print

One goal: make the page in the app be the page in the book — the same āyāt on
the same leaf, the same words on the same line, in the same hand. Everything
here was measured against real prints, real fonts and real exports while
shipping a muṣḥaf that renders three of them. Where a number appears, it was
counted.

**Scope.** The muṣḥaf itself: text, numbering, pagination, line breaks, glyphs,
fonts and their licences, and the verification that proves all of it. Not
recitation audio, tafsir, memorisation, or prayer features.

**Understand this before anything else:** in this domain the dangerous errors
are the ones that *render beautifully*. A duplicated word in perfect
calligraphy. A highlight one word to the left. A bookmark that opens the wrong
leaf. A page whose every glyph after position 40 is shifted by one, still
flawless Nastaʿlīq, saying something the Qurʾān does not. None of these look
like bugs — they look like the muṣḥaf.

So every rule below is a way of making a wrong thing **loud** instead of pretty.

---

## The twelve laws

Break these knowingly or not at all.

### 1. Two sources cannot settle anything. Three can.

Two transcriptions of one print that disagree tell you only that one is wrong.
A third, independently produced, resolves it — and resolves it cleanly:
reconciling three transcriptions of the 1405H KFGQPC print across all 6,236
āyāt produced **nine disagreeing āyāt, every one settled 2-of-3, with no
three-way split.** Where a per-page font exists, ask it too: a font that inks
nothing at a codepoint is a fourth witness, and a font that gives every word
slot its own codepoint proves a repeated code is a duplicated word.

Pick the third source *before* you need it, and prefer one reachable without an
account or a referer check.

### 2. A pin is not correctness.

Pinning a mirror to a commit guarantees only that you keep getting the same
answer. A widely-used pinned glyph mirror carried **four real defects** — one
codepoint written twice (drawing one word twice, beautifully), a Latin `û`
among three-byte Arabic codepoints, a codepoint the page font does not ink (a
blank), and one āyah filed one page early. All four shipped for multiple
releases. **Reproducibility and correctness are different properties.** Buy
both, separately.

### 3. Drop the row and say so. Never repair it in place.

When an upstream row is out of bounds, self-contradictory, duplicated or
absent: **omit it and report the omission** — in the build log, in a defects
document, and upstream to the publisher. Do not clamp a range to fit, do not
invent a missing word, do not shift an index until it looks right.

> A missing row is visible. A wrong one is not.

A range clamped to an āyah's last word produces a plausible highlight over the
wrong words, forever, silently. The omission produces a gap someone reports.

When you *must* correct — because three sources prove the defect — make the
repair **self-asserting**: state the index it edits *and the byte it expects to
find there*, so an upstream fix breaks the build loudly instead of being
silently re-broken.

### 4. Never derive one edition's layout from another's.

The tempting shortcut: you already hold the 1405H glyph layout, and the 1441H
page fonts are public and enumerate their slots contiguously in reading order —
so derive the second from the first by positional correspondence and skip the
download. Page 1 even agrees exactly: 36 slots, 36 glyphs.

**Measured over a 32-page sample: 22 pages match, 10 differ.** Large positive
deltas are explainable (the newer cmap carries sūrah-header and basmala glyphs
your āyah rows do not). The **±1 and ±2 on plain single-sūrah pages are not** —
the two prints genuinely split words differently.

And that is the finding that kills it, because of the failure mode: **a
one-glyph divergence does not draw one wrong glyph. It shifts every glyph after
it on the page**, and the page still looks like beautiful calligraphy. Silent
corruption of scripture is not a defect you ship and fix later.

Pay for the real export. Every time.

### 5. A font's licence is inside the font, not on its download page.

Before bundling **any** typeface, dump `name` table IDs **0** (copyright), **7**
(trademark), **13** (licence description) and **14** (licence URL).
`scripts/font_licence.py` does it in one command.

This is the check that gets skipped. In the project this skill comes from,
eight of nine bundled fonts declared an SIL OFL grant in name ID 13. The ninth
— whose distributor's page stated no terms at all, which was read as silence —
carried this in its own metadata:

> *NOT FOR SALE, NOT FOR MODIFICATION, NOT FOR DISTRIBUTION OR NOT FOR
> DEVELOPMENT WITHOUT WRITTEN NOTICE*

Bundling a TTF in an app package **is** distribution. It was already shipping.
The `name` table was three IDs away in the same file that had already been
opened to discover its āyah numerals.

Two corollaries, both learned the same way:

- **Silence on a distributor's page is not a grant — and not a verdict.** It
  means you have not found the sentence yet. Look in the binary, then at the
  rights holder, then at whoever *they* derived from. A "free for daʿwah" font
  can be a derivative of a sold commercial typeface, in which case even written
  permission from its author clears only the top link of the chain.
- **An aggregator's MIT licence covers its code, never the resources it
  aggregates.** A repository can be MIT while every layout, script and font it
  serves belongs to someone who has stated nothing.

Record what each source *says*, verbatim, with URL and date read. Mark
judgement calls as judgement calls. This is a survey, not a clearance.

### 6. Word numbering is per-resource. Measure it; never inherit it.

Two exports from the same publisher can number the same words differently, and
nothing in either file says so. Measured:

| | Tanzil-style | KFGQPC script exports |
|---|---|---|
| Words in the muṣḥaf | **77,433** | **83,668** |
| Āyah-ending marker | not a word | **counted as a word** |
| `إل ياسين` (37:130) | two words | **one word** |

So one is `+1` on 6,235 of 6,236 āyāt and breaks that pattern at 37:130 alone,
where the two differences cancel. Every *real* word has the same index in both
— the divergence bites only at the **end** of an āyah, which is exactly where
out-of-range bugs live.

Establish the relationship by counting, put it in **one** file, and route every
consumer through it. Resources from the same site can disagree: a segmented
export and a script export from one publisher used different numbering, and
neither page said so.

### 7. The font does not imply the line breaks.

The seductive premise: *"a glyph edition's per-page font already implies its
line breaks, so storing them again would be a second copy of the same fact."*

**It is false.** The font reproduces the print's lines only when the run is set
at the **print's measure**. On a phone the engine breaks wherever it fits. A
per-page font gets you a page that *fills* like the print; it does not get you
the print's fifteen lines.

Store line data for **every** edition. Real counts: **9,046** line rows for each
604-page Madani layout, **9,131** for a 610-page IndoPak one.

### 8. Position travels by āyah, never by page.

A bookmark, a resume point, a khatmah counter and a share card must key on
**āyah identity**, not on "page N". Page numbers are edition-local: 604 pages
in the Madani KFGQPC layout, **610** in a 15-line IndoPak one. A page number
cannot survive 604 → 610. An āyah always can.

Map through āyah identity at open (`pageOfAyah(edition, ayah)`), pay one lookup,
and a bookmark set in any print reopens in any other. Write that test first:
*bookmark set in edition A is found again in edition B.*

Corollary: **anything that hardcodes 604 breaks on the second edition you add**
— including the pager's item count, which silently makes the last six pages of
a 610-page print unreachable.

### 9. Never export the glyphs. Export the text.

A per-page muṣḥaf font renders private-use codepoints. They are pixel-perfect
on screen and **tofu everywhere else** — in a share sheet, a clipboard, a
search index, a screenshot's alt text. Share, copy and export the Unicode text;
the glyphs are a rendering detail that never leaves the widget.

### 10. Every guard fails loudly in both directions.

"Stop the build on any divergence" is right and insufficient — real exports
diverge, so a build that stops on all of them never runs, and a list of
exceptions is how a bad import wins quietly. A working guard has three parts:

1. **Every row is compared** against what already ships. An unruled
   disagreement stops the build and names the āyah.
2. **A ruling is a claim, and the claim is checked.** A ruling naming āyāt that
   now *agree* stops the build just as loudly — the export was re-cut or the
   ruling was wrong, and either way it must be re-read, not left standing as
   cover. Same for a ruling naming a row the export no longer has.
3. **A ruling never imports the other file's answer.** Take from the second
   source only the narrow thing it is authoritative for (e.g. *where one word
   ends and the next begins*), and assert that it **tiles your own data
   exactly** — over-run or fall short and the build stops. A line can then never
   begin mid-word.

### 11. A page is written in one pen.

The press writes a leaf in one hand at one size: every line, the basmala, the
sūrah's name in its header. Three separate ways of breaking that shipped in
one reader, each one perfectly legible, each one found by a reader and not
by a test:

- **Each line fitted on its own.** A Unicode page scaled every justified line
  to the measure independently, so a line of fewer letters was drawn in a
  larger hand than a line of many — two sūrahs on one leaf in visibly
  different sizes, and on the last leaf a short centred line half as large
  again as the lines over it. **The widest line sets the page's one scale.**
  A shorter line reaches the margins by widening the gaps between its words
  (the press's own answer), never by enlarging its letters; a centred line
  and the basmala are set at the same scale, in a box as wide as the widest
  line.
- **Fixed headers beside fitted text.** The text was fitted per page (14–28
  px) while the sūrah header and the basmala were fixed sizes. On an average
  page they agreed; on a dense leaf of three sūrahs the āyāt shrank and the
  headers did not. **Set the header, the panel and the basmala from the
  page's fitted size**, and put them inside the fit's measure rather than
  subtracting a constant from the page beforehand.
- **A fixed basmala in a scaled page.** The basmala kept its own size while
  the lines around it were scaled, so it stood larger than the āyāt it opens.

Compare line heights on a page that has a short line on it. It is the one
check that sees all three.

### 12. A line's words and a page's lines belong to the print.

Nothing on screen may move them: not a font change, not a size change, not a
fit, not a theme. Every fix in this file changes how a line is *drawn*; none
may change *which words* are on it or *how many lines* the page has.

- **Forbid wrapping on every printed line** — no soft wrap, one line maximum.
  A line that is too wide is scaled down, never broken. A layout engine
  allowed to wrap will move the last word of a line to a line of its own, and
  the page will still look like a muṣḥaf.
- **Prove it before and after any rendering change**: the same pages, rows
  counted, the words of each row read, in both builds. A change that alters
  either has changed the print.
- A reader that sets its own lines — an app-set page with no line data — is
  not bound by this law: its line breaks were never the print's, only its
  āyāt per page are. Say so in its code, so nobody holds it to a standard it
  cannot meet, or holds a printed edition to its looser one.

---

## The two rendering models

Everything else follows from which of these an edition is. Deciding this wrong
means writing one widget with a conditional at every step — two algorithms
wearing one name.

| | **Glyph edition** | **Unicode edition** |
|---|---|---|
| Examples | KFGQPC v1 (Madani), QPC v4 (tajwīd) | IndoPak Nastaʿlīq |
| Typeface | **one font per page** (604 of them) | **one face**, all pages |
| Text in DB | private-use glyph codes | real Unicode words |
| Fonts | downloaded on demand, ~62 MB total | bundled, ~300 KB |
| Page fills because | the page's own font is cut for it | line data + per-line fitting |
| Line breaks | **still need line data** (Law 7) | line data, always |
| Storage shape | per-āyah glyph rows + line rows | line rows |
| Renderer | sibling widget | sibling widget |

Build them as **siblings**, not as branches inside one component.

## The fidelity levels

Pick deliberately. Most projects do not know level 3 exists.

| Level | What it is | Cost |
|---|---|---|
| **1** | Flowing text, āyah cards | one Arabic font |
| **2** | Justified Uthmani text, real page numbers, page-turn pager | one Qurʾānic font (OFL ones exist) |
| **3** | **The printed muṣḥaf** — the publisher's own hand, page for page | tens of MB of fonts, on-demand download, an open licence question |

Keep level 2 as the permanent offline fallback, and make level 3 opt-in.

---

## Stages

### Stage 0 — the licence gate, before a line of code

It decides what you can build, so it goes first.

1. Dump name IDs 0/7/13/14 for every font you intend to **bundle** (Law 5).
2. For every dataset — text, layout, line breaks, glyph codes — find the
   **rights holder**, not the distributor, and record what they state, verbatim
   and dated.
3. Decide the posture for anything you cannot clear: **fetch from upstream at
   runtime; do not self-host the bytes.** Re-serving someone's fonts makes you a
   redistributor; pointing a client at their origin does not.
4. Write the attributions the sources ask for *into the app*, not only into a
   repo file. A common term: *the text may be used in any app provided the
   source is indicated and linked.*

Output: a table of resource → what ships → what the source says → ✅ cleared /
⚠️ open / ❌ forbidden. **Keep the ⚠️ rows visible.** A record that quietly
rewrites itself to match the decision it informed is worth nothing later.

→ `references/licensing.md`

### Stage 1 — the text

- Source it from a **primary publisher**, not an app's API dump.
- **Split the basmala** rather than gluing it to the first āyah of each sūrah:
  it is a header everywhere except 1:1, and 27:30 carries it mid-āyah.
- Read **sajda positions from the source's own metadata**; never transcribe them.
- Verify before storing: 114 sūras, **6,236** āyāt, per-sūra counts against the
  known table, and a content hash recorded in the database's `meta`.

→ `references/sources.md`, `scripts/verify_corpus.py`

### Stage 2 — pagination, and a caution about your own data

Store the page number as a **named column per layout**, keyed to the layout it
came from. Never assume one pagination.

Then the caution, which is itself the lesson. This project documented that two
paginations "differ by an āyah at a few page breaks" and cited 83:35 as the
example — until three-source reconciliation showed **83:35 was a defect in our
own mirror**, and the two paginations had agreed there all along. *The claim
that your sources differ may be your source's bug wearing a costume.* Verify a
divergence with a third source before you architect around it.

Gate: page numbers form a **monotonic walk** ending on the layout's last page.
A shifted export breaks this — which is what makes an order-only alignment safe
without a per-āyah key.

### Stage 3 — line breaks

Get real line data (Law 7). A typical export gives you, per page:

```
pages(page_number, line_number, line_type[ayah|surah_name|basmallah],
      is_centered, first_word_id, last_word_id, surah_number)
words(word_index, word_key, surah, ayah, text)
```

Three things that are not obvious from that schema:

- **A line usually holds the tail of one āyah and the head of the next.** So a
  line row is not an āyah. Record **per-āyah segments within the line**
  (`ayahId:start–end`, in **code units**) while the build tool joins the words —
  it knows each word's āyah at that moment, and nothing downstream can recover
  it. Without segments, recitation highlighting washes a neighbouring āyah's
  words, and a tap answers with the āyah the line *starts* in — wrong for every
  press past the boundary, which is most of the line.
- **A `surah_name` row carries no āyah.** Read which sūrah it announces forward
  from the next line that has one; do not store the fact twice.
- **`is_centered` chooses the fit** — justify to the measure for a normal line,
  scale-down for a centred one, so a sūrah's short closing line is never
  stretched into a hand the printer did not use.

### Stage 4 — rendering the page

**Glyph editions**

- Bundle the glyph *layout*; fetch the *fonts* per page on first view, cache
  forever, in a directory stamped with the upstream commit so a re-pin cannot
  mix cuts.
- **Glyph runs have no break points** — the codes are contiguous, so a layout
  engine has nowhere to wrap. Insert a separator between glyphs; the
  print-exact glyph widths then make ordinary justification fill each line as
  the press does.
- **Size the text per page, not globally.** The print fills every leaf because
  every leaf has its own font. One fixed size cannot: in glyph units al-Fātiḥa
  is ~36, the closing pages ~70, the average page ~146. Binary-search the
  largest size at which the page's runs still reach the bottom, minus a reserve
  for the sūrah band and basmala, and hold the **leading constant** so the line
  rhythm is identical across all 604 while the size varies.
- **The closing glyph of an āyah is its number** — verify on a real page before
  relying on it, including a page with a sajda mark, where the ۩ comes *before*
  the number. Hit-test the number against its painted box, not by nearest
  character, or a resting thumb opens something.
- **Record each āyah's character range as you assemble the run**, in code
  *units* (these codepoints reach into supplementary planes), or you cannot map
  a tap back to an āyah on a page that is one joined string.

**Flowing Unicode pages (an app-set page in a Qurʾānic face)**

- **Size the header and the basmala from the fitted text size** (Law 11), and
  count them inside the fit. Take the size they are set from down to a whole
  pixel, so neighbouring pages share one header and one cached ornament
  rather than each page painting its own at 17.31 and 17.38.
- **Look at where the marks sit before choosing the face.** One widely used
  OFL Qurʾānic face lifts its marks high on purpose, to leave room for stacked
  ones; across a whole page the vowels stood visibly clear of their letters.
  The King Fahd Complex's own Unicode face sets them on the letters — but
  **reads the Complex's encoding, not Tanzil's**: swap U+0652 → U+06E1 first,
  then U+06DF → U+0652 (order matters), or every sukūn draws as the silent
  zero and every silent alif as a dotted circle that breaks the word's
  joining. Check the face's cmap against **every** code point of the whole
  text after the swap (62 distinct ones; the face covered all). Both swaps are
  one code unit for one, which is what keeps every āyah, word and tap range
  measured on the stored text valid — assert the lengths are equal.
- **Keep the marks that are not words in a face that has them.** The face
  above lacks U+202F (the joiner that glues an āyah's last word to its
  medallion); the medallion, the ۩ and the joiner stayed in the old face, and
  so did the line strut, so the line pitch did not move.
- **Justification is a cost, so plan it ahead.** Justifying an app-set line
  with kashīda takes several layouts of the run; planned only when a page
  first appears, it was most of a 55–99 ms frame at every page turn on a
  mid-range phone. Plan the neighbours' lines in idle time, after their fit,
  with exactly the inputs the build will use.

**Unicode editions (IndoPak and its kin)**

- **Lines stack at their own heights and the block centres.** Giving each of
  fifteen lines an equal share of the page — the thing a glyph page effectively
  does — produces **fifteen stripes with gutters**, because a line is scaled to
  the measure's *width* and a phone leaf is far taller than a muṣḥaf's.
- **The furniture is not decoration.** An IndoPak muṣḥaf sets its fifteen lines
  inside a **double-ruled frame, on ruled lines** — a rule under every line. A
  reader who knows the print reads these as part of the muṣḥaf, not as chrome.
  The text can be perfectly correct while the page is unrecognisable.
- **Paint the furniture; do not lay it out.** A sūrah header occupies **one of
  the fifteen line slots**. A panel's margin + padding + border ate about half
  that slot before the name was measured, and the fit then shrank the name into
  what was left — which reads as a bad font choice and is not. Painting the
  frame, the corner diamonds and the rosettes costs no layout height.
- The bundled face may carry **āyah numerals and waqf marks in the private-use
  area**, so substituting a different face loses the numbering, not merely the
  hand.
- **One scale per page** (Law 11): the widest justified line sets it; a
  shorter line is widened between its words, up to a cap past which the
  words look adrift, and only the remainder is scaled; centred lines and the
  basmala sit in a box as wide as the widest line. Measure the lines' natural
  widths once per page and keep them, keyed by the page's text and not by its
  number alone.
- **Centre a header's name by its ink, and measure it.** A name that inherited
  the app's body text style drew 8 px below the middle of a 42 px panel —
  its descender through the lower rule — and the box it sat in was perfectly
  centred. Give it a style of its own, whole.

**Every edition**

- **The sūrah header is painted, and the painting has a cost.** An
  illuminated panel (jewelled border, a lattice of stars, roundels) drawn as
  paths on every frame added ~1.5 ms to every raster frame of a page turn on a
  mid-range phone; caching hints and a repaint boundary did not remove it.
  Paint the many small marks **once** into an image all headers of that size
  and palette share, and keep as paths only what sits against the name.
- **A phone is portrait, the muṣḥaf included.** A reader that unlocks
  landscape for a tablet's two-page spread must do it only on a large screen
  (a shortest side of 600 dp, read from the display, not the window). On
  Android a per-screen orientation request overrides the manifest's lock, so
  an ungated request turns the muṣḥaf on every phone with auto-rotate on.

**Colour (tajwīd) editions**

- The colours belong to the **font**, via `COLR`/`CPAL` — a text colour
  property cannot reach them. Check the actual table version before designing
  around it; one widely-described "COLRv1" font turned out to be **COLR v0**
  (layered glyphs + palette), which is far more portable.
- **Dark mode is the trap.** `CPAL` commonly ships several palettes; palette 0
  draws base letters `#000000`. On a dark leaf most of the muṣḥaf disappears
  while the coloured rules stay — the worst half-failure, because it looks
  deliberate. The font's author usually shipped the answer inside the file: a
  second palette with white base letters and lightened accents.
- If your framework cannot select a palette (most cannot), **repoint
  `CPAL.colorRecordIndices[0]`** at the other palette's first record — a
  two-byte write, no table resized, no offset moved. Register the patched bytes
  under a **different font family name**; a family name is usually the only
  handle you have on "which bytes", and registering both cuts under one name
  leaves the engine choosing. Keep **one copy on disk** and patch on the way
  into the engine, so switching theme costs no bytes and no network.

→ `references/layout.md`

### Stage 5 — verification, or none of the above is true

Layout correctness cannot be eyeballed; it must be counted.

- **Text**: 114 / 6,236, per-sūra counts, content hash.
- **Pagination**: monotonic, ends on the layout's last page.
- **Glyph totals**: three sources converge on one number once each one's own
  defect is repaired. Here that number was **88,246**. The convergence *is* the
  result; a build that cannot state it has not reconciled anything.
- **Word boundaries tile the text exactly** — no over-run, no gap (Law 10.3).
- **Every page of every edition resolves to real words, and every āyah is
  reachable** — checked by the build tool, not by users.
- **Cross-row leakage**: when asserting a target āyah is marked, assert **the
  others are not**. A single-āyah fixture cannot see a leak.
- **Goldens** of a sparse page and a dense page, per edition.
- **One pen per page** (Law 11): on a page with a short or centred line, every
  line and the basmala the same height; the header in proportion to the text.
- **The print unmoved** (Law 12): rows per page and the words of each row,
  read before and after every rendering change.
- **A device pass**, on real hardware, listed explicitly — including one press
  at each end of a line that carries two āyāt, **four pages of every edition
  on every paper the app offers** (a phone in night mode shows only the dark
  one unless you switch it), and the orientation the app actually requests
  inside the reader.

→ `references/verification.md`, `scripts/`

### Stage 6 — shipping the data

- **Build the database; do not commit it.** A tool regenerates it from cached
  upstream exports. Document the failure mode: *missing asset → run the tool.*
- **A data-only change still needs the dataset version bumped**, or upgrading
  installs keep the old file and you debug a phantom.
- **Report what the build dropped**, every run, by count and by row.

---

## Reference files

| File | Covers |
|---|---|
| `references/sources.md` | Every known text / layout / line / glyph / font source, what it publishes, what its terms say, and the defects found in each |
| `references/numbering.md` | Word and āyah numbering across resources, with the measured relationships |
| `references/layout.md` | The two rendering models in full, fitting algorithms, IndoPak page furniture, COLR/CPAL |
| `references/licensing.md` | The font-metadata check, the survey format, the posture table |
| `references/verification.md` | Every gate, with the failure it catches, and the device-pass checklist |
| `references/flutter.md` | **Framework appendix** — measured Flutter/Dart patterns |

Everything outside `references/flutter.md` is framework-neutral and applies
equally to Swift, Kotlin, React Native or web.

## Scripts

| Script | What it proves |
|---|---|
| `scripts/verify_corpus.py` | 114 / 6,236, per-sūra counts, monotonic pages, content hash |
| `scripts/font_licence.py` | Dumps name IDs 0/7/13/14 for every font given; exits non-zero on any font with no stated grant |
| `scripts/reconcile_glyphs.py` | Three-way comparison of glyph or line exports; prints every disagreement with its 2-of-3 ruling |

A muṣḥaf that has not passed these has not been verified. It has been looked at.

---

## The adab of the thing

Not style preferences.

- **Do not invent.** A word with no gloss is shown as having none. An āyah with
  no data is absent, not approximated.
- **Do not silently move someone else's data to fit your reading of it.**
- **Report defects upstream.** A defect you drop and never report is a defect
  you have decided to keep — for every other consumer of the same export.
- **Attribute where the source asks, in the app**, not only in a repo file.
- **State open licence questions as open.** The reader deserves to know what
  hand they are reading, and the next maintainer deserves to know what you did
  not settle.
